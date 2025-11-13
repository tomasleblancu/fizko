"""
Form Service - Manejo de formularios SII (F29, F22, etc.)
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import UUID
from sqlalchemy import select

from app.integrations.sii import SIIClient
from app.db.models import Form29SIIDownload, Session as SessionModel
from app.integrations.sii.exceptions import AuthenticationError

from .base_service import BaseSIIService

logger = logging.getLogger(__name__)


class FormService(BaseSIIService):
    """
    Servicio para manejo de formularios SII (F29, F22, etc.)

    Responsabilidades:
    - Extracción de lista de formularios F29
    - Descarga de PDFs de formularios
    - Guardado y gestión de registros Form29SIIDownload
    - Extracción de datos de PDFs
    """

    # =============================================================================
    # EXTRACCIÓN DE LISTA F29
    # =============================================================================

    async def extract_f29_lista(
        self,
        session_id: Union[str, UUID],
        anio: str,
        company_id: Optional[Union[str, UUID]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extrae lista de formularios F29 del SII con guardado incremental via Celery

        Args:
            session_id: ID de la sesión en la DB
            anio: Año (ej: "2024")
            company_id: ID de la compañía (opcional, se obtiene de session si no se provee)

        Returns:
            Lista de formularios F29 (sin esperar a que se guarden)
        """
        from uuid import UUID as UUIDType

        creds = await self.get_stored_credentials(session_id)
        if not creds:
            raise ValueError(f"Session {session_id} not found")

        # Obtener company_id si no se proveyó
        if not company_id:
            company_id = await self.get_company_id_from_session(session_id)
            if not company_id:
                raise ValueError(f"Session {session_id} has no associated company")

        # Convertir a UUID si es string
        if isinstance(company_id, str):
            company_id = UUIDType(company_id)

        # Callback que dispara tarea Celery para guardar
        def celery_save_callback(formulario: Dict[str, Any]) -> None:
            """
            Callback síncrono que dispara tarea Celery para guardar formulario.

            Ventajas:
            - Más simple que queues + async workers
            - Celery maneja reintentos automáticamente
            - Monitoring en Flower
            - Guardado paralelo sin complejidad de threads
            """
            from app.infrastructure.celery.tasks.sii.forms import save_single_f29

            try:
                logger.info(f"📤 Encolando guardado de F29 {formulario['folio']} via Celery")
                save_single_f29.apply_async(
                    args=[str(company_id), formulario, str(session_id)],
                    countdown=0  # Save immediately
                )
            except Exception as e:
                logger.error(
                    f"❌ Error encolando guardado de F29 {formulario['folio']}: {e}\n"
                    f"   El formulario NO será guardado. Deberás re-ejecutar sync."
                )

        # Función sincrónica que ejecuta Selenium
        def _run_extraction():
            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=creds.get("cookies"),
                headless=True
            ) as client:

                # get_f29_lista con callback que usa Celery
                result = client.get_f29_lista(
                    anio=anio,
                    save_callback=celery_save_callback
                )

                # Obtener cookies actualizadas después del scraping
                updated_cookies = client.get_cookies()

                return result, updated_cookies

        try:
            # Ejecutar extracción en thread separado para no bloquear el event loop
            result, updated_cookies = await asyncio.to_thread(_run_extraction)

            # Guardar cookies actualizadas
            if updated_cookies:
                await self.save_cookies(session_id, updated_cookies)
                await self.db.commit()
                logger.debug(f"💾 Fresh cookies persisted to database for session {session_id}")

            logger.info(
                f"✅ Extracción F29 completada: {len(result)} formularios\n"
                f"   Los formularios se están guardando via Celery tasks en paralelo"
            )

            return result

        except AuthenticationError:
            return await self.extract_f29_lista(session_id, anio, company_id)

    # =============================================================================
    # GUARDADO DE REGISTROS F29
    # =============================================================================

    async def save_f29_downloads(
        self,
        company_id: Union[str, UUID],
        formularios: List[Dict[str, Any]]
    ) -> List[Form29SIIDownload]:
        """
        Guarda/actualiza formularios F29 descargados del SII en la base de datos

        Args:
            company_id: UUID de la compañía
            formularios: Lista de formularios F29 retornados por el SII

        Returns:
            Lista de Form29SIIDownload creados/actualizados

        Example formulario dict:
            {
                "folio": "7904207766",
                "period": "2024-01",
                "contributor": "77794858-K",
                "submission_date": "09/05/2024",
                "status": "Vigente",
                "amount": 42443,
                "id_interno_sii": "775148628"  # Optional
            }
        """
        from uuid import UUID as UUIDType

        # Convertir a UUID si es string
        if isinstance(company_id, str):
            company_id = UUIDType(company_id)

        saved_downloads = []

        for formulario in formularios:
            try:
                # Parsear período (formato "YYYY-MM")
                period_parts = formulario['period'].split('-')
                period_year = int(period_parts[0])
                period_month = int(period_parts[1])

                # Parsear fecha de envío (formato "DD/MM/YYYY" -> date)
                submission_date = None
                if formulario.get('submission_date'):
                    try:
                        date_parts = formulario['submission_date'].split('/')
                        submission_date = datetime(
                            int(date_parts[2]),  # year
                            int(date_parts[1]),  # month
                            int(date_parts[0])   # day
                        ).date()
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse submission_date: {e}")

                # Buscar si ya existe
                stmt = select(Form29SIIDownload).where(
                    Form29SIIDownload.company_id == company_id,
                    Form29SIIDownload.sii_folio == formulario['folio']
                )
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Actualizar registro existente
                    existing.period_year = period_year
                    existing.period_month = period_month
                    existing.period_display = formulario['period']
                    existing.contributor_rut = formulario['contributor']
                    existing.submission_date = submission_date
                    existing.status = formulario['status']
                    existing.amount_cents = formulario['amount']

                    # IMPORTANTE: Solo actualizar sii_id_interno si viene un valor válido
                    # Nunca sobrescribir un valor existente con None/null
                    new_id_interno = formulario.get('id_interno_sii')
                    if new_id_interno is not None:
                        # Actualizar con nuevo valor
                        if existing.sii_id_interno != new_id_interno:
                            logger.debug(
                                f"Updating sii_id_interno for folio {formulario['folio']}: "
                                f"{existing.sii_id_interno} → {new_id_interno}"
                            )
                        existing.sii_id_interno = new_id_interno
                    elif existing.sii_id_interno is not None:
                        # Preservar valor existente (no sobrescribir con None)
                        logger.debug(
                            f"Preserving existing sii_id_interno for folio {formulario['folio']}: "
                            f"{existing.sii_id_interno} (new extraction returned None)"
                        )
                    # else: ambos son None, dejar como está

                    logger.debug(f"Updated F29 download: folio={formulario['folio']}")
                    saved_downloads.append(existing)
                else:
                    # Crear nuevo registro
                    download = Form29SIIDownload(
                        company_id=company_id,
                        sii_folio=formulario['folio'],
                        sii_id_interno=formulario.get('id_interno_sii'),
                        period_year=period_year,
                        period_month=period_month,
                        period_display=formulario['period'],
                        contributor_rut=formulario['contributor'],
                        submission_date=submission_date,
                        status=formulario['status'],
                        amount_cents=formulario['amount']
                    )
                    self.db.add(download)
                    logger.debug(f"Created F29 download: folio={formulario['folio']}")
                    saved_downloads.append(download)

            except Exception as e:
                logger.error(f"Error saving F29 download for folio {formulario.get('folio')}: {e}")
                continue

        # Commit todos los cambios
        if self.is_async:
            await self.db.commit()
        else:
            self.db.commit()

        logger.info(f"✅ Saved {len(saved_downloads)} F29 downloads for company {company_id}")
        return saved_downloads

    # =============================================================================
    # CONSULTA DE PDFs PENDIENTES
    # =============================================================================

    async def get_pending_f29_downloads(
        self,
        company_id: Union[str, UUID],
        limit: int = 10
    ) -> List[Form29SIIDownload]:
        """
        Obtiene formularios F29 que tienen folio e id_interno pero no tienen PDF descargado.

        Args:
            company_id: UUID de la compañía
            limit: Máximo número de registros a retornar

        Returns:
            Lista de Form29SIIDownload pendientes de descarga
        """
        from uuid import UUID as UUIDType

        # Convertir a UUID si es string
        if isinstance(company_id, str):
            company_id = UUIDType(company_id)

        stmt = (
            select(Form29SIIDownload)
            .where(Form29SIIDownload.company_id == company_id)
            .where(Form29SIIDownload.sii_id_interno.isnot(None))  # Tiene id_interno
            .where(Form29SIIDownload.pdf_download_status != 'downloaded')  # No descargado
            .order_by(Form29SIIDownload.period_year.desc(), Form29SIIDownload.period_month.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        pending_downloads = result.scalars().all()

        logger.info(
            f"📋 Found {len(pending_downloads)} pending F29 PDFs for company {company_id} "
            f"(limit: {limit})"
        )

        return list(pending_downloads)

    # =============================================================================
    # DESCARGA DE PDFs
    # =============================================================================

    async def download_and_save_f29_pdf(
        self,
        download_id: Union[str, UUID],
        session_id: Union[str, UUID],
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Descarga el PDF de un F29 desde el SII y lo guarda en Supabase Storage

        Args:
            download_id: UUID del registro Form29SIIDownload
            session_id: UUID de la sesión para autenticación
            max_retries: Número máximo de reintentos

        Returns:
            Dict con status, url y mensaje

        Example:
            >>> result = await service.download_and_save_f29_pdf(
            ...     download_id="550e8400-e29b-41d4-a716-446655440000",
            ...     session_id="abc-123-..."
            ... )
            >>> if result['success']:
            ...     print(f"PDF guardado en: {result['url']}")
        """
        from uuid import UUID as UUIDType
        from app.services.storage import get_pdf_storage
        from app.utils.pdf_validator import is_valid_f29_pdf, get_pdf_size_mb

        # Convertir a UUID si son strings
        if isinstance(download_id, str):
            download_id = UUIDType(download_id)
        if isinstance(session_id, str):
            session_id = UUIDType(session_id)

        try:
            # 1. Obtener el registro de descarga
            stmt = select(Form29SIIDownload).where(
                Form29SIIDownload.id == download_id
            )
            result = await self.db.execute(stmt)
            download = result.scalar_one_or_none()

            if not download:
                return {
                    "success": False,
                    "error": f"Download record not found: {download_id}"
                }

            # 2. Verificar que tiene id_interno_sii
            if not download.sii_id_interno:
                download.pdf_download_status = "error"
                download.pdf_download_error = "No id_interno_sii available for PDF download"
                await self.db.commit()

                return {
                    "success": False,
                    "error": "Cannot download PDF: missing id_interno_sii"
                }

            logger.info(f"📥 Downloading PDF for F29: folio={download.sii_folio}, period={download.period_display}")

            # 3. Descargar PDF desde SII (con reintentos)
            pdf_bytes = None
            last_error = None

            for attempt in range(max_retries):
                try:
                    # Función sincrónica que ejecuta Selenium
                    def _download_pdf():
                        creds = self._get_stored_credentials_sync(session_id)
                        if not creds:
                            raise ValueError(f"Session {session_id} not found")

                        # Usar cookies solo si existen en BD
                        cookies = creds.get("cookies")

                        # Log para debugging
                        if cookies:
                            logger.info(f"📊 Found {len(cookies)} cookies in DB: {[c.get('name') for c in cookies]}")
                        else:
                            logger.info("📊 No cookies found in DB")

                        with SIIClient(
                            tax_id=creds["rut"],
                            password=creds["password"],
                            cookies=cookies,
                            headless=True
                        ) as client:
                            # Verificar estado de cookies antes de usarlas
                            needs_login = not cookies or len(cookies) <= 2

                            # Si tenemos cookies, verificar si son válidas
                            if cookies and len(cookies) > 2:
                                logger.info(f"🔍 Verifying session validity for {creds['rut']}")
                                try:
                                    session_status = client.verify_session()

                                    if session_status['refreshed']:
                                        # Cookies fueron refrescadas automáticamente
                                        logger.info("🔄 Session refreshed, saving new cookies")
                                        new_cookies = session_status['cookies']
                                        self._save_cookies_sync(session_id, new_cookies)
                                        cookies = new_cookies
                                    elif not session_status['valid']:
                                        # Sesión inválida, necesita login
                                        logger.warning("⚠️ Session invalid, will perform login")
                                        needs_login = True
                                    else:
                                        logger.info("✅ Session valid, reusing cookies")
                                except Exception as e:
                                    logger.warning(f"⚠️ Session verification failed: {e}, will perform login")
                                    needs_login = True

                            if needs_login:
                                logger.info(f"🔐 Performing login for {creds['rut']} (cookies: {len(cookies) if cookies else 0})")
                                client.login()
                                new_cookies = client.get_cookies()
                                logger.info(f"✅ Login successful, got {len(new_cookies)} cookies: {[c.get('name') for c in new_cookies]}")
                                # Guardar cookies de forma síncrona
                                self._save_cookies_sync(session_id, new_cookies)
                            else:
                                logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")

                            # Descargar PDF
                            pdf = client.get_f29_compacto(
                                folio=download.sii_folio,
                                id_interno_sii=download.sii_id_interno
                            )

                            # SIEMPRE actualizar cookies al final (mismo patrón que sync de documentos)
                            updated_cookies = client.get_cookies()
                            self._save_cookies_sync(session_id, updated_cookies)

                            return pdf

                    # Ejecutar en thread
                    pdf_bytes = await asyncio.to_thread(_download_pdf)

                    if pdf_bytes:
                        break  # Éxito, salir del loop

                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)  # Esperar antes de reintentar

            if not pdf_bytes:
                error_msg = f"Failed to download PDF after {max_retries} attempts: {last_error}"
                download.pdf_download_status = "error"
                download.pdf_download_error = error_msg
                await self.db.commit()

                return {
                    "success": False,
                    "error": error_msg
                }

            # 4. Validar PDF
            is_valid, validation_msg = is_valid_f29_pdf(pdf_bytes)
            pdf_size_mb = get_pdf_size_mb(pdf_bytes)

            logger.info(f"📄 PDF downloaded: {len(pdf_bytes)} bytes ({pdf_size_mb:.2f}MB)")
            logger.info(f"🔍 Validation: {validation_msg}")

            if not is_valid:
                error_msg = f"Invalid PDF: {validation_msg}"
                download.pdf_download_status = "error"
                download.pdf_download_error = error_msg
                await self.db.commit()

                return {
                    "success": False,
                    "error": error_msg,
                    "validation_msg": validation_msg
                }

            # 5. Extraer datos estructurados del PDF
            try:
                from app.services.f29_enhanced_extractor import extract_f29_data_from_pdf

                logger.info("📊 Extrayendo datos estructurados del PDF...")
                extracted_data = extract_f29_data_from_pdf(pdf_bytes)

                if extracted_data.get('extraction_success'):
                    logger.info(f"✅ Datos extraídos: {extracted_data.get('codes_extracted')} códigos")

                    # Guardar datos extraídos en extra_data (JSONB)
                    download.extra_data = download.extra_data or {}
                    download.extra_data['f29_data'] = extracted_data

                    logger.info("💾 Datos guardados en extra_data")
                else:
                    logger.warning(f"⚠️ Extracción falló: {extracted_data.get('error')}")
                    # No bloqueamos el proceso si falla la extracción
            except Exception as e:
                logger.warning(f"⚠️ Error extrayendo datos del PDF: {e}")
                # No bloqueamos el proceso si falla la extracción

            # 6. Subir a Supabase Storage
            storage = get_pdf_storage()

            success, storage_url, storage_error = storage.upload_pdf(
                company_id=download.company_id,
                year=download.period_year,
                period=download.period_display,
                folio=download.sii_folio,
                pdf_bytes=pdf_bytes
            )

            if not success:
                error_msg = f"Failed to upload PDF to storage: {storage_error}"
                download.pdf_download_status = "error"
                download.pdf_download_error = error_msg
                await self.db.commit()

                return {
                    "success": False,
                    "error": error_msg
                }

            # 7. Actualizar registro en DB
            download.pdf_storage_url = storage_url
            download.pdf_download_status = "downloaded"
            download.pdf_download_error = None
            download.pdf_downloaded_at = datetime.utcnow()

            await self.db.commit()

            logger.info(f"✅ PDF successfully downloaded and stored: {storage_url}")

            return {
                "success": True,
                "url": storage_url,
                "size_mb": pdf_size_mb,
                "validation_msg": validation_msg
            }

        except Exception as e:
            logger.error(f"❌ Unexpected error downloading PDF: {e}")
            import traceback
            traceback.print_exc()

            # Intentar actualizar estado de error
            try:
                if download:
                    download.pdf_download_status = "error"
                    download.pdf_download_error = str(e)
                    await self.db.commit()
            except:
                pass

            return {
                "success": False,
                "error": str(e)
            }

    # =============================================================================
    # DESCARGA MASIVA DE PDFs
    # =============================================================================

    async def download_f29_pdfs_for_session(
        self,
        session_id: Optional[Union[str, UUID]] = None,
        company_id: Optional[Union[str, UUID]] = None,
        max_per_company: int = 10
    ) -> Dict[str, Any]:
        """
        Descarga PDFs de F29 para una sesión específica.

        Este método encapsula toda la lógica de negocio:
        - Buscar sesión activa por company_id si no se proporciona session_id
        - Obtener company_id desde session si no se proporciona
        - Obtener lista de PDFs pendientes
        - Descargar cada PDF
        - Manejar errores y contadores

        Args:
            session_id: UUID de la sesión SII (opcional si se proporciona company_id)
            company_id: UUID de la compañía (opcional si se proporciona session_id)
            max_per_company: Máximo número de PDFs a descargar

        Returns:
            Dict con resultados de la operación:
            {
                "success": bool,
                "company_id": str,
                "session_id": str,
                "total_pending": int,
                "downloaded": int,
                "failed": int,
                "errors": List[Dict],
                "message": str
            }
        """
        from uuid import UUID as UUIDType
        from sqlalchemy import select
        from ...db.models.session import Session

        # 1. Si se proporciona company_id pero no session_id, buscar la sesión activa más reciente
        if company_id and not session_id:
            logger.info(f"🔍 Finding most recent active session for company {company_id}")

            # Convertir company_id a UUID si es string
            if isinstance(company_id, str):
                company_id = UUIDType(company_id)

            result = await self.db.execute(
                select(Session.id)
                .where(Session.company_id == company_id)
                .where(Session.is_active == True)
                .order_by(Session.last_accessed_at.desc())
                .limit(1)
            )
            session_row = result.first()

            if session_row:
                session_id = session_row[0]
                logger.info(f"✅ Found session {session_id} for company {company_id}")
            else:
                error_msg = f"No active session found for company {company_id}"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "company_id": str(company_id),
                    "session_id": None,
                    "total_pending": 0,
                    "downloaded": 0,
                    "failed": 0,
                    "errors": []
                }

        # 2. Validar que se tenga session_id en este punto
        if not session_id:
            error_msg = "Either session_id or company_id must be provided"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "company_id": str(company_id) if company_id else None,
                "session_id": None,
                "total_pending": 0,
                "downloaded": 0,
                "failed": 0,
                "errors": []
            }

        # Convertir session_id a UUID si es string
        if isinstance(session_id, str):
            session_id = UUIDType(session_id)

        if company_id and isinstance(company_id, str):
            company_id = UUIDType(company_id)

        # 3. Obtener company_id desde session si no se proporciona
        if not company_id:
            company_id = await self.get_company_id_from_session(session_id)
            if not company_id:
                error_msg = f"Session {session_id} not found"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "company_id": None,
                    "session_id": str(session_id),
                    "total_pending": 0,
                    "downloaded": 0,
                    "failed": 0,
                    "errors": []
                }

        logger.info(f"📥 Starting F29 PDF download for company {company_id} (max: {max_per_company})")

        # 2. Obtener lista de PDFs pendientes
        pending_downloads = await self.get_pending_f29_downloads(
            company_id=company_id,
            limit=max_per_company
        )

        if not pending_downloads:
            logger.info(f"ℹ️ No pending F29 PDFs for company {company_id}")
            return {
                "success": True,
                "company_id": str(company_id),
                "session_id": str(session_id),
                "total_pending": 0,
                "downloaded": 0,
                "failed": 0,
                "errors": [],
                "message": "No pending PDFs to download"
            }

        logger.info(f"📋 Found {len(pending_downloads)} pending PDFs")

        # 3. Descargar cada PDF
        downloaded = 0
        failed = 0
        errors = []

        for download in pending_downloads:
            try:
                logger.info(
                    f"📥 Downloading PDF for folio {download.sii_folio} "
                    f"(period: {download.period_display})"
                )

                result = await self.download_and_save_f29_pdf(
                    download_id=str(download.id),
                    session_id=session_id
                )

                if result.get("success"):
                    downloaded += 1
                    logger.info(f"✅ Downloaded PDF for folio {download.sii_folio}")
                else:
                    failed += 1
                    error_msg = result.get("error", "Unknown error")
                    logger.error(
                        f"❌ Failed to download PDF for folio {download.sii_folio}: {error_msg}"
                    )
                    errors.append({
                        "folio": download.sii_folio,
                        "period": download.period_display,
                        "error": error_msg
                    })

            except Exception as e:
                failed += 1
                logger.error(
                    f"❌ Exception downloading PDF for folio {download.sii_folio}: {e}",
                    exc_info=True
                )
                errors.append({
                    "folio": download.sii_folio,
                    "period": download.period_display,
                    "error": str(e)
                })

        logger.info(
            f"✅ F29 PDF download completed: {downloaded} downloaded, {failed} failed"
        )

        return {
            "success": True,
            "company_id": str(company_id),
            "session_id": str(session_id),
            "total_pending": len(pending_downloads),
            "downloaded": downloaded,
            "failed": failed,
            "errors": errors
        }

    # =============================================================================
    # PROPUESTA F29
    # =============================================================================

    async def get_propuesta_f29(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene la propuesta de declaración F29 pre-calculada por el SII.

        Args:
            session_id: ID de la sesión en la DB
            periodo: Período tributario en formato YYYYMM (ej: "202510")
            force_new_login: Si True, fuerza nuevo login

        Returns:
            Dict con la propuesta completa del F29

        Raises:
            ValueError: Si la sesión no existe
            Exception: Si falla la obtención de la propuesta
        """
        creds = await self.get_stored_credentials(session_id)
        if not creds:
            raise ValueError(f"Session {session_id} not found")

        # Función sincrónica que usa el cliente SII
        def _run_extraction():
            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=creds.get("cookies"),
                headless=True
            ) as client:
                # Login si es necesario
                if force_new_login:
                    client.login(force_new=True)

                # Obtener propuesta F29
                result = client.get_propuesta_f29(periodo=periodo)

                # Obtener cookies actualizadas
                updated_cookies = client.get_cookies()

                return result, updated_cookies

        try:
            logger.info(f"📊 Fetching F29 propuesta - Period: {periodo}")

            # Ejecutar en thread separado
            result, updated_cookies = await asyncio.to_thread(_run_extraction)

            # Actualizar cookies en la sesión
            if updated_cookies:
                await self.save_cookies(session_id, updated_cookies)
                await self.db.commit()
                logger.debug(f"💾 Fresh cookies persisted to database for session {session_id}")

            logger.info("✅ F29 propuesta retrieved successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Error fetching F29 propuesta: {e}", exc_info=True)
            raise

    async def get_tasa_ppmo(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        categoria_tributaria: int = 1,
        tipo_formulario: str = "FMNINT",
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene la tasa de PPMO para el F29.

        Args:
            session_id: ID de la sesión en la DB
            periodo: Período tributario en formato YYYYMM (ej: "202510")
            categoria_tributaria: Categoría tributaria (1=Primera categoría, default: 1)
            tipo_formulario: Tipo de formulario (default: "FMNINT")
            force_new_login: Si True, fuerza nuevo login

        Returns:
            Dict con información de tasa PPMO

        Raises:
            ValueError: Si la sesión no existe
            Exception: Si falla la obtención
        """
        creds = await self.get_stored_credentials(session_id)
        if not creds:
            raise ValueError(f"Session {session_id} not found")

        # Función sincrónica que usa el cliente SII
        def _run_extraction():
            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=creds.get("cookies"),
                headless=True
            ) as client:
                # Login si es necesario
                if force_new_login:
                    client.login(force_new=True)

                # Obtener tasa PPMO
                result = client.get_tasa_ppmo(
                    periodo=periodo,
                    categoria_tributaria=categoria_tributaria,
                    tipo_formulario=tipo_formulario
                )

                # Obtener cookies actualizadas
                updated_cookies = client.get_cookies()

                return result, updated_cookies

        try:
            logger.info(f"📊 Fetching PPMO tasa - Period: {periodo}")

            # Ejecutar en thread separado
            result, updated_cookies = await asyncio.to_thread(_run_extraction)

            # Actualizar cookies en la sesión
            if updated_cookies:
                await self.save_cookies(session_id, updated_cookies)
                await self.db.commit()
                logger.debug(f"💾 Fresh cookies persisted to database for session {session_id}")

            logger.info("✅ PPMO tasa retrieved successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Error fetching PPMO tasa: {e}", exc_info=True)
            raise

    # =============================================================================
    # LISTADO DE FORMULARIOS
    # =============================================================================

    async def list_f29_forms(
        self,
        company_id: Union[str, UUID],
        form_type: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
        pdf_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lista formularios F29 de una empresa con filtros opcionales

        Args:
            company_id: ID de la empresa
            form_type: Tipo de formulario ('monthly' para mensuales, 'annual' para anuales)
            year: Filtrar por año
            status: Filtrar por estado del formulario ('Vigente', 'Rectificado', 'Anulado')
            pdf_status: Filtrar por estado de descarga del PDF ('pending', 'downloaded', 'error')

        Returns:
            Dict con lista de formularios y totales:
            {
                "forms": [...],
                "total": int,
                "filtered": int
            }
        """
        from uuid import UUID as UUIDType
        from sqlalchemy import and_, desc

        # Convertir a UUID si es string
        if isinstance(company_id, str):
            company_id = UUIDType(company_id)

        logger.info(
            f"📋 Listing F29 forms for company {company_id}: "
            f"form_type={form_type}, year={year}, status={status}, pdf_status={pdf_status}"
        )

        # 1. Construir query base
        query = select(Form29SIIDownload).where(
            Form29SIIDownload.company_id == company_id
        )

        # 2. Aplicar filtros
        filters = []

        # Filtro por tipo de formulario
        if form_type == 'monthly':
            # Mensuales: period_month entre 1 y 12
            filters.append(
                and_(
                    Form29SIIDownload.period_month >= 1,
                    Form29SIIDownload.period_month <= 12
                )
            )
        elif form_type == 'annual':
            # Anuales: period_month = 13 (si existe en el sistema)
            # Por ahora todos son mensuales, pero dejamos la lógica preparada
            filters.append(Form29SIIDownload.period_month == 13)

        # Filtro por año
        if year:
            filters.append(Form29SIIDownload.period_year == year)

        # Filtro por estado
        if status:
            filters.append(Form29SIIDownload.status == status)

        # Filtro por estado de PDF
        if pdf_status:
            filters.append(Form29SIIDownload.pdf_download_status == pdf_status)

        if filters:
            query = query.where(and_(*filters))

        # 3. Ordenar por periodo (más reciente primero)
        query = query.order_by(
            desc(Form29SIIDownload.period_year),
            desc(Form29SIIDownload.period_month)
        )

        # 4. Ejecutar query
        result = await self.db.execute(query)
        forms = result.scalars().all()

        # 5. Obtener total sin filtros (para estadísticas)
        total_query = select(Form29SIIDownload).where(
            Form29SIIDownload.company_id == company_id
        )
        total_result = await self.db.execute(total_query)
        total_forms = len(total_result.scalars().all())

        return {
            "forms": forms,
            "total": total_forms,
            "filtered": len(forms)
        }

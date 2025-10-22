"""
Servicio de integración SII - Capa de aplicación
Conecta el módulo SII (agnostic) con la base de datos de la aplicación
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, update

from app.integrations.sii import SIIClient
from app.db.models import Session as SessionModel, Company, Form29SIIDownload
from app.integrations.sii.exceptions import (
    AuthenticationError,
    ExtractionError,
    SIIUnavailableException
)
from app.config.database import SyncSessionLocal

logger = logging.getLogger(__name__)


class SIIService:
    """
    Servicio que conecta el módulo SII con la base de datos.

    Responsabilidades:
    1. Obtener credenciales desde la DB
    2. Reutilizar cookies almacenadas
    3. Actualizar cookies en la DB después de extracciones
    4. Manejar errores y reintentos
    5. Guardar datos extraídos en la DB

    El módulo SII permanece completamente agnostic de la DB.

    IMPORTANTE: Este servicio usa operaciones SÍNCRONAS de DB cuando trabaja con Selenium
    para evitar conflictos entre async/sync contexts.
    """

    def __init__(self, db: Union[AsyncSession, Session]):
        """
        Inicializa el servicio

        Args:
            db: Sesión de base de datos (async o sync)
        """
        self.db = db
        self.is_async = isinstance(db, AsyncSession)

    def _get_stored_credentials_sync(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene las credenciales almacenadas en la DB (versión SÍNCRONA)

        Args:
            session_id: ID de la sesión en la DB

        Returns:
            Dict con rut, password y cookies (si existen)
        """
        # Usar una sesión sync separada
        with SyncSessionLocal() as sync_db:
            stmt = select(SessionModel).where(SessionModel.id == session_id)
            result = sync_db.execute(stmt)
            session = result.scalar_one_or_none()

            if not session:
                return None

            return {
                "rut": session.company.rut,
                "password": session.company.sii_password,
                "cookies": session.cookies.get("sii_cookies") if session.cookies else None,
                "session_db_id": session.id,
                "company_id": session.company_id
            }

    async def get_stored_credentials(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene las credenciales almacenadas en la DB (versión ASYNC - para compatibilidad)

        Args:
            session_id: ID de la sesión en la DB

        Returns:
            Dict con rut, password y cookies (si existen)
        """
        stmt = select(SessionModel).where(SessionModel.id == session_id).options(
            selectinload(SessionModel.company)
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        return {
            "rut": session.company.rut,
            "password": session.company.sii_password,
            "cookies": session.cookies.get("sii_cookies") if session.cookies else None,
            "session_db_id": session.id,
            "company_id": session.company_id
        }

    def _save_cookies_sync(self, session_id: int, cookies: List[Dict]) -> None:
        """
        Guarda las cookies en la DB para reutilización futura (versión SÍNCRONA)

        Args:
            session_id: ID de la sesión en la DB
            cookies: Lista de cookies del SII
        """
        with SyncSessionLocal() as sync_db:
            stmt = (
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(
                    cookies={
                        "sii_cookies": cookies,
                        "updated_at": datetime.utcnow().isoformat()
                    },
                    last_accessed_at=datetime.utcnow()
                )
            )
            sync_db.execute(stmt)
            sync_db.commit()

            logger.debug(f"✅ Saved {len(cookies)} cookies to DB for session {session_id}")

    async def save_cookies(self, session_id: int, cookies: List[Dict]) -> None:
        """
        Guarda las cookies en la DB para reutilización futura (versión ASYNC - para compatibilidad)

        Args:
            session_id: ID de la sesión en la DB
            cookies: Lista de cookies del SII
        """
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                cookies={
                    "sii_cookies": cookies,
                    "updated_at": datetime.utcnow().isoformat()
                },
                last_accessed_at=datetime.utcnow()
            )
        )
        await self.db.execute(stmt)
        # No commit aquí - se hace en el caller
        # await self.db.commit()

        logger.debug(f"✅ Saved {len(cookies)} cookies to DB for session {session_id}")

    async def extract_contribuyente(
        self,
        session_id: int,
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae información del contribuyente usando el módulo SII

        Args:
            session_id: ID de la sesión en la DB
            force_new_login: Si True, ignora cookies y hace login fresco

        Returns:
            Información del contribuyente

        Raises:
            AuthenticationError: Si falla la autenticación
            ExtractionError: Si falla la extracción
        """
        # 1. Obtener credenciales desde DB
        creds = await self.get_stored_credentials(session_id)
        if not creds:
            raise ValueError(f"Session {session_id} not found")

        # 2. Usar cookies almacenadas si existen (a menos que se fuerce nuevo login)
        cookies = None if force_new_login else creds.get("cookies")

        # 3. Usar el módulo SII (completamente agnostic de DB)
        # Función sincrónica que ejecuta Selenium
        def _run_extraction():
            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=cookies,
                headless=True
            ) as client:

                # Login solo si no hay cookies válidas
                if not cookies:
                    logger.info(f"🔐 No cookies found, performing login for {creds['rut']}")
                    client.login()
                    new_cookies = client.get_cookies()
                else:
                    logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")
                    new_cookies = None

                # Extraer datos
                info = client.get_contribuyente()

                # Actualizar cookies por si cambiaron
                updated_cookies = client.get_cookies()

                return info, new_cookies, updated_cookies

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            info, new_cookies, updated_cookies = await asyncio.to_thread(_run_extraction)

            # Ahora SÍ podemos hacer operaciones async de DB
            if new_cookies:
                await self.save_cookies(session_id, new_cookies)

            if updated_cookies:
                await self.save_cookies(session_id, updated_cookies)

            return info

        except AuthenticationError as e:
            logger.error(f"❌ Authentication failed for session {session_id}: {e}")

            # Si falló con cookies, reintentar con login fresco
            if cookies and not force_new_login:
                logger.info("🔄 Retrying with fresh login...")
                return await self.extract_contribuyente(session_id, force_new_login=True)

            raise

        except SIIUnavailableException as e:
            logger.error(f"⚠️ SII temporarily unavailable: {e}")
            raise

    async def extract_compras(
        self,
        session_id: int,
        periodo: str,
        tipo_doc: str = "33",
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae DTEs de compra

        Args:
            session_id: ID de la sesión en la DB
            periodo: Período en formato YYYYMM (ej: "202510")
            tipo_doc: Tipo de documento (default: "33" = Factura Electrónica)
            force_new_login: Si True, ignora cookies y hace login fresco

        Returns:
            Dict con status, data, extraction_method
        """
        # Función sincrónica que ejecuta TODO en sync (Selenium + DB)
        def _run_extraction():
            # Obtener credenciales de forma síncrona
            creds = self._get_stored_credentials_sync(session_id)
            if not creds:
                raise ValueError(f"Session {session_id} not found")

            # Usar cookies solo si no forzamos nuevo login
            cookies = None if force_new_login else creds.get("cookies")

            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=cookies,
                headless=True
            ) as client:

                # Login si no hay cookies o si se fuerza
                if not cookies:
                    logger.info(f"🔐 Performing login for {creds['rut']}")
                    client.login()
                    new_cookies = client.get_cookies()
                    # Guardar cookies de forma síncrona
                    self._save_cookies_sync(session_id, new_cookies)
                else:
                    logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")

                # Extraer compras (operación sincrónica de Selenium)
                result = client.get_compras(periodo=periodo, tipo_doc=tipo_doc)

                # Actualizar cookies de forma síncrona
                updated_cookies = client.get_cookies()
                self._save_cookies_sync(session_id, updated_cookies)

                return result

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            result = await asyncio.to_thread(_run_extraction)
            return result

        except (AuthenticationError, ExtractionError) as e:
            # Si falló con cookies almacenadas, reintentar con login fresco
            if not force_new_login and "401" in str(e):
                logger.warning(f"⚠️ Cookies expired (401), retrying with fresh login...")
                return await self.extract_compras(session_id, periodo, tipo_doc, force_new_login=True)
            raise

    async def extract_ventas(
        self,
        session_id: int,
        periodo: str,
        tipo_doc: str = "33",
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae DTEs de venta

        Args:
            session_id: ID de la sesión en la DB
            periodo: Período en formato YYYYMM
            tipo_doc: Tipo de documento
            force_new_login: Si True, ignora cookies y hace login fresco

        Returns:
            Dict con status, data, extraction_method
        """
        # Función sincrónica que ejecuta TODO en sync (Selenium + DB)
        def _run_extraction():
            # Obtener credenciales de forma síncrona
            creds = self._get_stored_credentials_sync(session_id)
            if not creds:
                raise ValueError(f"Session {session_id} not found")

            # Usar cookies solo si no forzamos nuevo login
            cookies = None if force_new_login else creds.get("cookies")

            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=cookies,
                headless=True
            ) as client:

                # Login si no hay cookies o si se fuerza
                if not cookies:
                    logger.info(f"🔐 Performing login for {creds['rut']}")
                    client.login()
                    new_cookies = client.get_cookies()
                    # Guardar cookies de forma síncrona
                    self._save_cookies_sync(session_id, new_cookies)
                else:
                    logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")

                # Extraer ventas (operación sincrónica de Selenium)
                result = client.get_ventas(periodo=periodo, tipo_doc=tipo_doc)

                # Actualizar cookies de forma síncrona
                updated_cookies = client.get_cookies()
                self._save_cookies_sync(session_id, updated_cookies)

                return result

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            result = await asyncio.to_thread(_run_extraction)
            return result

        except (AuthenticationError, ExtractionError) as e:
            # Si falló con cookies almacenadas, reintentar con login fresco
            if not force_new_login and "401" in str(e):
                logger.warning(f"⚠️ Cookies expired (401), retrying with fresh login...")
                return await self.extract_ventas(session_id, periodo, tipo_doc, force_new_login=True)
            raise

    async def extract_resumen(
        self,
        session_id: int,
        periodo: str,
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Extrae resumen de compras y ventas del período

        Args:
            session_id: ID de la sesión en la DB
            periodo: Período en formato YYYYMM (ej: "202510")
            force_new_login: Si True, ignora cookies y hace login fresco

        Returns:
            Dict con resumen_compras y resumen_ventas por tipo de documento
        """
        # Función sincrónica que ejecuta TODO en sync (Selenium + DB)
        def _run_extraction():
            # Obtener credenciales de forma síncrona
            creds = self._get_stored_credentials_sync(session_id)
            if not creds:
                raise ValueError(f"Session {session_id} not found")

            # Usar cookies solo si no forzamos nuevo login
            cookies = None if force_new_login else creds.get("cookies")

            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=cookies,
                headless=True
            ) as client:

                # Login si no hay cookies o si se fuerza
                if not cookies:
                    logger.info(f"🔐 Performing login for {creds['rut']}")
                    client.login()
                    new_cookies = client.get_cookies()
                    # Guardar cookies de forma síncrona
                    self._save_cookies_sync(session_id, new_cookies)
                else:
                    logger.debug(f"🍪 Reusing stored cookies for {creds['rut']}")

                # Extraer resumen (operación sincrónica)
                result = client.get_resumen(periodo=periodo)

                # Actualizar cookies de forma síncrona
                updated_cookies = client.get_cookies()
                self._save_cookies_sync(session_id, updated_cookies)

                return result

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            result = await asyncio.to_thread(_run_extraction)
            return result

        except (AuthenticationError, ExtractionError) as e:
            # Si falló con cookies almacenadas, reintentar con login fresco
            if not force_new_login and "401" in str(e):
                logger.warning(f"⚠️ Cookies expired (401), retrying with fresh login...")
                return await self.extract_resumen(session_id, periodo, force_new_login=True)
            raise

    async def extract_f29_lista(
        self,
        session_id: int,
        anio: str
    ) -> List[Dict[str, Any]]:
        """
        Extrae lista de formularios F29

        Args:
            session_id: ID de la sesión en la DB
            anio: Año (ej: "2024")

        Returns:
            Lista de formularios F29
        """
        creds = await self.get_stored_credentials(session_id)
        if not creds:
            raise ValueError(f"Session {session_id} not found")

        # Función sincrónica que ejecuta Selenium
        def _run_extraction():
            with SIIClient(
                tax_id=creds["rut"],
                password=creds["password"],
                cookies=creds.get("cookies"),
                headless=True
            ) as client:

                # F29 requiere login fresco
                client.login(force_new=True)
                new_cookies = client.get_cookies()

                # Extraer lista F29
                result = client.get_f29_lista(anio=anio)

                # Obtener cookies actualizadas
                updated_cookies = client.get_cookies()

                return result, new_cookies, updated_cookies

        try:
            # Ejecutar en thread separado para no bloquear el event loop
            result, new_cookies, updated_cookies = await asyncio.to_thread(_run_extraction)

            # Ahora SÍ podemos hacer operaciones async de DB
            if new_cookies:
                await self.save_cookies(session_id, new_cookies)

            if updated_cookies:
                await self.save_cookies(session_id, updated_cookies)

            return result

        except AuthenticationError:
            return await self.extract_f29_lista(session_id, anio)

    async def save_f29_downloads(
        self,
        company_id: str,
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
                    existing.sii_id_interno = formulario.get('id_interno_sii')

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

    async def download_and_save_f29_pdf(
        self,
        download_id: str,
        session_id: int,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Descarga el PDF de un F29 desde el SII y lo guarda en Supabase Storage

        Args:
            download_id: UUID del registro Form29SIIDownload
            session_id: ID de la sesión para autenticación
            max_retries: Número máximo de reintentos

        Returns:
            Dict con status, url y mensaje

        Example:
            >>> result = await service.download_and_save_f29_pdf(
            ...     download_id="550e8400-e29b-41d4-a716-446655440000",
            ...     session_id=123
            ... )
            >>> if result['success']:
            ...     print(f"PDF guardado en: {result['url']}")
        """
        from uuid import UUID
        from app.services.storage import get_pdf_storage
        from app.utils.pdf_validator import is_valid_f29_pdf, get_pdf_size_mb

        try:
            # 1. Obtener el registro de descarga
            stmt = select(Form29SIIDownload).where(
                Form29SIIDownload.id == UUID(download_id)
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
                # Actualizar estado
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

                        with SIIClient(
                            tax_id=creds["rut"],
                            password=creds["password"],
                            cookies=creds.get("cookies"),
                            headless=True
                        ) as client:
                            # Login fresco para F29
                            client.login(force_new=True)

                            # Descargar PDF
                            pdf = client.get_f29_compacto(
                                folio=download.sii_folio,
                                id_interno_sii=download.sii_id_interno
                            )

                            # Actualizar cookies
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

            # 5. Subir a Supabase Storage
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

            # 6. Actualizar registro en DB
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


# Funciones helper para usar en routers
async def get_sii_service(db: AsyncSession) -> SIIService:
    """Dependency injection para FastAPI"""
    return SIIService(db)

"""
Servicio de sincronización de documentos tributarios SII

Este servicio coordina la extracción y persistencia de documentos tributarios
desde el SII hacia la base de datos de la aplicación.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from uuid import UUID

from app.services.sii.service import SIIService
from app.db.models import Company, Contact, PurchaseDocument, SalesDocument, Session as SessionModel

logger = logging.getLogger(__name__)


class SIISyncService:
    """
    Servicio de sincronización de documentos tributarios

    Responsabilidades:
    1. Calcular períodos a sincronizar (últimos N meses)
    2. Extraer compras y ventas del SII usando SIIService
    3. Guardar/actualizar documentos en DB (upsert)
    4. Trackear progreso (nuevos, actualizados, errores)
    5. Logging detallado del proceso
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio de sincronización

        Args:
            db: Sesión de base de datos async
        """
        self.db = db
        self.sii_service = SIIService(db)

    async def sync_last_n_months(
        self,
        session_id: UUID,
        months: int = 3,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Sincroniza documentos tributarios de los últimos N meses

        Args:
            session_id: ID de sesión con credenciales SII
            months: Cantidad de meses a sincronizar (default: 3)
            progress_callback: Función opcional para reportar progreso

        Returns:
            Dict con resumen de sincronización:
            {
                "compras": {"total": int, "nuevos": int, "actualizados": int},
                "ventas": {"total": int, "nuevos": int, "actualizados": int},
                "periods_processed": List[str],
                "errors": List[Dict],
                "duration_seconds": float
            }

        Raises:
            ValueError: Si la sesión no existe
        """
        start_time = datetime.now()

        logger.info(f"🚀 Starting sync for session {session_id} - last {months} months")

        # Obtener company_id de la sesión
        company_id = await self._get_company_id_from_session(session_id)

        # Calcular períodos a sincronizar
        periods = self._calculate_periods(months)
        logger.info(f"📅 Periods to sync: {periods}")

        # Resultado acumulado
        results = {
            "compras": {"total": 0, "nuevos": 0, "actualizados": 0},
            "ventas": {"total": 0, "nuevos": 0, "actualizados": 0},
            "periods_processed": [],
            "errors": []
        }

        # Sincronizar cada período
        for period in periods:
            logger.info(f"📄 Processing period: {period}")

            # Sincronizar compras del período
            compras_result = {"total": 0, "nuevos": 0, "actualizados": 0}
            try:
                compras_result = await self._sync_compras_period(
                    session_id=session_id,
                    company_id=company_id,
                    period=period
                )
                results["compras"]["total"] += compras_result["total"]
                results["compras"]["nuevos"] += compras_result["nuevos"]
                results["compras"]["actualizados"] += compras_result["actualizados"]
            except Exception as e:
                error_msg = f"Error processing compras for period {period}"
                logger.error(
                    f"❌ {error_msg}",
                    exc_info=True,
                    extra={
                        "session_id": str(session_id),
                        "company_id": str(company_id),
                        "period": period,
                        "document_type": "compras",
                        "error_type": type(e).__name__
                    }
                )
                results["errors"].append({
                    "period": period,
                    "type": "compras",
                    "error": str(e),
                    "exception_type": type(e).__name__
                })

            # Sincronizar ventas del período (independiente de si compras falló)
            ventas_result = {"total": 0, "nuevos": 0, "actualizados": 0}
            try:
                ventas_result = await self._sync_ventas_period(
                    session_id=session_id,
                    company_id=company_id,
                    period=period
                )
                results["ventas"]["total"] += ventas_result["total"]
                results["ventas"]["nuevos"] += ventas_result["nuevos"]
                results["ventas"]["actualizados"] += ventas_result["actualizados"]
            except Exception as e:
                error_msg = f"Error processing ventas for period {period}"
                logger.error(
                    f"❌ {error_msg}",
                    exc_info=True,
                    extra={
                        "session_id": str(session_id),
                        "company_id": str(company_id),
                        "period": period,
                        "document_type": "ventas",
                        "error_type": type(e).__name__
                    }
                )
                results["errors"].append({
                    "period": period,
                    "type": "ventas",
                    "error": str(e),
                    "exception_type": type(e).__name__
                })

            # Marcar período como procesado (aunque haya errores parciales)
            results["periods_processed"].append(period)

            # Callback de progreso
            if progress_callback:
                await progress_callback(period, results)

            logger.info(
                f"✅ Period {period} completed: "
                f"Compras ({compras_result['nuevos']} nuevos, {compras_result['actualizados']} actualizados), "
                f"Ventas ({ventas_result['nuevos']} nuevos, {ventas_result['actualizados']} actualizados)"
            )

        # Calcular duración
        duration = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = duration

        logger.info(
            f"🎉 Sync completed in {duration:.2f}s: "
            f"Compras: {results['compras']}, Ventas: {results['ventas']}, "
            f"Errors: {len(results['errors'])}"
        )

        return results

    async def _get_company_id_from_session(self, session_id: UUID) -> UUID:
        """Obtiene el company_id de una sesión"""
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        return session.company_id

    def _calculate_periods(self, months: int) -> List[str]:
        """
        Calcula los períodos en formato YYYYMM

        Args:
            months: Cantidad de meses hacia atrás

        Returns:
            Lista de períodos en formato YYYYMM, ordenados descendente

        Example:
            Si hoy es 2024-03-15 y months=3:
            ['202403', '202402', '202401']
        """
        periods = []
        now = datetime.now()

        for i in range(months):
            # Retroceder i meses
            target_date = now - timedelta(days=30 * i)
            period = target_date.strftime("%Y%m")

            # Evitar duplicados (puede pasar si el mes tiene 31 días)
            if period not in periods:
                periods.append(period)

        return periods

    async def _get_or_create_contact(
        self,
        company_id: UUID,
        rut: Optional[str],
        name: Optional[str],
        contact_type: str  # 'provider' or 'client'
    ) -> Optional[UUID]:
        """
        Busca o crea un contacto basado en el RUT

        Args:
            company_id: ID de la compañía
            rut: RUT del contacto
            name: Nombre del contacto
            contact_type: Tipo de contacto ('provider' o 'client')

        Returns:
            UUID del contacto o None si no se puede crear
        """
        if not rut or not name:
            return None

        # Normalizar RUT (eliminar puntos, guiones, etc)
        rut = rut.strip().replace(".", "").replace("-", "").upper()

        # Buscar contacto existente
        stmt = select(Contact).where(
            Contact.company_id == company_id,
            Contact.rut == rut
        )
        result = await self.db.execute(stmt)
        existing_contact = result.scalar_one_or_none()

        if existing_contact:
            # Verificar si necesitamos actualizar el tipo
            if existing_contact.contact_type != 'both':
                # Si es proveedor y ahora es cliente (o viceversa), cambiar a 'both'
                if (existing_contact.contact_type == 'provider' and contact_type == 'client') or \
                   (existing_contact.contact_type == 'client' and contact_type == 'provider'):
                    existing_contact.contact_type = 'both'
                    existing_contact.updated_at = datetime.utcnow()
                    logger.info(f"📝 Updated contact {rut} type to 'both'")

            return existing_contact.id

        # Crear nuevo contacto
        try:
            new_contact = Contact(
                company_id=company_id,
                rut=rut,
                business_name=name,
                contact_type=contact_type,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(new_contact)
            await self.db.flush()  # Flush para obtener el ID sin commit

            logger.info(f"✨ Created new {contact_type}: {name} ({rut})")
            return new_contact.id

        except Exception as e:
            logger.error(f"❌ Error creating contact {rut}: {e}")
            return None

    async def _sync_compras_period(
        self,
        session_id: UUID,
        company_id: UUID,
        period: str
    ) -> Dict[str, int]:
        """
        Sincroniza compras de un período específico

        Primero obtiene el resumen para saber qué tipos de documentos sincronizar,
        luego extrae cada tipo que tenga documentos.

        Returns:
            {"total": int, "nuevos": int, "actualizados": int}
        """
        logger.info(f"📥 Extracting compras summary for period {period}")

        # Paso 1: Obtener resumen del período
        resumen_result = await self.sii_service.extract_resumen(
            session_id=session_id,
            periodo=period
        )

        # Validar que tenemos el resumen
        if not resumen_result.get("data") or not resumen_result["data"].get("resumen_compras"):
            logger.warning(f"⚠️ No resumen_compras data for period {period}")
            return {"total": 0, "nuevos": 0, "actualizados": 0}

        resumen_compras = resumen_result["data"]["resumen_compras"]

        # Paso 2: Procesar cada item del resumen
        # El resumen viene con estructura: {"data": [...items...]}
        resumen_items = resumen_compras.get("data", []) if isinstance(resumen_compras, dict) else []

        total_docs = 0
        total_nuevos = 0
        total_actualizados = 0

        for item in resumen_items:
            try:
                tipo_doc = str(item.get("rsmnTipoDocInteger", ""))
                if not tipo_doc:
                    continue

                cantidad_docs = item.get("rsmnTotDoc", 0)
                nombre_tipo = item.get("dcvNombreTipoDoc", f"Tipo {tipo_doc}")

                logger.info(f"  📋 {nombre_tipo} (Tipo {tipo_doc}): {cantidad_docs} documentos")

                # Verificar si es resumen mensual (sin detalle) o si tiene documentos individuales
                es_resumen = (
                    item.get("dcvTipoIngresoDoc") == "RESUMEN" or
                    item.get("rsmnLink") == False
                )

                if es_resumen:
                    # Es un resumen mensual (boletas, comprobantes) - guardar como 1 documento
                    logger.info(f"  📊 Tipo {tipo_doc} es RESUMEN mensual - creando documento agregado")
                    nuevos, actualizados = await self._save_resumen_mensual_compras(
                        company_id=company_id,
                        period=period,
                        tipo_doc=tipo_doc,
                        resumen_item=item
                    )
                    total_docs += 1
                    total_nuevos += nuevos
                    total_actualizados += actualizados
                else:
                    # Tiene detalle individual - extraer cada documento
                    logger.info(f"  📤 Tipo {tipo_doc} tiene detalle - extrayendo documentos individuales")

                    result = await self.sii_service.extract_compras(
                        session_id=session_id,
                        periodo=period,
                        tipo_doc=tipo_doc
                    )

                    # Validar que tenemos datos
                    if not result.get("data"):
                        logger.info(f"  ℹ️ No documents found for tipo {tipo_doc}")
                        continue

                    documents = result["data"]
                    logger.info(f"  ✅ Extracted {len(documents)} documents tipo {tipo_doc}")

                    # Guardar en DB (pasar tipo_doc para mapeo correcto)
                    nuevos, actualizados = await self._save_compras(
                        company_id=company_id,
                        documents=documents,
                        tipo_doc=tipo_doc
                    )

                    total_docs += len(documents)
                    total_nuevos += nuevos
                    total_actualizados += actualizados

            except Exception as e:
                logger.error(f"❌ Error processing compras tipo {item.get('rsmnTipoDocInteger')}: {e}")
                # Continuar con el siguiente tipo

        logger.info(f"📊 Compras sync completed: {total_docs} docs, {total_nuevos} nuevos, {total_actualizados} actualizados")

        return {
            "total": total_docs,
            "nuevos": total_nuevos,
            "actualizados": total_actualizados
        }

    async def _sync_ventas_period(
        self,
        session_id: UUID,
        company_id: UUID,
        period: str
    ) -> Dict[str, int]:
        """
        Sincroniza ventas de un período específico

        Primero obtiene el resumen para saber qué tipos de documentos sincronizar,
        luego extrae cada tipo que tenga documentos.

        Returns:
            {"total": int, "nuevos": int, "actualizados": int}
        """
        logger.info(f"📤 Extracting ventas summary for period {period}")

        # Paso 1: Obtener resumen del período
        resumen_result = await self.sii_service.extract_resumen(
            session_id=session_id,
            periodo=period
        )

        # Validar que tenemos el resumen
        if not resumen_result.get("data") or not resumen_result["data"].get("resumen_ventas"):
            logger.warning(f"⚠️ No resumen_ventas data for period {period}")
            return {"total": 0, "nuevos": 0, "actualizados": 0}

        resumen_ventas = resumen_result["data"]["resumen_ventas"]

        # Paso 2: Procesar cada item del resumen
        # El resumen viene con estructura: {"data": [...items...]}
        resumen_items = resumen_ventas.get("data", []) if isinstance(resumen_ventas, dict) else []

        total_docs = 0
        total_nuevos = 0
        total_actualizados = 0

        for item in resumen_items:
            try:
                tipo_doc = str(item.get("rsmnTipoDocInteger", ""))
                if not tipo_doc:
                    continue

                cantidad_docs = item.get("rsmnTotDoc", 0)
                nombre_tipo = item.get("dcvNombreTipoDoc", f"Tipo {tipo_doc}")

                logger.info(f"  📋 {nombre_tipo} (Tipo {tipo_doc}): {cantidad_docs} documentos")

                # Verificar si es resumen mensual (sin detalle) o si tiene documentos individuales
                es_resumen = (
                    item.get("dcvTipoIngresoDoc") == "RESUMEN" or
                    item.get("rsmnLink") == False
                )

                if es_resumen:
                    # Es un resumen mensual (boletas, comprobantes) - guardar como 1 documento
                    logger.info(f"  📊 Tipo {tipo_doc} es RESUMEN mensual - creando documento agregado")
                    nuevos, actualizados = await self._save_resumen_mensual_ventas(
                        company_id=company_id,
                        period=period,
                        tipo_doc=tipo_doc,
                        resumen_item=item
                    )
                    total_docs += 1
                    total_nuevos += nuevos
                    total_actualizados += actualizados
                else:
                    # Tiene detalle individual - extraer cada documento
                    logger.info(f"  📤 Tipo {tipo_doc} tiene detalle - extrayendo documentos individuales")

                    result = await self.sii_service.extract_ventas(
                        session_id=session_id,
                        periodo=period,
                        tipo_doc=tipo_doc
                    )

                    # Validar que tenemos datos
                    if not result.get("data"):
                        logger.info(f"  ℹ️ No documents found for tipo {tipo_doc}")
                        continue

                    documents = result["data"]
                    logger.info(f"  ✅ Extracted {len(documents)} documents tipo {tipo_doc}")

                    # Guardar en DB (pasar tipo_doc para mapeo correcto)
                    nuevos, actualizados = await self._save_ventas(
                        company_id=company_id,
                        documents=documents,
                        tipo_doc=tipo_doc
                    )

                    total_docs += len(documents)
                    total_nuevos += nuevos
                    total_actualizados += actualizados

            except Exception as e:
                logger.error(f"❌ Error processing ventas item: {e}")
                # Continuar con el siguiente item

        logger.info(f"📊 Ventas sync completed: {total_docs} docs, {total_nuevos} nuevos, {total_actualizados} actualizados")

        return {
            "total": total_docs,
            "nuevos": total_nuevos,
            "actualizados": total_actualizados
        }

    async def _save_compras(
        self,
        company_id: UUID,
        documents: List[Dict[str, Any]],
        tipo_doc: str
    ) -> tuple[int, int]:
        """
        Guarda documentos de compra en DB usando bulk upsert

        Args:
            company_id: ID de la compañía
            documents: Lista de documentos extraídos del SII
            tipo_doc: Tipo de documento SII (33, 56, 61, etc.)

        Returns:
            (nuevos, actualizados)
        """
        if not documents:
            return 0, 0

        # Preparar datos de todos los documentos
        docs_to_upsert = []
        for doc in documents:
            try:
                folio = doc.get('detNroDoc') or doc.get('folio')
                if not folio:
                    logger.warning(f"⚠️ Skipping purchase doc without folio: {doc}")
                    continue

                doc_data = self._parse_purchase_document(
                    company_id=company_id,
                    doc=doc,
                    tipo_doc=tipo_doc
                )

                # Crear o buscar contacto (proveedor) si hay RUT y nombre
                sender_rut = doc_data.get('sender_rut')
                sender_name = doc_data.get('sender_name')
                if sender_rut and sender_name:
                    contact_id = await self._get_or_create_contact(
                        company_id=company_id,
                        rut=sender_rut,
                        name=sender_name,
                        contact_type='provider'
                    )
                    if contact_id:
                        doc_data['contact_id'] = contact_id

                doc_data['created_at'] = datetime.utcnow()
                doc_data['updated_at'] = datetime.utcnow()
                docs_to_upsert.append(doc_data)

            except Exception as e:
                logger.error(f"❌ Error parsing purchase doc {doc.get('detNroDoc')}: {e}")
                continue

        if not docs_to_upsert:
            logger.warning("⚠️ No valid purchase documents to save")
            return 0, 0

        # Obtener folios existentes para contar nuevos vs actualizados
        folios = [doc['folio'] for doc in docs_to_upsert]
        stmt = select(PurchaseDocument.folio).where(
            PurchaseDocument.company_id == company_id,
            PurchaseDocument.folio.in_(folios)
        )
        result = await self.db.execute(stmt)
        existing_folios = set(row[0] for row in result.fetchall())

        nuevos = sum(1 for doc in docs_to_upsert if doc['folio'] not in existing_folios)
        actualizados = len(docs_to_upsert) - nuevos

        # Usar PostgreSQL INSERT ... ON CONFLICT para upsert en batch
        stmt = insert(PurchaseDocument).values(docs_to_upsert)
        stmt = stmt.on_conflict_do_update(
            index_elements=['company_id', 'folio'],
            set_={
                'document_type': stmt.excluded.document_type,
                'issue_date': stmt.excluded.issue_date,
                'sender_rut': stmt.excluded.sender_rut,
                'sender_name': stmt.excluded.sender_name,
                'contact_id': stmt.excluded.contact_id,
                'net_amount': stmt.excluded.net_amount,
                'tax_amount': stmt.excluded.tax_amount,
                'exempt_amount': stmt.excluded.exempt_amount,
                'total_amount': stmt.excluded.total_amount,
                'status': stmt.excluded.status,
                'extra_data': stmt.excluded.extra_data,
                'updated_at': datetime.utcnow()
            }
        )

        await self.db.execute(stmt)
        logger.info(f"💾 Saved compras: {nuevos} nuevos, {actualizados} actualizados")

        return nuevos, actualizados

    async def _save_resumen_mensual_compras(
        self,
        company_id: UUID,
        period: str,
        tipo_doc: str,
        resumen_item: Dict
    ) -> tuple[int, int]:
        """
        Guarda o actualiza un documento de resumen mensual de compras.

        Para documentos tipo RESUMEN (boletas 39, comprobantes 48), se crea
        un único documento mensual que se actualiza en cada sincronización.

        Args:
            company_id: ID de la empresa
            period: Período en formato YYYYMM
            tipo_doc: Tipo de documento (39, 48, etc.)
            resumen_item: Item del resumen con datos agregados

        Returns:
            Tuple (nuevos, actualizados)
        """
        # Generar folio único: PERIODO + TIPO (ej: 20251039)
        folio = int(f"{period}{tipo_doc}")

        logger.debug(f"💾 Saving monthly summary (compras): folio={folio}, tipo={tipo_doc}, period={period}")

        # Buscar documento existente
        stmt = (
            select(PurchaseDocument)
            .where(PurchaseDocument.company_id == company_id)
            .where(PurchaseDocument.folio == folio)
        )
        result = await self.db.execute(stmt)
        existing_doc = result.scalar_one_or_none()

        # Preparar datos del resumen
        doc_data = {
            "company_id": company_id,
            "document_type": self._get_purchase_document_type_name(tipo_doc),
            "folio": folio,
            "issue_date": self._parse_date(f"{period}01"),  # Primer día del mes
            "sender_rut": None,
            "sender_name": "RESUMEN MENSUAL",
            "net_amount": Decimal(str(resumen_item.get('rsmnMntNeto', 0))),
            "tax_amount": Decimal(str(resumen_item.get('rsmnMntIVA', 0))),
            "exempt_amount": Decimal(str(resumen_item.get('rsmnMntExento', 0))),
            "total_amount": Decimal(str(resumen_item.get('rsmnMntTotal', 0))),
            "status": "pending",
            "extra_data": {
                "is_monthly_summary": True,
                "period": period,
                "tipo_doc": tipo_doc,
                "total_documents": resumen_item.get('rsmnTotDoc', 0),
                "resumen_completo": resumen_item
            }
        }

        if existing_doc:
            # Actualizar documento existente
            for key, value in doc_data.items():
                if key != "company_id":  # No actualizar company_id
                    setattr(existing_doc, key, value)

            logger.debug(f"♻️  Updated monthly summary (compras): folio={folio}")
            return 0, 1
        else:
            # Crear nuevo documento
            purchase_doc = PurchaseDocument(**doc_data)
            self.db.add(purchase_doc)
            logger.debug(f"✨ Created monthly summary (compras): folio={folio}")
            return 1, 0

    async def _save_ventas(
        self,
        company_id: UUID,
        documents: List[Dict[str, Any]],
        tipo_doc: str
    ) -> tuple[int, int]:
        """
        Guarda documentos de venta en DB usando bulk upsert

        Args:
            company_id: ID de la compañía
            documents: Lista de documentos extraídos del SII
            tipo_doc: Tipo de documento SII (33, 39, 56, 61, etc.)

        Returns:
            (nuevos, actualizados)
        """
        if not documents:
            return 0, 0

        # Preparar datos de todos los documentos
        docs_to_upsert = []
        for doc in documents:
            try:
                folio = doc.get('detNroDoc') or doc.get('folio')
                if not folio:
                    logger.warning(f"⚠️ Skipping sales doc without folio: {doc}")
                    continue

                doc_data = self._parse_sales_document(
                    company_id=company_id,
                    doc=doc,
                    tipo_doc=tipo_doc
                )

                # Crear o buscar contacto (cliente) si hay RUT y nombre
                recipient_rut = doc_data.get('recipient_rut')
                recipient_name = doc_data.get('recipient_name')
                if recipient_rut and recipient_name:
                    contact_id = await self._get_or_create_contact(
                        company_id=company_id,
                        rut=recipient_rut,
                        name=recipient_name,
                        contact_type='client'
                    )
                    if contact_id:
                        doc_data['contact_id'] = contact_id

                doc_data['created_at'] = datetime.utcnow()
                doc_data['updated_at'] = datetime.utcnow()
                docs_to_upsert.append(doc_data)

            except Exception as e:
                logger.error(f"❌ Error parsing sales doc {doc.get('detNroDoc')}: {e}")
                continue

        if not docs_to_upsert:
            logger.warning("⚠️ No valid sales documents to save")
            return 0, 0

        # Obtener folios existentes para contar nuevos vs actualizados
        folios = [doc['folio'] for doc in docs_to_upsert]
        stmt = select(SalesDocument.folio).where(
            SalesDocument.company_id == company_id,
            SalesDocument.folio.in_(folios)
        )
        result = await self.db.execute(stmt)
        existing_folios = set(row[0] for row in result.fetchall())

        nuevos = sum(1 for doc in docs_to_upsert if doc['folio'] not in existing_folios)
        actualizados = len(docs_to_upsert) - nuevos

        # Usar PostgreSQL INSERT ... ON CONFLICT para upsert en batch
        stmt = insert(SalesDocument).values(docs_to_upsert)
        stmt = stmt.on_conflict_do_update(
            index_elements=['company_id', 'folio'],
            set_={
                'document_type': stmt.excluded.document_type,
                'issue_date': stmt.excluded.issue_date,
                'recipient_rut': stmt.excluded.recipient_rut,
                'recipient_name': stmt.excluded.recipient_name,
                'contact_id': stmt.excluded.contact_id,
                'net_amount': stmt.excluded.net_amount,
                'tax_amount': stmt.excluded.tax_amount,
                'exempt_amount': stmt.excluded.exempt_amount,
                'total_amount': stmt.excluded.total_amount,
                'status': stmt.excluded.status,
                'extra_data': stmt.excluded.extra_data,
                'updated_at': datetime.utcnow()
            }
        )

        await self.db.execute(stmt)
        logger.info(f"💾 Saved ventas: {nuevos} nuevos, {actualizados} actualizados")

        return nuevos, actualizados

    async def _save_resumen_mensual_ventas(
        self,
        company_id: UUID,
        period: str,
        tipo_doc: str,
        resumen_item: Dict
    ) -> tuple[int, int]:
        """
        Guarda o actualiza un documento de resumen mensual de ventas.

        Para documentos tipo RESUMEN (boletas 39, comprobantes 48), se crea
        un único documento mensual que se actualiza en cada sincronización.

        Args:
            company_id: ID de la empresa
            period: Período en formato YYYYMM
            tipo_doc: Tipo de documento (39, 48, etc.)
            resumen_item: Item del resumen con datos agregados

        Returns:
            Tuple (nuevos, actualizados)
        """
        # Generar folio único: PERIODO + TIPO (ej: 20251039)
        folio = int(f"{period}{tipo_doc}")

        logger.debug(f"💾 Saving monthly summary: folio={folio}, tipo={tipo_doc}, period={period}")

        # Buscar documento existente
        stmt = (
            select(SalesDocument)
            .where(SalesDocument.company_id == company_id)
            .where(SalesDocument.folio == folio)
        )
        result = await self.db.execute(stmt)
        existing_doc = result.scalar_one_or_none()

        # Preparar datos del resumen
        doc_data = {
            "company_id": company_id,
            "document_type": self._get_sales_document_type_name(tipo_doc),
            "folio": folio,
            "issue_date": self._parse_date(f"{period}01"),  # Primer día del mes
            "recipient_rut": None,
            "recipient_name": "RESUMEN MENSUAL",
            "net_amount": Decimal(str(resumen_item.get('rsmnMntNeto', 0))),
            "tax_amount": Decimal(str(resumen_item.get('rsmnMntIVA', 0))),
            "exempt_amount": Decimal(str(resumen_item.get('rsmnMntExento', 0))),
            "total_amount": Decimal(str(resumen_item.get('rsmnMntTotal', 0))),
            "status": "pending",
            "extra_data": {
                "is_monthly_summary": True,
                "period": period,
                "tipo_doc": tipo_doc,
                "total_documents": resumen_item.get('rsmnTotDoc', 0),
                "resumen_completo": resumen_item
            }
        }

        if existing_doc:
            # Actualizar documento existente
            for key, value in doc_data.items():
                if key != "company_id":  # No actualizar company_id
                    setattr(existing_doc, key, value)

            logger.debug(f"♻️  Updated monthly summary: folio={folio}")
            return 0, 1
        else:
            # Crear nuevo documento
            sales_doc = SalesDocument(**doc_data)
            self.db.add(sales_doc)
            logger.debug(f"✨ Created monthly summary: folio={folio}")
            return 1, 0

    def _get_purchase_document_type_name(self, tipo_doc: str) -> str:
        """
        Mapea código de tipo de documento de COMPRA a nombre descriptivo

        Args:
            tipo_doc: Código del tipo de documento

        Returns:
            Nombre del tipo de documento de compra
        """
        tipo_map = {
            "33": "factura_compra",
            "34": "factura_exenta_compra",
            "43": "liquidacion_factura",
            "46": "factura_compra",  # Factura de compra electrónica
            "56": "nota_debito_compra",
            "61": "nota_credito_compra"
        }
        return tipo_map.get(tipo_doc, "factura_compra")  # Default a factura_compra

    def _get_sales_document_type_name(self, tipo_doc: str) -> str:
        """
        Mapea código de tipo de documento de VENTA a nombre descriptivo

        Args:
            tipo_doc: Código del tipo de documento

        Returns:
            Nombre del tipo de documento de venta
        """
        tipo_map = {
            "33": "factura_venta",
            "34": "factura_exenta",
            "39": "boleta",
            "41": "boleta_exenta",
            "43": "liquidacion_factura",
            "48": "comprobante_pago",
            "56": "nota_debito_venta",
            "61": "nota_credito_venta"
        }
        return tipo_map.get(tipo_doc, "factura_venta")  # Default a factura_venta

    def _parse_purchase_document(self, company_id: UUID, doc: Dict, tipo_doc: str) -> Dict:
        """
        Parsea documento de compra del formato SII al formato DB

        Args:
            company_id: ID de la empresa
            doc: Documento raw del SII
            tipo_doc: Tipo de documento SII (33, 56, 61, etc.) - viene del parámetro de extracción
        """
        # Obtener RUT y convertir a string si es necesario
        sender_rut = doc.get('detRutDoc')
        if sender_rut is not None:
            sender_rut = str(sender_rut)

        # Usar el tipo_doc del parámetro (ya que detTpoDoc viene null del SII)
        # Fallback a detTpoDoc solo si existe (para compatibilidad futura)
        tipo_doc_sii = str(doc.get('detTpoDoc') or tipo_doc)
        document_type = self._get_purchase_document_type_name(tipo_doc_sii)

        return {
            "company_id": company_id,
            "document_type": document_type,
            "folio": int(doc.get('detNroDoc') or doc.get('folio', 0)),
            "issue_date": self._parse_date(doc.get('detFchDoc') or doc.get('fecha')),
            "sender_rut": sender_rut,
            "sender_name": doc.get('detRznSoc'),
            "net_amount": Decimal(str(doc.get('detMntNeto', 0))),
            "tax_amount": Decimal(str(doc.get('detMntIVA', 0))),
            "exempt_amount": Decimal(str(doc.get('detMntExento', 0))),
            "total_amount": Decimal(str(doc.get('detMntTotal', 0))),
            "status": "pending",
            "extra_data": doc  # Guardar datos completos
        }

    def _parse_sales_document(self, company_id: UUID, doc: Dict, tipo_doc: str) -> Dict:
        """
        Parsea documento de venta del formato SII al formato DB

        Args:
            company_id: ID de la empresa
            doc: Documento raw del SII
            tipo_doc: Tipo de documento SII (33, 39, 56, 61, etc.) - viene del parámetro de extracción
        """
        # Obtener RUT y convertir a string si es necesario
        recipient_rut = doc.get('detRutDoc')
        if recipient_rut is not None:
            recipient_rut = str(recipient_rut)

        # Usar el tipo_doc del parámetro (ya que detTpoDoc viene null del SII)
        # Fallback a detTpoDoc solo si existe (para compatibilidad futura)
        tipo_doc_sii = str(doc.get('detTpoDoc') or tipo_doc)
        document_type = self._get_sales_document_type_name(tipo_doc_sii)

        return {
            "company_id": company_id,
            "document_type": document_type,
            "folio": int(doc.get('detNroDoc') or doc.get('folio', 0)),
            "issue_date": self._parse_date(doc.get('detFchDoc') or doc.get('fecha')),
            "recipient_rut": recipient_rut,
            "recipient_name": doc.get('detRznSoc'),
            "net_amount": Decimal(str(doc.get('detMntNeto', 0))),
            "tax_amount": Decimal(str(doc.get('detMntIVA', 0))),
            "exempt_amount": Decimal(str(doc.get('detMntExento', 0))),
            "total_amount": Decimal(str(doc.get('detMntTotal', 0))),
            "status": "pending",
            "extra_data": doc  # Guardar datos completos
        }

    def _parse_date(self, date_str: Optional[str]) -> datetime.date:
        """
        Parsea fecha del SII a datetime.date

        Formatos soportados:
        - DD/MM/YYYY
        - YYYY-MM-DD
        - YYYYMMDD (para períodos)

        Raises:
            ValueError: Si la fecha no puede ser parseada
        """
        if not date_str:
            raise ValueError("Fecha no puede ser None o vacía")

        date_str = date_str.strip()

        try:
            # Intentar formato DD/MM/YYYY
            if '/' in date_str:
                return datetime.strptime(date_str, "%d/%m/%Y").date()
            # Intentar formato YYYY-MM-DD
            elif '-' in date_str:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            # Intentar formato YYYYMMDD (para períodos como "20251001")
            elif len(date_str) == 8 and date_str.isdigit():
                return datetime.strptime(date_str, "%Y%m%d").date()
            else:
                raise ValueError(f"Formato de fecha no reconocido: {date_str}")
        except ValueError as e:
            logger.error(f"❌ Error parsing date '{date_str}': {e}")
            raise ValueError(f"No se pudo parsear la fecha '{date_str}': {str(e)}")


# Dependency injection para FastAPI
async def get_sii_sync_service(db: AsyncSession) -> SIISyncService:
    """Factory para crear instancia de SIISyncService"""
    return SIISyncService(db)

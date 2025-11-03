"""
Módulo de sincronización de documentos de compra

Maneja la extracción y persistencia de documentos de compra desde el SII.
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.sii.service import SIIService
from .parsers import (
    parse_purchase_document,
    parse_daily_purchase_document,
    parse_monthly_summary,
    get_purchase_document_type_name
)
from .persistence import (
    get_or_create_contact,
    bulk_upsert_purchases,
    upsert_monthly_summary_purchase
)

logger = logging.getLogger(__name__)


async def sync_compras_period(
    db: AsyncSession,
    sii_service: SIIService,
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
    resumen_result = await sii_service.extract_resumen(
        session_id=session_id,
        periodo=period
    )

    # Validar que tenemos el resumen
    if not resumen_result.get("data") or not resumen_result["data"].get("resumen_compras"):
        logger.warning(f"⚠️ No resumen_compras data for period {period}")
        return {"total": 0, "nuevos": 0, "actualizados": 0}

    resumen_compras = resumen_result["data"]["resumen_compras"]

    # Paso 2: Procesar cada item del resumen
    resumen_items = resumen_compras.get("data") if isinstance(resumen_compras, dict) else None
    if not resumen_items:
        logger.warning(f"⚠️ No data items in resumen_compras for period {period}. Structure: {list(resumen_compras.keys()) if isinstance(resumen_compras, dict) else type(resumen_compras)}")
        resumen_items = []

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

            # Para boletas (39) y comprobantes (48), extraer detalle diario
            # IMPORTANTE: Solo guardamos el detalle diario, NO el resumen mensual
            # para evitar duplicación de montos en tax_summary
            if es_resumen and tipo_doc in ["39", "48"]:
                logger.info(f"  🔄 Tipo {tipo_doc} ({nombre_tipo}): Procesando SOLO detalle diario, OMITIENDO resumen mensual")
                nuevos, actualizados = await _sync_daily_purchases(
                    db, sii_service, session_id, company_id, period, tipo_doc
                )
                total_docs += nuevos + actualizados
                total_nuevos += nuevos
                total_actualizados += actualizados
                logger.info(f"  ✅ Tipo {tipo_doc}: {nuevos} nuevos, {actualizados} actualizados (detalle diario solamente)")
                # NO procesar resumen mensual para estos tipos (continuar al siguiente item)
                continue

            elif es_resumen:
                # Otros tipos de resumen mensual (sin detalle diario disponible)
                nuevos, actualizados = await _save_monthly_summary_compras(
                    db, company_id, period, tipo_doc, item
                )
                total_docs += 1
                total_nuevos += nuevos
                total_actualizados += actualizados

            else:
                # Tiene detalle individual - extraer cada documento
                nuevos, actualizados = await _sync_individual_purchases(
                    db, sii_service, session_id, company_id, period, tipo_doc
                )
                total_docs += nuevos + actualizados
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


async def _sync_daily_purchases(
    db: AsyncSession,
    sii_service: SIIService,
    session_id: UUID,
    company_id: UUID,
    period: str,
    tipo_doc: str
) -> Tuple[int, int]:
    """Sincroniza boletas/comprobantes diarios de compra"""
    logger.info(f"  📅 Tipo {tipo_doc} es RESUMEN - extrayendo totales diarios")

    try:
        result = await sii_service.extract_boletas_diarias(
            session_id=session_id,
            periodo=period,
            tipo_doc=tipo_doc
        )

        # Validar que tenemos datos
        if not result.get("data"):
            logger.info(f"  ℹ️ No daily data found for tipo {tipo_doc}")
            return 0, 0

        daily_documents = result["data"]
        logger.info(f"  ✅ Extracted {len(daily_documents)} daily totals for tipo {tipo_doc}")

        # Preparar datos de todos los documentos diarios
        docs_to_upsert = []
        for daily_doc in daily_documents:
            try:
                doc_data = parse_daily_purchase_document(
                    company_id=company_id,
                    period=period,
                    tipo_doc=tipo_doc,
                    daily_doc=daily_doc
                )
                docs_to_upsert.append(doc_data)
            except Exception as e:
                logger.error(f"❌ Error parsing daily doc {daily_doc}: {e}")
                continue

        if not docs_to_upsert:
            logger.warning("⚠️ No valid daily documents to save")
            return 0, 0

        # Guardar en DB
        nuevos, actualizados = await bulk_upsert_purchases(db, company_id, docs_to_upsert)
        logger.info(f"💾 Saved daily compras: {nuevos} nuevos, {actualizados} actualizados")
        return nuevos, actualizados

    except Exception as e:
        logger.error(f"❌ Error extracting daily data for tipo {tipo_doc}: {e}")
        raise


async def _sync_individual_purchases(
    db: AsyncSession,
    sii_service: SIIService,
    session_id: UUID,
    company_id: UUID,
    period: str,
    tipo_doc: str
) -> Tuple[int, int]:
    """Sincroniza documentos individuales de compra"""
    logger.info(f"  📤 Tipo {tipo_doc} tiene detalle - extrayendo documentos individuales")

    result = await sii_service.extract_compras(
        session_id=session_id,
        periodo=period,
        tipo_doc=tipo_doc
    )

    # Validar que tenemos datos
    if not result.get("data"):
        logger.info(f"  ℹ️ No documents found for tipo {tipo_doc}")
        return 0, 0

    documents = result["data"]
    logger.info(f"  ✅ Extracted {len(documents)} documents tipo {tipo_doc}")

    # Preparar datos de todos los documentos
    docs_to_upsert = []
    for doc in documents:
        try:
            folio = doc.get('detNroDoc') or doc.get('folio')
            if not folio:
                logger.warning(f"⚠️ Skipping purchase doc without folio: {doc}")
                continue

            doc_data = parse_purchase_document(
                company_id=company_id,
                doc=doc,
                tipo_doc=tipo_doc
            )

            # Crear o buscar contacto (proveedor) si hay RUT y nombre
            sender_rut = doc_data.get('sender_rut')
            sender_name = doc_data.get('sender_name')
            if sender_rut and sender_name:
                contact_id = await get_or_create_contact(
                    db=db,
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

    # Guardar en DB
    nuevos, actualizados = await bulk_upsert_purchases(db, company_id, docs_to_upsert)
    logger.info(f"💾 Saved compras: {nuevos} nuevos, {actualizados} actualizados")
    return nuevos, actualizados


async def _save_monthly_summary_compras(
    db: AsyncSession,
    company_id: UUID,
    period: str,
    tipo_doc: str,
    resumen_item: Dict
) -> Tuple[int, int]:
    """Guarda o actualiza un documento de resumen mensual de compras"""
    logger.info(f"  📊 Tipo {tipo_doc} es RESUMEN mensual - creando documento agregado")

    doc_data = parse_monthly_summary(
        company_id=company_id,
        period=period,
        tipo_doc=tipo_doc,
        resumen_item=resumen_item,
        document_type_mapper=get_purchase_document_type_name
    )

    # Agregar campos específicos de compras
    doc_data["sender_rut"] = None
    doc_data["sender_name"] = "RESUMEN MENSUAL"

    return await upsert_monthly_summary_purchase(db, doc_data)

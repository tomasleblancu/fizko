"""
Módulo de sincronización de boletas de honorarios

Maneja la extracción y persistencia de boletas de honorarios desde el SII.
"""
import logging
from datetime import datetime
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.sii.service import SIIService
from .parsers import parse_honorarios_receipt
from .persistence import bulk_upsert_honorarios

logger = logging.getLogger(__name__)


async def sync_honorarios_period(
    db: AsyncSession,
    sii_service: SIIService,
    session_id: UUID,
    company_id: UUID,
    period: str
) -> Dict[str, int]:
    """
    Sincroniza boletas de honorarios de un período específico

    Args:
        db: Sesión de base de datos async
        sii_service: Servicio SII para extraer datos
        session_id: ID de sesión con credenciales SII
        company_id: ID de la compañía
        period: Período en formato YYYYMM

    Returns:
        {"total": int, "nuevos": int, "actualizados": int}
    """
    logger.info(f"💼 Extracting boletas de honorarios for period {period}")

    # Extraer mes y año del período
    year = period[:4]
    month = period[4:6].lstrip('0')  # Remover cero a la izquierda

    # Paso 1: Obtener boletas de honorarios del período
    try:
        boletas_result = await sii_service.extract_boletas_honorarios(
            session_id=session_id,
            mes=month,
            anio=year
        )
    except Exception as e:
        logger.error(f"❌ Error extracting boletas de honorarios for period {period}: {e}", exc_info=True)
        return {"total": 0, "nuevos": 0, "actualizados": 0}

    # Validar que tenemos datos
    if not boletas_result.get("data"):
        logger.warning(f"⚠️ No boletas de honorarios data for period {period}")
        return {"total": 0, "nuevos": 0, "actualizados": 0}

    data = boletas_result["data"]
    boletas_list = data.get("boletas", [])

    if not boletas_list:
        logger.info(f"✅ No boletas de honorarios found for period {period}")
        return {"total": 0, "nuevos": 0, "actualizados": 0}

    logger.info(f"  📋 Found {len(boletas_list)} boletas de honorarios")

    # Paso 2: Parsear boletas
    parsed_boletas = []
    for boleta_raw in boletas_list:
        try:
            boleta_parsed = parse_honorarios_receipt(
                boleta_raw,
                company_id=company_id,
                period=period
            )
            parsed_boletas.append(boleta_parsed)
        except Exception as e:
            logger.error(
                f"❌ Error parsing boleta {boleta_raw.get('numero_boleta', 'unknown')}: {e}",
                exc_info=True
            )
            continue

    if not parsed_boletas:
        logger.warning(f"⚠️ No valid boletas parsed for period {period}")
        return {"total": 0, "nuevos": 0, "actualizados": 0}

    # Paso 3: Guardar en base de datos (bulk upsert)
    logger.info(f"💾 Saving {len(parsed_boletas)} boletas to database")

    try:
        result = await bulk_upsert_honorarios(
            db=db,
            honorarios_list=parsed_boletas,
            company_id=company_id
        )

        logger.info(
            f"✅ Boletas honorarios sync complete for {period}: "
            f"{result['nuevos']} nuevos, {result['actualizados']} actualizados"
        )

        return {
            "total": len(parsed_boletas),
            "nuevos": result["nuevos"],
            "actualizados": result["actualizados"]
        }

    except Exception as e:
        logger.error(f"❌ Error saving boletas de honorarios: {e}", exc_info=True)
        raise

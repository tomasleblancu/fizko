"""
Router para sincronización de documentos tributarios (compras/ventas)

Proporciona endpoints para sincronizar documentos de compra y venta desde el SII.
"""
import logging
from uuid import UUID
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...config.database import get_db
from ...db.models import Session as SessionModel, Profile
from ...dependencies import get_current_user_id, require_auth
from ...services.sii.sync_service import SIISyncService

# Import the validate_session_access function from sync_f29
from .sync_f29 import validate_session_access

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["sii-sync-documents"],
    dependencies=[Depends(require_auth)]
)


class SyncRequest(BaseModel):
    """Request para iniciar sincronización de documentos"""
    session_id: UUID = Field(..., description="ID de sesión SII activa")
    months: int = Field(
        default=3,
        ge=1,
        le=12,
        description="Cantidad de meses a sincronizar (1-12)"
    )


class SyncRecentRequest(BaseModel):
    """Request para sincronizar documentos recientes (últimos días)"""
    session_id: UUID = Field(..., description="ID de sesión SII activa")
    days: int = Field(
        default=7,
        ge=1,
        le=7,
        description="Cantidad de días a sincronizar (1-7)"
    )


class SyncResponse(BaseModel):
    """Respuesta de sincronización completada"""
    status: str = Field(..., description="Estado: 'completed' o 'error'")
    message: str = Field(..., description="Mensaje descriptivo")
    session_id: str = Field(..., description="ID de sesión SII")
    months: int = Field(..., description="Meses sincronizados")
    compras: Dict[str, int] = Field(..., description="Estadísticas de compras")
    ventas: Dict[str, int] = Field(..., description="Estadísticas de ventas")
    duration_seconds: float = Field(..., description="Duración en segundos")
    errors: int = Field(..., description="Número de errores")


@router.post("", response_model=SyncResponse)
async def sync_documents(
    request: SyncRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Sincroniza documentos tributarios de forma síncrona

    Esta sincronización extrae documentos de compra y venta de los últimos
    N meses desde el SII y los almacena en la base de datos.

    El proceso es síncrono, por lo que la respuesta se devuelve cuando
    la sincronización ha finalizado completamente.

    Args:
        request: Parámetros de sincronización (session_id, months)
        current_user_id: ID del usuario autenticado
        db: Sesión de base de datos

    Returns:
        SyncResponse con resultado de la sincronización

    Example:
        ```json
        POST /api/sii/sync/documents
        {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "months": 3
        }
        ```

        Response:
        ```json
        {
            "status": "completed",
            "message": "Sincronización completada exitosamente",
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "months": 3,
            "compras": {"total": 10, "nuevos": 8, "actualizados": 2},
            "ventas": {"total": 15, "nuevos": 12, "actualizados": 3},
            "duration_seconds": 12.5,
            "errors": 0
        }
        ```
    """
    logger.info(
        f"🔄 Document sync requested by user {current_user_id}: "
        f"session={request.session_id}, months={request.months}"
    )

    # Validar que el usuario tenga acceso a usar la sesión
    session = await validate_session_access(request.session_id, current_user_id, db)

    try:
        # Ejecutar sincronización de forma síncrona
        sync_service = SIISyncService(db)
        result = await sync_service.sync_last_n_months(
            session_id=request.session_id,
            months=request.months
        )

        # Commit de cambios
        await db.commit()

        return SyncResponse(
            status="completed",
            message=f"Sincronización de {request.months} meses completada exitosamente",
            session_id=str(request.session_id),
            months=request.months,
            compras=result["compras"],
            ventas=result["ventas"],
            duration_seconds=result["duration_seconds"],
            errors=len(result.get("errors", []))
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Document sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en sincronización: {str(e)}"
        )


@router.post("/recent", response_model=SyncResponse)
async def sync_recent_documents(
    request: SyncRecentRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Sincroniza documentos tributarios de los últimos N días (máximo 7 días)

    Este endpoint es ideal para mantener actualizados los datos sin tener que
    sincronizar meses completos. Sincroniza compras y ventas de los últimos días.

    Args:
        request: Parámetros de sincronización (session_id, days)
        current_user_id: ID del usuario autenticado
        db: Sesión de base de datos

    Returns:
        SyncResponse con resultado de la sincronización

    Example:
        ```json
        POST /api/sii/sync/documents/recent
        {
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "days": 7
        }
        ```

        Response:
        ```json
        {
            "status": "completed",
            "message": "Sincronización de últimos 7 días completada",
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "months": 0,
            "compras": {"total": 5, "nuevos": 4, "actualizados": 1},
            "ventas": {"total": 8, "nuevos": 7, "actualizados": 1},
            "duration_seconds": 3.2,
            "errors": 0
        }
        ```
    """
    from datetime import datetime, timedelta
    import time

    logger.info(
        f"🔄 Recent documents sync requested by user {current_user_id}: "
        f"session={request.session_id}, days={request.days}"
    )

    # Validar que el usuario tenga acceso a usar la sesión
    session = await validate_session_access(request.session_id, current_user_id, db)

    try:
        start_time = time.time()

        # Calcular el rango de fechas (últimos N días)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=request.days - 1)  # -1 para incluir hoy

        logger.info(f"📅 Syncing documents from {start_date} to {end_date}")

        # Crear el servicio de sincronización
        sync_service = SIISyncService(db)

        # Determinar el período (año y mes) a sincronizar
        # Para simplificar, sincronizamos el mes actual y el anterior si los días cruzan meses
        periods_to_sync = []
        current_period = (end_date.year, end_date.month)
        periods_to_sync.append(current_period)

        # Si los días cruzan al mes anterior, agregarlo también
        if start_date.month != end_date.month or start_date.year != end_date.year:
            previous_period = (start_date.year, start_date.month)
            if previous_period not in periods_to_sync:
                periods_to_sync.insert(0, previous_period)

        logger.info(f"📊 Will sync periods: {periods_to_sync}")

        # Sincronizar compras y ventas para cada período
        total_compras = {"total": 0, "nuevos": 0, "actualizados": 0}
        total_ventas = {"total": 0, "nuevos": 0, "actualizados": 0}
        total_errors = 0

        for year, month in periods_to_sync:
            try:
                # Sincronizar compras
                logger.info(f"📥 Syncing purchases for {year}-{month:02d}")
                compras_result = await sync_service._sync_compras_period(
                    session_id=request.session_id,
                    company_id=session.company_id,
                    year=year,
                    month=month
                )

                # Filtrar solo documentos dentro del rango de días
                # (Los métodos _sync_compras_period sincronizan el mes completo)
                total_compras["total"] += compras_result.get("total", 0)
                total_compras["nuevos"] += compras_result.get("nuevos", 0)
                total_compras["actualizados"] += compras_result.get("actualizados", 0)

                # Sincronizar ventas
                logger.info(f"📤 Syncing sales for {year}-{month:02d}")
                ventas_result = await sync_service._sync_ventas_period(
                    session_id=request.session_id,
                    company_id=session.company_id,
                    year=year,
                    month=month
                )

                total_ventas["total"] += ventas_result.get("total", 0)
                total_ventas["nuevos"] += ventas_result.get("nuevos", 0)
                total_ventas["actualizados"] += ventas_result.get("actualizados", 0)

            except Exception as e:
                logger.error(f"❌ Error syncing period {year}-{month:02d}: {e}")
                total_errors += 1

        # Commit de todos los cambios
        await db.commit()

        duration = time.time() - start_time

        logger.info(
            f"✅ Recent documents sync completed in {duration:.2f}s: "
            f"compras={total_compras['total']}, ventas={total_ventas['total']}, errors={total_errors}"
        )

        return SyncResponse(
            status="completed",
            message=f"Sincronización de últimos {request.days} días completada exitosamente",
            session_id=str(request.session_id),
            months=0,  # No sincronizamos meses completos
            compras=total_compras,
            ventas=total_ventas,
            duration_seconds=round(duration, 2),
            errors=total_errors
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Recent documents sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en sincronización de documentos recientes: {str(e)}"
        )

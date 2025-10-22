"""
Router para sincronización de documentos SII

Proporciona endpoints para sincronizar documentos tributarios desde el SII.
"""
import logging
from uuid import UUID
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from ...config.database import get_db
from ...db.models import Session as SessionModel
from ...dependencies import get_current_user_id, require_auth
from ...services.sii.sync_service import SIISyncService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sync",
    tags=["sii-sync"],
    dependencies=[Depends(require_auth)]
)


class SyncRequest(BaseModel):
    """Request para iniciar sincronización"""
    session_id: UUID = Field(..., description="ID de sesión SII activa")
    months: int = Field(
        default=3,
        ge=1,
        le=12,
        description="Cantidad de meses a sincronizar (1-12)"
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


@router.post("/documents", response_model=SyncResponse)
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
        f"🔄 Sync requested by user {current_user_id}: "
        f"session={request.session_id}, months={request.months}"
    )

    # Validar que la sesión pertenece al usuario actual y está activa
    stmt = select(SessionModel).where(SessionModel.id == request.session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        logger.warning(f"⚠️ Session {request.session_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sesión {request.session_id} no encontrada"
        )

    # Convertir current_user_id a UUID si es string
    if isinstance(current_user_id, str):
        from uuid import UUID as UUIDType
        current_user_id = UUIDType(current_user_id)

    if session.user_id != current_user_id:
        logger.warning(
            f"⚠️ User {current_user_id} attempted to sync session {request.session_id} "
            f"belonging to user {session.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para sincronizar esta sesión"
        )

    if not session.is_active:
        logger.warning(f"⚠️ Session {request.session_id} is not active")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La sesión no está activa. Por favor, vuelve a autenticarte con el SII."
        )

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
        logger.error(f"❌ Sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en sincronización: {str(e)}"
        )


# Endpoint futuro para consultar estado de sincronización
# (requiere implementar tracking de jobs)
#
# @router.get("/status/{job_id}")
# async def get_sync_status(job_id: UUID):
#     """
#     Consulta el estado de una sincronización en progreso
#     """
#     # Implementar cuando tengamos job tracking
#     pass

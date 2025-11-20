"""REST API endpoints for user-specific operations."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/user",
    tags=["user"],
    dependencies=[Depends(require_auth)]
)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class UserNotificationPreferencesResponse(BaseModel):
    notifications_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    quiet_days: Optional[List[str]]
    muted_categories: Optional[List[str]]
    muted_templates: List[str]
    max_notifications_per_day: int
    min_interval_minutes: int


class UpdateUserNotificationPreferencesRequest(BaseModel):
    company_id: UUID
    notifications_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    quiet_days: Optional[List[str]] = None
    muted_categories: Optional[List[str]] = None
    muted_templates: Optional[List[str]] = None
    max_notifications_per_day: Optional[int] = None
    min_interval_minutes: Optional[int] = None


# ============================================================================
# USER NOTIFICATION PREFERENCES
# ============================================================================

@router.get("/notification-preferences")
async def get_user_notification_preferences(
    company_id: UUID = Query(..., description="ID de la empresa"),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Obtiene las preferencias de notificaciones del usuario para una empresa específica.

    - **company_id**: ID de la empresa (requerido en query params)

    Retorna las preferencias del usuario o valores por defecto si no existen.
    """
    from app.services.notifications import get_notification_service

    notification_service = get_notification_service()
    preferences = await notification_service.get_user_preferences(
        db=db,
        user_id=user_id,
        company_id=company_id
    )

    return {
        "data": preferences
    }


@router.put("/notification-preferences")
async def update_user_notification_preferences(
    request: UpdateUserNotificationPreferencesRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Actualiza las preferencias de notificaciones del usuario.

    Solo actualiza los campos proporcionados, mantiene el resto sin cambios.

    - **company_id**: ID de la empresa (requerido)
    - **notifications_enabled**: Activar/desactivar todas las notificaciones
    - **muted_templates**: Lista de IDs de templates silenciados
    - **quiet_hours_start**: Hora de inicio de silencio (HH:MM)
    - **quiet_hours_end**: Hora de fin de silencio (HH:MM)
    - **quiet_days**: Días silenciados (ej: ["saturday", "sunday"])
    - **muted_categories**: Categorías silenciadas (ej: ["system"])
    - **max_notifications_per_day**: Máximo de notificaciones por día
    - **min_interval_minutes**: Intervalo mínimo entre notificaciones
    """
    from app.services.notifications import get_notification_service

    notification_service = get_notification_service()

    try:
        await notification_service.update_user_preferences(
            db=db,
            user_id=user_id,
            company_id=request.company_id,
            notifications_enabled=request.notifications_enabled,
            quiet_hours_start=request.quiet_hours_start,
            quiet_hours_end=request.quiet_hours_end,
            quiet_days=request.quiet_days,
            muted_categories=request.muted_categories,
            muted_templates=request.muted_templates,
            max_notifications_per_day=request.max_notifications_per_day,
            min_interval_minutes=request.min_interval_minutes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "message": "Preferencias actualizadas exitosamente"
    }

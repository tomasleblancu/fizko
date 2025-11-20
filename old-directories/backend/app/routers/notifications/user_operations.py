"""User-facing notification operations (scheduling, history, preferences)."""

import os
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id, get_user_company_id
from ...services.notifications import NotificationService
from ...services.whatsapp.service import WhatsAppService

router = APIRouter()

# Inicializar servicios
KAPSO_API_TOKEN = os.getenv("KAPSO_API_TOKEN", "")
KAPSO_API_BASE_URL = os.getenv("KAPSO_API_BASE_URL", "https://app.kapso.ai/api/v1")

whatsapp_service = WhatsAppService(
    api_token=KAPSO_API_TOKEN,
    base_url=KAPSO_API_BASE_URL,
)

notification_service = NotificationService(whatsapp_service=whatsapp_service)


# ========== Request/Response Models ==========

class ScheduleNotificationRequest(BaseModel):
    template_code: str = Field(..., description="Código del template a usar")
    recipients: List[dict] = Field(
        ...,
        description='Lista de destinatarios: [{"user_id": "uuid", "phone": "+56..."}]',
    )
    message_context: dict = Field(
        ..., description="Contexto para renderizar variables del mensaje"
    )
    entity_type: Optional[str] = Field(None, description="Tipo de entidad relacionada")
    entity_id: Optional[str] = Field(None, description="ID de la entidad")
    reference_date: Optional[datetime] = Field(
        None, description="Fecha de referencia para calcular timing"
    )
    custom_timing: Optional[dict] = Field(None, description="Timing personalizado")


class ScheduledNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    notification_template_id: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    recipients: dict
    message_content: str
    scheduled_for: datetime
    status: str
    created_at: datetime


class NotificationHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    notification_template_id: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    user_id: Optional[str]
    phone_number: str
    message_content: str
    status: str
    sent_at: datetime
    whatsapp_message_id: Optional[str]


class ProcessStatsResponse(BaseModel):
    processed: int
    sent: int
    failed: int
    skipped: int


class UserPreferencesRequest(BaseModel):
    notifications_enabled: bool = True
    quiet_hours_start: Optional[str] = Field(
        None, description="Hora de inicio de silencio (HH:MM)"
    )
    quiet_hours_end: Optional[str] = Field(None, description="Hora de fin de silencio (HH:MM)")
    quiet_days: Optional[List[str]] = Field(None, description='Días silenciados: ["saturday", "sunday"]')
    muted_categories: Optional[List[str]] = Field(
        None, description='Categorías silenciadas: ["system"]'
    )
    muted_templates: Optional[List[str]] = Field(
        None, description='Templates silenciados: ["template_id_1", "template_id_2"]'
    )
    max_notifications_per_day: int = 20
    min_interval_minutes: int = 30


# ========== Scheduling Endpoints ==========

@router.post("/schedule", response_model=ScheduledNotificationResponse)
async def schedule_notification(
    request: ScheduleNotificationRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_user_company_id),
):
    """
    Programa una notificación para envío futuro.

    Scoped to current user's company.

    Ejemplo de uso:
    ```json
    {
        "template_code": "calendar_event_reminder_1d",
        "recipients": [
            {"user_id": "uuid-here", "phone": "+56912345678"}
        ],
        "message_context": {
            "event_title": "Declaración F29 - Octubre 2025",
            "due_date": "12 de Noviembre",
            "description": "Presentación mensual de IVA"
        },
        "entity_type": "calendar_event",
        "entity_id": "event-uuid-here",
        "reference_date": "2025-11-12T23:59:59Z"
    }
    ```
    """
    # Obtener template por código
    template = await notification_service.get_template(db=db, code=request.template_code)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{request.template_code}' no encontrado")

    # Programar notificación
    scheduled = await notification_service.schedule_notification(
        db=db,
        company_id=company_id,
        template_id=template.id,
        recipients=request.recipients,
        message_context=request.message_context,
        entity_type=request.entity_type,
        entity_id=UUID(request.entity_id) if request.entity_id else None,
        reference_date=request.reference_date,
        custom_timing=request.custom_timing,
    )

    return ScheduledNotificationResponse(
        id=str(scheduled.id),
        company_id=str(scheduled.company_id),
        notification_template_id=str(scheduled.notification_template_id),
        entity_type=scheduled.entity_type,
        entity_id=str(scheduled.entity_id) if scheduled.entity_id else None,
        recipients=scheduled.recipients,
        message_content=scheduled.message_content,
        scheduled_for=scheduled.scheduled_for,
        status=scheduled.status,
        created_at=scheduled.created_at,
    )


@router.post("/process", response_model=ProcessStatsResponse)
async def process_pending_notifications_now(
    batch_size: int = 50,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Procesa manualmente notificaciones pendientes.

    Este endpoint es útil para testing o para ejecutar el procesamiento
    de forma manual antes de configurar Celery.

    Requiere permisos de administrador (TODO: agregar validación de rol).
    """
    # TODO: Validar que el usuario sea admin

    stats = await notification_service.process_pending_notifications(
        db=db,
        batch_size=batch_size,
    )

    return ProcessStatsResponse(**stats)


# ========== History Endpoints ==========

@router.get("/history", response_model=List[NotificationHistoryResponse])
async def get_notification_history(
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_user_company_id),
):
    """
    Obtiene el historial de notificaciones enviadas.

    Scoped to current user's company.

    Filtros opcionales:
    - entity_type: 'calendar_event', 'form29', etc.
    - entity_id: UUID de la entidad específica
    - status: 'sent', 'failed', 'delivered', 'read'
    - limit: Máximo de resultados (default: 100)
    """
    history = await notification_service.get_notification_history(
        db=db,
        company_id=company_id,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        limit=limit,
    )

    return [
        NotificationHistoryResponse(
            id=str(h.id),
            company_id=str(h.company_id),
            notification_template_id=str(h.notification_template_id) if h.notification_template_id else None,
            entity_type=h.entity_type,
            entity_id=str(h.entity_id) if h.entity_id else None,
            user_id=str(h.user_id) if h.user_id else None,
            phone_number=h.phone_number,
            message_content=h.message_content,
            status=h.status,
            sent_at=h.sent_at,
            whatsapp_message_id=h.whatsapp_message_id,
        )
        for h in history
    ]


# ========== User Preferences Endpoints ==========

@router.get("/preferences")
async def get_user_notification_preferences(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_user_company_id),
):
    """
    Obtiene las preferencias de notificaciones del usuario actual.

    Delega a NotificationService.
    """
    return await notification_service.get_user_preferences(
        db=db,
        user_id=user_id,
        company_id=company_id
    )


@router.put("/preferences")
async def update_user_notification_preferences(
    request: UserPreferencesRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_user_company_id),
):
    """
    Actualiza las preferencias de notificaciones del usuario actual.

    Delega a NotificationService.
    """
    await notification_service.update_user_preferences(
        db=db,
        user_id=user_id,
        company_id=company_id,
        notifications_enabled=request.notifications_enabled,
        quiet_hours_start=request.quiet_hours_start,
        quiet_hours_end=request.quiet_hours_end,
        quiet_days=request.quiet_days,
        muted_categories=request.muted_categories,
        muted_templates=request.muted_templates,
        max_notifications_per_day=request.max_notifications_per_day,
        min_interval_minutes=request.min_interval_minutes,
    )

    return {"message": "Preferencias actualizadas exitosamente"}

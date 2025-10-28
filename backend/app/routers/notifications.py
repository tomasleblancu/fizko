"""
API endpoints para gestión de notificaciones por WhatsApp
"""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.dependencies import get_current_user_id, get_user_company_id
from app.services.notifications import NotificationService
from app.services.whatsapp.service import WhatsAppService
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Inicializar servicios
KAPSO_API_TOKEN = os.getenv("KAPSO_API_TOKEN", "")
KAPSO_API_BASE_URL = os.getenv("KAPSO_API_BASE_URL", "https://app.kapso.ai/api/v1")

whatsapp_service = WhatsAppService(
    api_token=KAPSO_API_TOKEN,
    base_url=KAPSO_API_BASE_URL,
)

notification_service = NotificationService(whatsapp_service=whatsapp_service)


# ========== Request/Response Models ==========

class NotificationTemplateResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str]
    category: str
    entity_type: Optional[str]
    message_template: str
    timing_config: dict
    priority: str
    is_active: bool

    class Config:
        from_attributes = True


class SubscriptionRequest(BaseModel):
    template_id: str
    custom_timing: Optional[dict] = None
    custom_message: Optional[str] = None
    is_enabled: bool = True


class SubscriptionResponse(BaseModel):
    id: str
    company_id: str
    notification_template_id: str
    is_enabled: bool
    custom_timing_config: Optional[dict]
    custom_message_template: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class NotificationHistoryResponse(BaseModel):
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

    class Config:
        from_attributes = True


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
    max_notifications_per_day: int = 20
    min_interval_minutes: int = 30


# ========== Templates Endpoints ==========

@router.get("/templates", response_model=List[NotificationTemplateResponse])
async def list_notification_templates(
    category: Optional[str] = None,
    entity_type: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Lista todos los templates de notificaciones disponibles.

    Filtros opcionales:
    - category: 'calendar', 'tax_document', 'payroll', 'system', 'custom'
    - entity_type: 'calendar_event', 'form29', etc.
    - is_active: true/false
    """
    templates = await notification_service.list_templates(
        db=db,
        category=category,
        entity_type=entity_type,
        is_active=is_active,
    )

    return [
        NotificationTemplateResponse(
            id=str(t.id),
            code=t.code,
            name=t.name,
            description=t.description,
            category=t.category,
            entity_type=t.entity_type,
            message_template=t.message_template,
            timing_config=t.timing_config,
            priority=t.priority,
            is_active=t.is_active,
        )
        for t in templates
    ]


@router.get("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def get_notification_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Obtiene detalles de un template específico."""
    template = await notification_service.get_template(db=db, template_id=template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    return NotificationTemplateResponse(
        id=str(template.id),
        code=template.code,
        name=template.name,
        description=template.description,
        category=template.category,
        entity_type=template.entity_type,
        message_template=template.message_template,
        timing_config=template.timing_config,
        priority=template.priority,
        is_active=template.is_active,
    )


# ========== Subscriptions Endpoints ==========

@router.get("/subscriptions", response_model=List[SubscriptionResponse])
async def list_company_subscriptions(
    is_enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_user_company_id),
):
    """Lista las suscripciones de notificaciones de la empresa actual."""
    subscriptions = await notification_service.get_company_subscriptions(
        db=db,
        company_id=company_id,
        is_enabled=is_enabled,
    )

    return [
        SubscriptionResponse(
            id=str(s.id),
            company_id=str(s.company_id),
            notification_template_id=str(s.notification_template_id),
            is_enabled=s.is_enabled,
            custom_timing_config=s.custom_timing_config,
            custom_message_template=s.custom_message_template,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in subscriptions
    ]


@router.post("/subscriptions", response_model=SubscriptionResponse)
async def subscribe_to_notification(
    request: SubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_user_company_id),
):
    """
    Suscribe la empresa a una notificación específica.

    Permite personalizar el timing y el mensaje.
    """
    subscription = await notification_service.subscribe_company(
        db=db,
        company_id=company_id,
        template_id=UUID(request.template_id),
        custom_timing=request.custom_timing,
        custom_message=request.custom_message,
        is_enabled=request.is_enabled,
    )

    return SubscriptionResponse(
        id=str(subscription.id),
        company_id=str(subscription.company_id),
        notification_template_id=str(subscription.notification_template_id),
        is_enabled=subscription.is_enabled,
        custom_timing_config=subscription.custom_timing_config,
        custom_message_template=subscription.custom_message_template,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )


@router.delete("/subscriptions/{template_id}")
async def unsubscribe_from_notification(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_user_company_id),
):
    """Desuscribe la empresa de una notificación."""
    success = await notification_service.unsubscribe_company(
        db=db,
        company_id=company_id,
        template_id=template_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")

    return {"message": "Desuscripción exitosa"}


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
    """Obtiene las preferencias de notificaciones del usuario actual."""
    from app.db.models import UserNotificationPreference
    from sqlalchemy import select, and_

    result = await db.execute(
        select(UserNotificationPreference).where(
            and_(
                UserNotificationPreference.user_id == user_id,
                UserNotificationPreference.company_id == company_id,
            )
        )
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        # Retornar valores por defecto
        return {
            "notifications_enabled": True,
            "quiet_hours_start": None,
            "quiet_hours_end": None,
            "quiet_days": None,
            "muted_categories": None,
            "max_notifications_per_day": 20,
            "min_interval_minutes": 30,
        }

    return {
        "notifications_enabled": prefs.notifications_enabled,
        "quiet_hours_start": str(prefs.quiet_hours_start) if prefs.quiet_hours_start else None,
        "quiet_hours_end": str(prefs.quiet_hours_end) if prefs.quiet_hours_end else None,
        "quiet_days": prefs.quiet_days,
        "muted_categories": prefs.muted_categories,
        "max_notifications_per_day": prefs.max_notifications_per_day,
        "min_interval_minutes": prefs.min_interval_minutes,
    }


@router.put("/preferences")
async def update_user_notification_preferences(
    request: UserPreferencesRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_user_company_id),
):
    """Actualiza las preferencias de notificaciones del usuario actual."""
    from app.db.models import UserNotificationPreference
    from sqlalchemy import select, and_
    from datetime import time as dt_time

    result = await db.execute(
        select(UserNotificationPreference).where(
            and_(
                UserNotificationPreference.user_id == user_id,
                UserNotificationPreference.company_id == company_id,
            )
        )
    )
    prefs = result.scalar_one_or_none()

    # Parsear horarios si se proporcionan
    quiet_start = None
    quiet_end = None
    if request.quiet_hours_start:
        hour, minute = map(int, request.quiet_hours_start.split(":"))
        quiet_start = dt_time(hour=hour, minute=minute)
    if request.quiet_hours_end:
        hour, minute = map(int, request.quiet_hours_end.split(":"))
        quiet_end = dt_time(hour=hour, minute=minute)

    if prefs:
        # Actualizar existente
        prefs.notifications_enabled = request.notifications_enabled
        prefs.quiet_hours_start = quiet_start
        prefs.quiet_hours_end = quiet_end
        prefs.quiet_days = request.quiet_days
        prefs.muted_categories = request.muted_categories
        prefs.max_notifications_per_day = request.max_notifications_per_day
        prefs.min_interval_minutes = request.min_interval_minutes
        prefs.updated_at = datetime.utcnow()
    else:
        # Crear nueva
        prefs = UserNotificationPreference(
            user_id=user_id,
            company_id=company_id,
            notifications_enabled=request.notifications_enabled,
            quiet_hours_start=quiet_start,
            quiet_hours_end=quiet_end,
            quiet_days=request.quiet_days,
            muted_categories=request.muted_categories,
            max_notifications_per_day=request.max_notifications_per_day,
            min_interval_minutes=request.min_interval_minutes,
        )
        db.add(prefs)

    await db.commit()
    await db.refresh(prefs)

    return {"message": "Preferencias actualizadas exitosamente"}

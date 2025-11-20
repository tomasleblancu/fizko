"""
Helpers y utilidades para facilitar el uso del sistema de notificaciones
Proporciona funciones simples para enviar notificaciones desde cualquier parte de la app
"""
import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.whatsapp.service import WhatsAppService
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)

# ========== SINGLETON PATTERN PARA SERVICIOS ==========

_whatsapp_service_instance: Optional[WhatsAppService] = None
_notification_service_instance: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """
    Obtiene instancia singleton del servicio de notificaciones.
    Lazy initialization para evitar problemas de import circular.

    Returns:
        NotificationService: Instancia del servicio
    """
    global _whatsapp_service_instance, _notification_service_instance

    if _notification_service_instance is None:
        # Crear servicio de WhatsApp si no existe
        if _whatsapp_service_instance is None:
            kapso_token = os.getenv("KAPSO_API_TOKEN", "")
            kapso_base_url = os.getenv(
                "KAPSO_API_BASE_URL", "https://app.kapso.ai/api/v1"
            )
            _whatsapp_service_instance = WhatsAppService(
                api_token=kapso_token,
                base_url=kapso_base_url,
            )

        # Crear servicio de notificaciones
        _notification_service_instance = NotificationService(
            whatsapp_service=_whatsapp_service_instance
        )

    return _notification_service_instance


# ========== FUNCIONES SIMPLES PARA USO RÁPIDO ==========


async def send_instant_notification(
    db: AsyncSession,
    company_id: UUID,
    phone_numbers: List[str],
    message: str,
    user_ids: Optional[List[UUID]] = None,
) -> Dict[str, Any]:
    """
    Envía una notificación instantánea (sin template).

    Uso:
        await send_instant_notification(
            db,
            company_id,
            ["+56912345678"],
            "¡Hola! Tu F29 fue procesado exitosamente."
        )

    Args:
        db: Sesión de base de datos
        company_id: ID de la empresa
        phone_numbers: Lista de teléfonos
        message: Mensaje a enviar
        user_ids: Lista opcional de user_ids (para tracking)

    Returns:
        Resultado con estadísticas de envío
    """
    service = get_notification_service()

    # Preparar destinatarios
    recipients = []
    for i, phone in enumerate(phone_numbers):
        recipient = {"phone": phone}
        if user_ids and i < len(user_ids):
            recipient["user_id"] = str(user_ids[i])
        recipients.append(recipient)

    # Programar con template de sistema (inmediato)
    template = await service.get_template(db, code="system_reminder")

    if not template:
        raise ValueError("Template 'system_reminder' no encontrado")

    scheduled = await service.schedule_notification(
        db=db,
        company_id=company_id,
        template_id=template.id,
        recipients=recipients,
        message_context={"message": message},
        custom_timing={"type": "immediate"},
    )

    # Enviar inmediatamente
    result = await service.send_scheduled_notification(db, scheduled.id)

    logger.info(
        f"✅ Notificación instantánea enviada: {result['sent']} éxitos, {result['failed']} fallos"
    )

    return result


async def send_calendar_reminder(
    db: AsyncSession,
    company_id: UUID,
    event_title: str,
    due_date: datetime,
    description: str,
    phone_numbers: List[str],
    days_before: int = 1,
    user_ids: Optional[List[UUID]] = None,
) -> str:
    """
    Programa un recordatorio de evento de calendario.

    Uso:
        await send_calendar_reminder(
            db,
            company_id,
            "Declaración F29 - Octubre 2025",
            datetime(2025, 11, 12),
            "Presentación mensual de IVA",
            ["+56912345678"],
            days_before=1
        )

    Args:
        db: Sesión de base de datos
        company_id: ID de la empresa
        event_title: Título del evento
        due_date: Fecha de vencimiento
        description: Descripción del evento
        phone_numbers: Lista de teléfonos
        days_before: Días antes del vencimiento (default: 1)
        user_ids: Lista opcional de user_ids

    Returns:
        ID de la notificación programada
    """
    service = get_notification_service()

    # Determinar template según días antes
    template_code = f"calendar_event_reminder_{days_before}d"

    # Si no existe template específico, usar el de 1 día
    template = await service.get_template(db, code=template_code)
    if not template:
        template = await service.get_template(db, code="calendar_event_reminder_1d")

    if not template:
        raise ValueError("No se encontró template de recordatorio")

    # Preparar destinatarios
    recipients = []
    for i, phone in enumerate(phone_numbers):
        recipient = {"phone": phone}
        if user_ids and i < len(user_ids):
            recipient["user_id"] = str(user_ids[i])
        recipients.append(recipient)

    # Contexto del mensaje
    message_context = {
        "event_title": event_title,
        "due_date": due_date.strftime("%d de %B de %Y"),
        "description": description,
    }

    # Programar notificación
    scheduled = await service.schedule_notification(
        db=db,
        company_id=company_id,
        template_id=template.id,
        recipients=recipients,
        message_context=message_context,
        reference_date=due_date,
    )

    logger.info(
        f"📅 Recordatorio programado: '{event_title}' para {scheduled.scheduled_for}"
    )

    return str(scheduled.id)


async def send_f29_reminder(
    db: AsyncSession,
    company_id: UUID,
    period: str,
    due_date: datetime,
    phone_numbers: List[str],
    user_ids: Optional[List[UUID]] = None,
) -> str:
    """
    Envía recordatorio específico para F29.

    Uso:
        await send_f29_reminder(
            db,
            company_id,
            "Octubre 2025",
            datetime(2025, 11, 12),
            ["+56912345678"]
        )

    Args:
        db: Sesión de base de datos
        company_id: ID de la empresa
        period: Período del F29 (ej: "Octubre 2025")
        due_date: Fecha de vencimiento
        phone_numbers: Lista de teléfonos
        user_ids: Lista opcional de user_ids

    Returns:
        ID de la notificación programada
    """
    service = get_notification_service()

    template = await service.get_template(db, code="f29_due_soon")

    if not template:
        raise ValueError("Template 'f29_due_soon' no encontrado")

    # Preparar destinatarios
    recipients = []
    for i, phone in enumerate(phone_numbers):
        recipient = {"phone": phone}
        if user_ids and i < len(user_ids):
            recipient["user_id"] = str(user_ids[i])
        recipients.append(recipient)

    # Contexto del mensaje
    message_context = {
        "period": period,
        "due_date": due_date.strftime("%d de %B de %Y"),
    }

    # Programar notificación
    scheduled = await service.schedule_notification(
        db=db,
        company_id=company_id,
        template_id=template.id,
        recipients=recipients,
        message_context=message_context,
        entity_type="form29",
        reference_date=due_date,
    )

    logger.info(f"📋 Recordatorio F29 programado para {scheduled.scheduled_for}")

    return str(scheduled.id)


async def notify_company_users(
    db: AsyncSession,
    company_id: UUID,
    message: str,
    send_immediately: bool = True,
) -> Dict[str, Any]:
    """
    Envía notificación a todos los usuarios activos de una empresa.

    Uso:
        await notify_company_users(
            db,
            company_id,
            "El sistema estará en mantenimiento mañana de 2-4 AM"
        )

    Args:
        db: Sesión de base de datos
        company_id: ID de la empresa
        message: Mensaje a enviar
        send_immediately: Si True, envía inmediatamente. Si False, solo programa.

    Returns:
        Resultado del envío o ID de notificación programada
    """
    from app.db.models import Profile, Session as UserSession
    from sqlalchemy import select, and_

    # Obtener usuarios activos con teléfono
    result = await db.execute(
        select(Profile, UserSession)
        .join(UserSession, UserSession.user_id == Profile.id)
        .where(
            and_(
                UserSession.company_id == company_id,
                UserSession.is_active == True,
                Profile.phone.isnot(None),
                Profile.phone != "",
            )
        )
        .distinct()
    )

    users = []
    for profile, session in result.all():
        users.append({"user_id": str(profile.id), "phone": profile.phone})

    if not users:
        logger.warning(f"⚠️ No hay usuarios con teléfono en company {company_id}")
        return {"sent": 0, "failed": 0, "skipped": 0, "details": []}

    logger.info(f"📢 Notificando a {len(users)} usuarios de company {company_id}")

    service = get_notification_service()

    # Usar template de sistema
    template = await service.get_template(db, code="system_reminder")

    if not template:
        raise ValueError("Template 'system_reminder' no encontrado")

    # Programar notificación
    scheduled = await service.schedule_notification(
        db=db,
        company_id=company_id,
        template_id=template.id,
        recipients=users,
        message_context={"message": message},
        custom_timing={"type": "immediate"},
    )

    # Enviar si se solicita
    if send_immediately:
        result = await service.send_scheduled_notification(db, scheduled.id)
        return result
    else:
        return {"scheduled_id": str(scheduled.id), "recipients": len(users)}


async def schedule_notification_with_template(
    db: AsyncSession,
    company_id: UUID,
    template_code: str,
    phone_numbers: List[str],
    message_context: Dict[str, Any],
    user_ids: Optional[List[UUID]] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    reference_date: Optional[datetime] = None,
    send_immediately: bool = False,
) -> str:
    """
    Programa una notificación usando un template específico (versión genérica).

    Uso:
        await schedule_notification_with_template(
            db,
            company_id,
            "calendar_event_reminder_1d",
            ["+56912345678"],
            {"event_title": "F29", "due_date": "12 Nov", "description": "IVA"}
        )

    Args:
        db: Sesión de base de datos
        company_id: ID de la empresa
        template_code: Código del template
        phone_numbers: Lista de teléfonos
        message_context: Contexto para variables del mensaje
        user_ids: Lista opcional de user_ids
        entity_type: Tipo de entidad relacionada (opcional)
        entity_id: ID de la entidad (opcional)
        reference_date: Fecha de referencia para calcular timing
        send_immediately: Si True, envía inmediatamente

    Returns:
        ID de la notificación programada
    """
    service = get_notification_service()

    # Obtener template
    template = await service.get_template(db, code=template_code)

    if not template:
        raise ValueError(f"Template '{template_code}' no encontrado")

    # Preparar destinatarios
    recipients = []
    for i, phone in enumerate(phone_numbers):
        recipient = {"phone": phone}
        if user_ids and i < len(user_ids):
            recipient["user_id"] = str(user_ids[i])
        recipients.append(recipient)

    # Timing custom si es inmediato
    custom_timing = {"type": "immediate"} if send_immediately else None

    # Programar notificación
    scheduled = await service.schedule_notification(
        db=db,
        company_id=company_id,
        template_id=template.id,
        recipients=recipients,
        message_context=message_context,
        entity_type=entity_type,
        entity_id=entity_id,
        reference_date=reference_date,
        custom_timing=custom_timing,
    )

    logger.info(f"📅 Notificación programada con template '{template_code}'")

    # Enviar si se solicita
    if send_immediately:
        await service.send_scheduled_notification(db, scheduled.id)
        logger.info(f"✅ Notificación enviada inmediatamente")

    return str(scheduled.id)


async def cancel_scheduled_notification(
    db: AsyncSession,
    notification_id: UUID,
) -> bool:
    """
    Cancela una notificación programada.

    Uso:
        await cancel_scheduled_notification(db, notification_id)

    Args:
        db: Sesión de base de datos
        notification_id: ID de la notificación a cancelar

    Returns:
        True si se canceló exitosamente
    """
    from app.db.models import ScheduledNotification
    from sqlalchemy import select

    result = await db.execute(
        select(ScheduledNotification).where(ScheduledNotification.id == notification_id)
    )
    scheduled = result.scalar_one_or_none()

    if not scheduled:
        logger.warning(f"⚠️ Notificación {notification_id} no encontrada")
        return False

    if scheduled.status != "pending":
        logger.warning(
            f"⚠️ Notificación {notification_id} no está pendiente: {scheduled.status}"
        )
        return False

    scheduled.status = "cancelled"
    scheduled.updated_at = datetime.utcnow()
    await db.commit()

    logger.info(f"🚫 Notificación {notification_id} cancelada")

    return True


# ========== DECORADORES Y HELPERS ==========


def format_phone_number(phone: str) -> str:
    """
    Normaliza número de teléfono chileno.

    Args:
        phone: Número en cualquier formato

    Returns:
        Número normalizado (+56XXXXXXXXX)
    """
    import re

    # Remover espacios, guiones, paréntesis
    phone = re.sub(r"[\s\-\(\)]", "", phone)

    # Si empieza con +56, está ok
    if phone.startswith("+56"):
        return phone

    # Si empieza con 56, agregar +
    if phone.startswith("56"):
        return f"+{phone}"

    # Si empieza con 9 o 2 (móvil o fijo), agregar +56
    if phone.startswith("9") or phone.startswith("2"):
        return f"+56{phone}"

    # Caso default
    return phone


async def get_company_phones(
    db: AsyncSession,
    company_id: UUID,
) -> List[Dict[str, str]]:
    """
    Obtiene teléfonos de todos los usuarios activos de una empresa.

    Args:
        db: Sesión de base de datos
        company_id: ID de la empresa

    Returns:
        Lista de dicts con user_id y phone
    """
    from app.db.models import Profile, Session as UserSession
    from sqlalchemy import select, and_

    result = await db.execute(
        select(Profile, UserSession)
        .join(UserSession, UserSession.user_id == Profile.id)
        .where(
            and_(
                UserSession.company_id == company_id,
                UserSession.is_active == True,
                Profile.phone.isnot(None),
                Profile.phone != "",
            )
        )
        .distinct()
    )

    users = []
    for profile, session in result.all():
        users.append({"user_id": str(profile.id), "phone": profile.phone})

    return users

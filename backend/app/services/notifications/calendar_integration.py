"""
Integración de notificaciones con eventos de calendario
Genera notificaciones automáticas basadas en eventos del calendario tributario
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    CalendarEvent,
    Company,
    Profile,
    Session as UserSession,
    NotificationTemplate,
)
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


class CalendarNotificationIntegration:
    """
    Integración entre el calendario tributario y el sistema de notificaciones.
    Genera automáticamente notificaciones basadas en eventos del calendario.
    """

    def __init__(self, notification_service: NotificationService):
        """
        Inicializa la integración.

        Args:
            notification_service: Instancia del servicio de notificaciones
        """
        self.notification_service = notification_service

    async def _get_company_users(
        self,
        db: AsyncSession,
        company_id: UUID,
    ) -> List[dict]:
        """
        Obtiene usuarios de una empresa con sus teléfonos.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa

        Returns:
            Lista de usuarios con formato [{"user_id": "...", "phone": "+56..."}, ...]
        """
        # Obtener usuarios activos de la empresa
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
            users.append(
                {
                    "user_id": str(profile.id),
                    "phone": profile.phone,
                }
            )

        return users

    async def schedule_notification_for_event(
        self,
        db: AsyncSession,
        calendar_event: CalendarEvent,
        template_code: str,
        offset_days: Optional[int] = None,
    ) -> Optional[str]:
        """
        Programa una notificación para un evento de calendario específico.

        Args:
            db: Sesión de base de datos
            calendar_event: Evento de calendario
            template_code: Código del template a usar
            offset_days: Días de offset (ej: -1 para 1 día antes, None usa config del template)

        Returns:
            ID de la notificación programada o None si no se pudo programar
        """
        # Check if company has active subscription
        from app.infrastructure.celery.subscription_helper import check_company_subscription

        has_subscription = await check_company_subscription(db, calendar_event.company_id)
        if not has_subscription:
            logger.debug(
                f"⏭️  Skipping calendar notification for event {calendar_event.id}: "
                f"Company {calendar_event.company_id} has no active subscription"
            )
            return None

        # Obtener template
        template = await self.notification_service.get_template(db=db, code=template_code)
        if not template:
            logger.warning(f"⚠️ Template '{template_code}' no encontrado")
            return None

        # Verificar suscripción de la empresa
        subscriptions = await self.notification_service.get_company_subscriptions(
            db=db,
            company_id=calendar_event.company_id,
            is_enabled=True,
        )

        is_subscribed = any(
            s.notification_template_id == template.id for s in subscriptions
        )

        if not is_subscribed:
            logger.info(
                f"ℹ️ Company {calendar_event.company_id} no está suscrita a '{template_code}'"
            )
            return None

        # Obtener usuarios de la empresa
        recipients = await self._get_company_users(db, calendar_event.company_id)

        if not recipients:
            logger.warning(
                f"⚠️ No hay usuarios con teléfono para company {calendar_event.company_id}"
            )
            return None

        # Asegurar que event_template está cargado
        if not calendar_event.event_template:
            await db.refresh(calendar_event, ["event_template"])

        # Preparar contexto para el mensaje
        message_context = {
            "event_title": calendar_event.event_template.name,
            "due_date": calendar_event.due_date.strftime("%d de %B de %Y"),
            "description": calendar_event.event_template.description or "Sin descripción",
        }

        # Si el evento tiene período, agregarlo
        if calendar_event.period_start and calendar_event.period_end:
            period_str = (
                f"{calendar_event.period_start.strftime('%B %Y')}"
            )
            message_context["period"] = period_str

        # Usar offset personalizado si se proporciona
        custom_timing = None
        if offset_days is not None:
            custom_timing = {
                "type": "relative",
                "offset_days": offset_days,
                "time": "09:00",
            }

        # Programar notificación
        try:
            scheduled = await self.notification_service.schedule_notification(
                db=db,
                company_id=calendar_event.company_id,
                template_id=template.id,
                recipients=recipients,
                message_context=message_context,
                entity_type="calendar_event",
                entity_id=calendar_event.id,
                reference_date=datetime.combine(
                    calendar_event.due_date,
                    datetime.min.time()
                ),
                custom_timing=custom_timing,
            )

            logger.info(
                f"✅ Notificación programada para evento '{calendar_event.event_template.name}' "
                f"({scheduled.scheduled_for})"
            )

            return str(scheduled.id)

        except Exception as e:
            logger.error(f"❌ Error programando notificación: {e}", exc_info=True)
            return None

    async def schedule_notifications_for_event(
        self,
        db: AsyncSession,
        calendar_event: CalendarEvent,
        notification_templates: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Programa múltiples notificaciones para un evento (7 días, 3 días, 1 día, día actual).

        Args:
            db: Sesión de base de datos
            calendar_event: Evento de calendario
            notification_templates: Lista de códigos de templates (opcional, usa defaults)

        Returns:
            Lista de IDs de notificaciones programadas
        """
        # Templates por defecto
        if not notification_templates:
            notification_templates = [
                "calendar_event_reminder_7d",  # 7 días antes
                "calendar_event_reminder_3d",  # 3 días antes
                "calendar_event_reminder_1d",  # 1 día antes
                "calendar_event_due_today",    # Día del vencimiento
            ]

        scheduled_ids = []

        for template_code in notification_templates:
            scheduled_id = await self.schedule_notification_for_event(
                db=db,
                calendar_event=calendar_event,
                template_code=template_code,
            )

            if scheduled_id:
                scheduled_ids.append(scheduled_id)

        # Asegurar que event_template está cargado
        if not calendar_event.event_template:
            await db.refresh(calendar_event, ["event_template"])

        logger.info(
            f"✅ {len(scheduled_ids)} notificaciones programadas para evento "
            f"'{calendar_event.event_template.name}'"
        )

        return scheduled_ids

    async def schedule_notifications_for_upcoming_events(
        self,
        db: AsyncSession,
        company_id: Optional[UUID] = None,
        days_ahead: int = 30,
    ) -> dict:
        """
        Programa notificaciones para todos los eventos próximos.

        Args:
            db: Sesión de base de datos
            company_id: Filtrar por empresa (opcional)
            days_ahead: Días hacia adelante a considerar

        Returns:
            Estadísticas del procesamiento
        """
        logger.info(
            f"🔄 Programando notificaciones para eventos próximos ({days_ahead} días)..."
        )

        # Obtener eventos próximos
        today = datetime.utcnow().date()
        future_date = today + timedelta(days=days_ahead)

        query = select(CalendarEvent).where(
            and_(
                CalendarEvent.due_date >= today,
                CalendarEvent.due_date <= future_date,
                CalendarEvent.status.in_(["saved", "in_progress"]),
            )
        ).options(selectinload(CalendarEvent.event_template))

        if company_id:
            query = query.where(CalendarEvent.company_id == company_id)

        result = await db.execute(query)
        events = result.scalars().all()

        stats = {
            "events_processed": 0,
            "notifications_scheduled": 0,
            "errors": 0,
        }

        for event in events:
            try:
                scheduled_ids = await self.schedule_notifications_for_event(
                    db=db,
                    calendar_event=event,
                )

                stats["events_processed"] += 1
                stats["notifications_scheduled"] += len(scheduled_ids)

            except Exception as e:
                logger.error(
                    f"❌ Error procesando evento {event.id}: {e}",
                    exc_info=True,
                )
                stats["errors"] += 1

        logger.info(
            f"✅ Programación completada: {stats['events_processed']} eventos, "
            f"{stats['notifications_scheduled']} notificaciones"
        )

        return stats

    async def notify_event_status_change(
        self,
        db: AsyncSession,
        calendar_event: CalendarEvent,
        old_status: str,
        new_status: str,
    ) -> Optional[str]:
        """
        Envía una notificación inmediata cuando cambia el estado de un evento.

        Args:
            db: Sesión de base de datos
            calendar_event: Evento de calendario
            old_status: Estado anterior
            new_status: Nuevo estado

        Returns:
            ID de la notificación programada o None
        """
        # Solo notificar para ciertos cambios de estado
        if new_status == "completed":
            template_code = "calendar_event_completed"
        else:
            # No notificar para otros cambios
            return None

        # Obtener template
        template = await self.notification_service.get_template(db=db, code=template_code)
        if not template:
            return None

        # Obtener usuarios
        recipients = await self._get_company_users(db, calendar_event.company_id)
        if not recipients:
            return None

        # Asegurar que event_template está cargado
        if not calendar_event.event_template:
            await db.refresh(calendar_event, ["event_template"])

        # Contexto del mensaje
        message_context = {
            "event_title": calendar_event.event_template.name,
            "completion_date": (
                calendar_event.completion_date.strftime("%d de %B de %Y")
                if calendar_event.completion_date
                else datetime.utcnow().strftime("%d de %B de %Y")
            ),
        }

        # Programar notificación inmediata
        try:
            scheduled = await self.notification_service.schedule_notification(
                db=db,
                company_id=calendar_event.company_id,
                template_id=template.id,
                recipients=recipients,
                message_context=message_context,
                entity_type="calendar_event",
                entity_id=calendar_event.id,
                reference_date=datetime.utcnow(),
                custom_timing={"type": "immediate"},
            )

            logger.info(
                f"✅ Notificación inmediata programada: evento completado '{calendar_event.event_template.name}'"
            )

            return str(scheduled.id)

        except Exception as e:
            logger.error(f"❌ Error programando notificación: {e}", exc_info=True)
            return None


# ========== FUNCIONES AUXILIARES ==========

async def setup_calendar_event_notifications(
    db: AsyncSession,
    calendar_event: CalendarEvent,
    notification_service: NotificationService,
) -> List[str]:
    """
    Función auxiliar para configurar notificaciones al crear un evento de calendario.

    Uso:
        # En el endpoint de creación de calendario
        from app.services.notifications import NotificationService
        from app.services.notifications.calendar_integration import setup_calendar_event_notifications

        notification_service = NotificationService(whatsapp_service)
        await setup_calendar_event_notifications(db, new_event, notification_service)

    Args:
        db: Sesión de base de datos
        calendar_event: Evento recién creado
        notification_service: Servicio de notificaciones

    Returns:
        Lista de IDs de notificaciones programadas
    """
    integration = CalendarNotificationIntegration(notification_service)
    return await integration.schedule_notifications_for_event(db, calendar_event)


async def notify_calendar_event_completed(
    db: AsyncSession,
    calendar_event: CalendarEvent,
    notification_service: NotificationService,
) -> Optional[str]:
    """
    Función auxiliar para notificar cuando un evento es completado.

    Uso:
        # En el endpoint de actualización de evento
        if new_status == "completed" and old_status != "completed":
            await notify_calendar_event_completed(db, event, notification_service)

    Args:
        db: Sesión de base de datos
        calendar_event: Evento completado
        notification_service: Servicio de notificaciones

    Returns:
        ID de la notificación o None
    """
    integration = CalendarNotificationIntegration(notification_service)
    return await integration.notify_event_status_change(
        db, calendar_event, "in_progress", "completed"
    )

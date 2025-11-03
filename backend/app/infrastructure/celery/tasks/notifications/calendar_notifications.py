"""
Calendar Notifications Task

Tarea periódica para sincronizar notificaciones asociadas a eventos de calendario.

Esta tarea:
1. Escanea CalendarEvents en los próximos 30 días
2. Verifica suscripciones activas a templates de notificaciones
3. Crea ScheduledNotifications para recordatorios (7d, 3d, 1d, hoy)
4. Es idempotente - no duplica notificaciones ya programadas

Frecuencia: Cada 15 minutos
"""
import asyncio
import logging
from datetime import datetime, timedelta

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="notifications.sync_calendar",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def sync_calendar_notifications(self):
    """
    Tarea periódica: Sincroniza notificaciones de calendario.

    Esta tarea escanea eventos de calendario próximos y crea
    ScheduledNotifications para recordatorios automáticos.

    Ejecuta cada 15 minutos.

    Returns:
        dict: Resumen de notificaciones creadas

    Raises:
        Exception: Si hay errores críticos en la sincronización
    """
    logger.info("🔔 Starting calendar notifications sync...")

    async def _sync_notifications():
        from app.config.database import AsyncSessionLocal
        from app.services.notifications import get_notification_service
        from app.services.notifications.calendar_integration import CalendarNotificationIntegration

        async with AsyncSessionLocal() as db:
            # Obtener servicio de notificaciones
            notification_service = await get_notification_service(db)

            # Crear instancia del servicio de integración
            integration = CalendarNotificationIntegration(notification_service)

            # Delegar al servicio de integración
            result = await integration.schedule_notifications_for_upcoming_events(
                db=db,
                company_id=None,  # Todas las empresas
                days_ahead=30
            )

            return result

    try:
        # Run async function in sync context
        result = asyncio.run(_sync_notifications())

        # Log del resultado
        total_created = result.get("total_notifications_created", 0)
        events_processed = result.get("events_processed", 0)

        logger.info(
            f"✅ Calendar notifications sync completed: "
            f"{events_processed} events processed, "
            f"{total_created} notifications created"
        )

        return {
            "success": True,
            "events_processed": events_processed,
            "notifications_created": total_created,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Calendar notifications synced successfully"
        }

    except Exception as e:
        logger.error(f"❌ Error syncing calendar notifications: {e}", exc_info=True)

        # Retry la tarea si falla
        try:
            raise self.retry(exc=e)
        except Exception as retry_error:
            logger.error(f"Max retries reached for calendar notifications sync: {retry_error}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

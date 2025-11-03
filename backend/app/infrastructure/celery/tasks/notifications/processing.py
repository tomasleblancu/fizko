"""
Notification Processing Task

Tarea periódica para procesar y enviar notificaciones pendientes.

Esta tarea:
1. Busca ScheduledNotifications cuyo scheduled_for <= now()
2. Respeta preferencias de usuario (quiet hours, límites diarios)
3. Envía notificaciones vía WhatsApp
4. Crea registros en NotificationHistory
5. Procesa en batches de 50 notificaciones

Frecuencia: Cada 5 minutos
"""
import asyncio
import logging
from datetime import datetime

from app.infrastructure.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="notifications.process_pending",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_pending_notifications(self):
    """
    Tarea periódica: Procesa notificaciones pendientes.

    Esta tarea busca todas las ScheduledNotifications cuyo scheduled_for
    ya pasó y las envía a los usuarios vía WhatsApp, respetando sus
    preferencias de notificaciones.

    Es genérica - procesa notificaciones de cualquier tipo (calendario,
    documentos, payroll, etc.)

    Ejecuta cada 5 minutos.

    Returns:
        dict: Resumen de notificaciones enviadas

    Raises:
        Exception: Si hay errores críticos en el procesamiento
    """
    logger.info("📤 Starting pending notifications processing...")

    async def _process_notifications():
        from app.services.notifications.scheduler import process_pending_notifications_task

        # Delegar al servicio de scheduler
        # Este servicio maneja toda la lógica de:
        # - Buscar notificaciones pendientes
        # - Validar preferencias de usuario
        # - Enviar vía WhatsApp
        # - Crear historial
        result = await process_pending_notifications_task(batch_size=50)
        return result

    try:
        # Run async function in sync context
        result = asyncio.run(_process_notifications())

        # Log del resultado
        sent_count = result.get("sent_count", 0)
        skipped_count = result.get("skipped_count", 0)
        failed_count = result.get("failed_count", 0)

        logger.info(
            f"✅ Notification processing completed: "
            f"{sent_count} sent, {skipped_count} skipped, {failed_count} failed"
        )

        return {
            "success": True,
            "sent_count": sent_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Pending notifications processed successfully"
        }

    except Exception as e:
        logger.error(f"❌ Error processing pending notifications: {e}", exc_info=True)

        # Retry la tarea si falla
        try:
            raise self.retry(exc=e)
        except Exception as retry_error:
            logger.error(f"Max retries reached for notification processing: {retry_error}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

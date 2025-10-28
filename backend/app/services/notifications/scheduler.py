"""
Scheduler de notificaciones
Puede ejecutarse manualmente o con Celery
"""
import logging
import asyncio
from typing import Optional

from app.config.database import AsyncSessionLocal
from app.services.notifications import NotificationService
from app.services.whatsapp.service import WhatsAppService
import os

logger = logging.getLogger(__name__)


async def process_pending_notifications_task(
    batch_size: int = 50,
    whatsapp_service: Optional[WhatsAppService] = None,
) -> dict:
    """
    Tarea asíncrona para procesar notificaciones pendientes.

    Args:
        batch_size: Número máximo de notificaciones a procesar
        whatsapp_service: Instancia del servicio de WhatsApp (opcional, se crea si no se proporciona)

    Returns:
        Diccionario con estadísticas del procesamiento
    """
    logger.info("🚀 Iniciando procesamiento de notificaciones pendientes...")

    # Crear servicio de WhatsApp si no se proporciona
    if not whatsapp_service:
        kapso_token = os.getenv("KAPSO_API_TOKEN", "")
        kapso_base_url = os.getenv("KAPSO_API_BASE_URL", "https://app.kapso.ai/api/v1")
        whatsapp_service = WhatsAppService(
            api_token=kapso_token,
            base_url=kapso_base_url,
        )

    # Crear servicio de notificaciones
    notification_service = NotificationService(whatsapp_service=whatsapp_service)

    # Procesar notificaciones
    async with AsyncSessionLocal() as db:
        try:
            stats = await notification_service.process_pending_notifications(
                db=db,
                batch_size=batch_size,
            )

            logger.info(f"✅ Procesamiento completado: {stats}")
            return stats

        except Exception as e:
            logger.error(f"❌ Error procesando notificaciones: {e}", exc_info=True)
            raise


def run_notification_scheduler_sync(batch_size: int = 50):
    """
    Versión síncrona del scheduler para ejecutar manualmente.

    Ejemplo de uso:
        python -m app.services.notifications.scheduler

    Args:
        batch_size: Número máximo de notificaciones a procesar
    """
    asyncio.run(process_pending_notifications_task(batch_size=batch_size))


# ========== CELERY INTEGRATION (FUTURO) ==========

# Para integrar con Celery, descomentar y configurar:
#
# from app.celery_app import celery_app
#
# @celery_app.task(name="process_pending_notifications")
# def celery_process_pending_notifications(batch_size: int = 50):
#     """
#     Tarea de Celery para procesar notificaciones pendientes.
#
#     Configurar en Celery Beat para ejecución periódica:
#
#     CELERY_BEAT_SCHEDULE = {
#         'process-notifications-every-5-minutes': {
#             'task': 'process_pending_notifications',
#             'schedule': crontab(minute='*/5'),  # Cada 5 minutos
#             'args': (50,),  # batch_size
#         },
#     }
#     """
#     return asyncio.run(process_pending_notifications_task(batch_size=batch_size))


if __name__ == "__main__":
    # Ejecutar scheduler manualmente
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("📅 Ejecutando scheduler de notificaciones manualmente...")
    run_notification_scheduler_sync(batch_size=50)
    logger.info("✅ Scheduler completado")

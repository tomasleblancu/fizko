"""
Notification Tasks Module

Este módulo contiene tareas de Celery relacionadas con notificaciones.

Estructura modular:
- calendar_notifications.py: Sincronización de notificaciones de calendario
- processing.py: Procesamiento y envío de notificaciones pendientes
- template_notification.py: Tarea genérica template-driven para todos los resúmenes de negocio

NOTA: Los PeriodicTasks se crean manualmente via Admin UI (/admin/scheduled-tasks)
      o directamente en la base de datos (tabla: celery_periodictask).

USO:
Para crear nuevos resúmenes periódicos:
1. Crear template en DB con metadata.summary_config
2. Crear PeriodicTask que use: process_template_notification(template_code="your_template_code")

Ejemplos:
- Daily summary: process_template_notification(template_code="daily_business_summary")
- Weekly summary: process_template_notification(template_code="weekly_business_summary")
"""

from .calendar_notifications import sync_calendar_notifications
from .processing import process_pending_notifications
from .template_notification import process_template_notification

__all__ = [
    "sync_calendar_notifications",
    "process_pending_notifications",
    "process_template_notification",
]

"""
Calendar Tasks Module

Tareas de Celery relacionadas con sincronización de calendario tributario.

Estructura modular:
- sync.py: Sincronización de eventos de calendario para empresas
- events.py: Activación de eventos obligatorios y asignación de notificaciones
"""

from .sync import sync_company_calendar, sync_all_companies_calendar
from .events import activate_mandatory_events_task, assign_auto_notifications_task

__all__ = [
    "sync_company_calendar",
    "sync_all_companies_calendar",
    "activate_mandatory_events_task",
    "assign_auto_notifications_task",
]

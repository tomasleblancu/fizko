"""
Servicio de notificaciones por WhatsApp
"""

from .service import NotificationService
from .helpers import (
    # Singleton
    get_notification_service,
    # Funciones simples
    send_instant_notification,
    send_calendar_reminder,
    send_f29_reminder,
    notify_company_users,
    schedule_notification_with_template,
    cancel_scheduled_notification,
    # Utilidades
    format_phone_number,
    get_company_phones,
)

__all__ = [
    # Servicio principal
    "NotificationService",
    # Singleton
    "get_notification_service",
    # Funciones simples de uso rápido
    "send_instant_notification",
    "send_calendar_reminder",
    "send_f29_reminder",
    "notify_company_users",
    "schedule_notification_with_template",
    "cancel_scheduled_notification",
    # Utilidades
    "format_phone_number",
    "get_company_phones",
]

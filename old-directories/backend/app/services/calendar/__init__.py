"""
Calendar service module - Gestión de eventos del calendario tributario

Estructura modular:
- base_service: Funcionalidad común y helpers
- event_config_service: Activar/desactivar eventos
- sync_service: Sincronización de calendario
- service: Facade unificado (punto de entrada principal)
"""

from .base_service import BaseCalendarService
from .event_config_service import EventConfigService
from .sync_service import SyncService
from .service import (
    CalendarService,
    get_calendar_service,
    get_event_config_service,
    get_sync_service
)

__all__ = [
    "BaseCalendarService",
    "EventConfigService",
    "SyncService",
    "CalendarService",
    "get_calendar_service",
    "get_event_config_service",
    "get_sync_service"
]

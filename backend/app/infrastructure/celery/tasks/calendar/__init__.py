"""
Calendar Celery tasks for Backend V2.

This module contains all Celery tasks related to calendar operations:
- Event synchronization (sync_company_calendar, sync_all_calendars)
- Event generation from company_events
"""
from .events import sync_company_calendar, sync_all_calendars

__all__ = [
    "sync_company_calendar",
    "sync_all_calendars",
]

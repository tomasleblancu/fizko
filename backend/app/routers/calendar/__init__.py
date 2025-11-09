"""Calendar router module."""

from fastapi import APIRouter, Depends

from ...dependencies import require_auth
from .calendar_events import router as calendar_events_router
from .company_calendar import router as company_calendar_router
from .company_events import router as company_events_router
from .event_history import router as event_history_router
from .event_templates import router as event_templates_router
from .statistics import router as statistics_router

# Create main calendar router
router = APIRouter(
    prefix="/api/calendar",
    tags=["calendar"],
    dependencies=[Depends(require_auth)]
)

# Include all sub-routers
router.include_router(event_templates_router)
router.include_router(company_events_router)
router.include_router(calendar_events_router)
router.include_router(statistics_router)
router.include_router(event_history_router)
router.include_router(company_calendar_router)

__all__ = ["router"]

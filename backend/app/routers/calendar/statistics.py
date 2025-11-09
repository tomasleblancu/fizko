"""REST API endpoints for calendar statistics."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id, require_auth
from ...repositories.calendar import CalendarRepository

router = APIRouter(
    prefix="/stats",
    tags=["calendar-stats"],
    dependencies=[Depends(require_auth)]
)


@router.get("")
async def get_calendar_stats(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Obtener estadísticas del calendario de una empresa.

    - **company_id**: ID de la empresa
    """
    repo = CalendarRepository(db)

    # Eventos pendientes
    pending_events = await repo.get_pending_events(company_id)

    # Eventos vencidos
    overdue_events = await repo.get_overdue_events(company_id)

    # Próximos 7 días
    upcoming_events = await repo.get_upcoming_week_events(company_id)

    # Eventos completados este mes
    completed_events = await repo.get_completed_events_this_month(company_id)

    return {
        "data": {
            "pending": len(pending_events),
            "overdue": len(overdue_events),
            "upcoming_7_days": len(upcoming_events),
            "completed_this_month": len(completed_events),
            "today": date.today().isoformat(),
        }
    }

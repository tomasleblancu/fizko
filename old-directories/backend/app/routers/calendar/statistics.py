"""REST API endpoints for calendar statistics."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id, require_auth
from ...repositories.calendar import CalendarRepository
from ...utils.company_resolver import get_user_primary_company_id

router = APIRouter(
    prefix="/stats",
    tags=["calendar-stats"],
    dependencies=[Depends(require_auth)]
)


@router.get("")
async def get_calendar_stats(
    company_id: UUID | None = Query(None, description="Company ID (optional, resolved from user if not provided)"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Obtener estadísticas del calendario de una empresa.

    - **company_id**: ID de la empresa (opcional, se resuelve automáticamente del usuario si no se proporciona)
    """
    # Resolve company_id from user's active session if not provided
    if company_id is None:
        company_id = await get_user_primary_company_id(user_id, db)
        if not company_id:
            raise HTTPException(
                status_code=404,
                detail="No active company found for user"
            )

    repo = CalendarRepository(db)

    # Eventos guardados (saved)
    saved_events = await repo.get_pending_events(company_id)

    # Eventos vencidos
    overdue_events = await repo.get_overdue_events(company_id)

    # Próximos 7 días
    upcoming_events = await repo.get_upcoming_week_events(company_id)

    # Eventos completados este mes
    completed_events = await repo.get_completed_events_this_month(company_id)

    return {
        "data": {
            "pending": len(saved_events),
            "overdue": len(overdue_events),
            "upcoming_7_days": len(upcoming_events),
            "completed_this_month": len(completed_events),
            "today": date.today().isoformat(),
        }
    }

"""REST API endpoints for calendar event management."""

from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id, require_auth
from ...repositories.calendar import CalendarRepository
from ...utils.company_resolver import get_user_primary_company_id

router = APIRouter(
    prefix="/events",
    tags=["calendar-events"],
    dependencies=[Depends(require_auth)]
)


@router.get("")
async def list_calendar_events(
    company_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    status: str | None = None,
    event_template_code: str | None = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Obtener eventos del calendario para una empresa.

    - **company_id**: ID de la empresa
    - **start_date**: Fecha de inicio (formato: YYYY-MM-DD)
    - **end_date**: Fecha de fin (formato: YYYY-MM-DD)
    - **status**: Filtrar por estado (saved, in_progress, completed, overdue, cancelled)
    - **event_template_code**: Filtrar por tipo de evento (f29, f22, etc.)
    - **limit**: Máximo de resultados (default: 50, max: 200)
    """
    repo = CalendarRepository(db)
    events = await repo.get_calendar_events(
        company_id,
        start_date,
        end_date,
        status,
        event_template_code,
        limit
    )

    return {
        "data": [
            {
                "id": str(event.id),
                "title": event.event_template.name,
                "description": event.event_template.description,
                "event_template": {
                    "code": event.event_template.code,
                    "name": event.event_template.name,
                    "category": event.event_template.category,
                },
                "due_date": event.due_date.isoformat(),
                "period_start": event.period_start.isoformat() if event.period_start else None,
                "period_end": event.period_end.isoformat() if event.period_end else None,
                "status": event.status,
                "completion_date": event.completion_date.isoformat() if event.completion_date else None,
                "completion_data": event.completion_data,
                "tasks_count": len(event.tasks),
                "tasks_completed": sum(1 for t in event.tasks if t.status == "completed"),
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
        "total": len(events),
        "filters": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "status": status,
            "event_template_code": event_template_code,
        }
    }


@router.get("/upcoming")
async def get_upcoming_events(
    company_id: UUID | None = Query(None, description="Company ID (optional, resolved from user if not provided)"),
    days_ahead: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Obtener eventos próximos a vencer.

    - **company_id**: ID de la empresa (opcional, se resuelve automáticamente del usuario si no se proporciona)
    - **days_ahead**: Días hacia adelante (default: 30, max: 365)
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
    events = await repo.get_upcoming_events(company_id, days_ahead)

    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    return {
        "data": [
            {
                "id": str(event.id),
                "title": event.event_template.name,
                "event_template": {
                    "code": event.event_template.code,
                    "name": event.event_template.name,
                },
                "due_date": event.due_date.isoformat(),
                "days_until_due": (event.due_date - today).days,
                "status": event.status,
            }
            for event in events
        ],
        "total": len(events),
        "period": {
            "start": today.isoformat(),
            "end": end_date.isoformat(),
            "days": days_ahead
        }
    }


@router.get("/{event_id}")
async def get_calendar_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Obtener detalle completo de un evento del calendario."""
    repo = CalendarRepository(db)
    event = await repo.get_calendar_event_by_id(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    # Asegurar que event_template está cargado
    if not event.event_template:
        await db.refresh(event, ["event_template"])

    return {
        "data": {
            "id": str(event.id),
            "title": event.event_template.name,
            "description": event.event_template.description,
            "event_template": {
                "id": str(event.event_template.id),
                "code": event.event_template.code,
                "name": event.event_template.name,
                "category": event.event_template.category,
                "authority": event.event_template.authority,
            },
            "due_date": event.due_date.isoformat(),
            "period_start": event.period_start.isoformat() if event.period_start else None,
            "period_end": event.period_end.isoformat() if event.period_end else None,
            "status": event.status,
            "completion_date": event.completion_date.isoformat() if event.completion_date else None,
            "completion_data": event.completion_data,
            "auto_generated": event.auto_generated,
            "metadata": event.extra_metadata,
            "tasks": [
                {
                    "id": str(task.id),
                    "task_type": task.task_type,
                    "title": task.title,
                    "description": task.description,
                    "order_index": task.order_index,
                    "status": task.status,
                    "is_automated": task.is_automated,
                    "completion_data": task.completion_data,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                }
                for task in sorted(event.tasks, key=lambda t: t.order_index)
            ],
            "created_at": event.created_at.isoformat(),
            "updated_at": event.updated_at.isoformat(),
        }
    }


@router.post("/{event_id}/complete")
async def complete_calendar_event(
    event_id: UUID,
    completion_data: dict | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Marcar un evento como completado.

    - **event_id**: ID del evento
    - **completion_data**: Datos opcionales del cumplimiento (folio, monto, etc.)
    """
    repo = CalendarRepository(db)
    event = await repo.get_calendar_event_by_id(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    # Asegurar que event_template está cargado
    if not event.event_template:
        await db.refresh(event, ["event_template"])

    event.status = "completed"
    event.completion_date = datetime.now()
    event.completion_data = completion_data or {}

    event = await repo.update_calendar_event(event)

    return {
        "data": {
            "id": str(event.id),
            "title": event.event_template.name,
            "status": event.status,
            "completion_date": event.completion_date.isoformat(),
            "completion_data": event.completion_data,
        },
        "message": "Evento marcado como completado"
    }


@router.patch("/{event_id}/status")
async def update_event_status(
    event_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Actualizar el estado de un evento.

    - **event_id**: ID del evento
    - **status**: Nuevo estado (saved, in_progress, completed, overdue, cancelled)
    """
    valid_statuses = ["saved", "in_progress", "completed", "overdue", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Debe ser uno de: {', '.join(valid_statuses)}"
        )

    repo = CalendarRepository(db)
    event = await repo.get_calendar_event_by_id(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    # Asegurar que event_template está cargado
    if not event.event_template:
        await db.refresh(event, ["event_template"])

    event.status = status

    if status == "completed" and not event.completion_date:
        event.completion_date = datetime.now()

    event = await repo.update_calendar_event(event)

    return {
        "data": {
            "id": str(event.id),
            "title": event.event_template.name,
            "status": event.status,
        },
        "message": f"Estado actualizado a '{status}'"
    }

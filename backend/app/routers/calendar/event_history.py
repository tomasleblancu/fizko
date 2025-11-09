"""REST API endpoints for event history management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import EventHistory
from ...dependencies import get_current_user_id, require_auth
from ...repositories.calendar import CalendarRepository
from ...schemas.calendar import CreateEventHistoryRequest

router = APIRouter(
    prefix="/events/{event_id}/history",
    tags=["calendar-history"],
    dependencies=[Depends(require_auth)]
)


@router.get("")
async def get_event_history(
    event_id: UUID,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Obtener el historial completo de un evento del calendario.

    - **event_id**: ID del evento
    - **limit**: Máximo de registros a devolver (default: 50, max: 200)
    """
    repo = CalendarRepository(db)

    # Verificar que el evento existe y el usuario tiene acceso
    event = await repo.get_calendar_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    # Obtener historial
    history_entries = await repo.get_event_history(event_id, limit)

    return {
        "data": [
            {
                "id": str(entry.id),
                "event_type": entry.event_type,
                "title": entry.title,
                "description": entry.description,
                "metadata": entry.event_metadata,
                "user_id": str(entry.user_id) if entry.user_id else None,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in history_entries
        ],
        "total": len(history_entries),
        "event": {
            "id": str(event.id),
            "title": event.title,
            "status": event.status,
        }
    }


@router.post("")
async def add_event_history(
    event_id: UUID,
    request: CreateEventHistoryRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Agregar una entrada manual al historial de un evento.

    - **event_id**: ID del evento
    - **event_type**: Tipo de evento (note_added, document_attached, etc.)
    - **title**: Título corto del evento
    - **description**: Descripción detallada (opcional)
    - **metadata**: Datos adicionales en formato JSON (opcional)
    """
    # Validar event_type
    valid_types = [
        'note_added', 'document_attached', 'updated',
        'system_action', 'task_completed', 'reminder_sent'
    ]
    if request.event_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de evento inválido. Debe ser uno de: {', '.join(valid_types)}"
        )

    repo = CalendarRepository(db)

    # Verificar que el evento existe
    event = await repo.get_calendar_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    # Crear entrada en el historial
    history_entry = EventHistory(
        calendar_event_id=event_id,
        user_id=user_id,
        event_type=request.event_type,
        title=request.title,
        description=request.description,
        event_metadata=request.metadata or {}
    )

    history_entry = await repo.create_event_history(history_entry)

    return {
        "data": {
            "id": str(history_entry.id),
            "event_type": history_entry.event_type,
            "title": history_entry.title,
            "description": history_entry.description,
            "metadata": history_entry.event_metadata,
            "user_id": str(history_entry.user_id),
            "created_at": history_entry.created_at.isoformat(),
        },
        "message": "Entrada agregada al historial exitosamente"
    }

"""REST API endpoints for tax calendar management."""

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...config.database import get_db
from ...db.models import CalendarEvent, Company, CompanyEvent, EventHistory, EventTask, EventTemplate
from ...dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/calendar",
    tags=["calendar"],
    dependencies=[Depends(require_auth)]
)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CreateEventTemplateRequest(BaseModel):
    code: str
    name: str
    category: str
    authority: str
    is_mandatory: bool
    default_recurrence: dict
    description: Optional[str] = None
    applies_to_regimes: Optional[dict] = None
    metadata: Optional[dict] = None


class UpdateEventTemplateRequest(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    authority: Optional[str] = None
    is_mandatory: Optional[bool] = None
    default_recurrence: Optional[dict] = None
    description: Optional[str] = None
    applies_to_regimes: Optional[dict] = None
    metadata: Optional[dict] = None


# ============================================================================
# EVENT TEMPLATES (Plantillas Globales)
# ============================================================================

@router.get("/event-templates")
async def list_event_templates(
    category: Optional[str] = None,
    is_mandatory: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Obtener catálogo de tipos de eventos tributarios.

    - **category**: Filtrar por categoría (impuesto_mensual, impuesto_anual, prevision, etc.)
    - **is_mandatory**: Filtrar por obligatorios (true) u opcionales (false)
    """
    query = select(EventTemplate)

    if category:
        query = query.where(EventTemplate.category == category)
    if is_mandatory is not None:
        query = query.where(EventTemplate.is_mandatory == is_mandatory)

    query = query.order_by(EventTemplate.category, EventTemplate.name)

    result = await db.execute(query)
    event_templates = result.scalars().all()

    return {
        "data": [
            {
                "id": str(et.id),
                "code": et.code,
                "name": et.name,
                "description": et.description,
                "category": et.category,
                "authority": et.authority,
                "is_mandatory": et.is_mandatory,
                "applies_to_regimes": et.applies_to_regimes,
                "default_recurrence": et.default_recurrence,
                "metadata": et.extra_metadata,
            }
            for et in event_templates
        ],
        "total": len(event_templates)
    }


@router.get("/event-templates/{event_template_id}")
async def get_event_template(
    event_template_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtener detalle de un tipo de evento."""
    result = await db.execute(
        select(EventTemplate).where(EventTemplate.id == event_template_id)
    )
    event_template = result.scalar_one_or_none()

    if not event_template:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")

    return {
        "data": {
            "id": str(event_template.id),
            "code": event_template.code,
            "name": event_template.name,
            "description": event_template.description,
            "category": event_template.category,
            "authority": event_template.authority,
            "is_mandatory": event_template.is_mandatory,
            "applies_to_regimes": event_template.applies_to_regimes,
            "default_recurrence": event_template.default_recurrence,
            "metadata": event_template.extra_metadata,
        }
    }


@router.post("/event-templates")
async def create_event_template(
    request: CreateEventTemplateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Crear un nuevo tipo de evento tributario.

    - **code**: Código único del evento (ej: f29, f22, previred)
    - **name**: Nombre descriptivo
    - **category**: Categoría (impuesto_mensual, impuesto_anual, prevision, etc.)
    - **authority**: Autoridad (SII, Previred, etc.)
    - **is_mandatory**: Si es obligatorio
    - **default_recurrence**: Configuración de recurrencia por defecto
    - **description**: Descripción opcional
    - **applies_to_regimes**: Regímenes a los que aplica (opcional)
    - **metadata**: Metadatos adicionales (opcional)
    """
    # Verificar que el código no existe
    result = await db.execute(
        select(EventTemplate).where(EventTemplate.code == request.code)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un tipo de evento con el código '{request.code}'"
        )

    # Crear nuevo event_template
    new_event_template = EventTemplate(
        code=request.code,
        name=request.name,
        description=request.description,
        category=request.category,
        authority=request.authority,
        is_mandatory=request.is_mandatory,
        applies_to_regimes=request.applies_to_regimes or {},
        default_recurrence=request.default_recurrence,
        extra_metadata=request.metadata or {},
    )

    db.add(new_event_template)
    await db.commit()
    # No refresh needed - all data is already in memory

    return {
        "data": {
            "id": str(new_event_template.id),
            "code": new_event_template.code,
            "name": new_event_template.name,
            "description": new_event_template.description,
            "category": new_event_template.category,
            "authority": new_event_template.authority,
            "is_mandatory": new_event_template.is_mandatory,
            "applies_to_regimes": new_event_template.applies_to_regimes,
            "default_recurrence": new_event_template.default_recurrence,
            "metadata": new_event_template.extra_metadata,
        },
        "message": "Tipo de evento creado exitosamente"
    }


@router.delete("/event-templates/{event_template_id}")
async def delete_event_template(
    event_template_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Eliminar un tipo de evento.

    ADVERTENCIA: Esto eliminará todas las reglas y eventos asociados.
    """
    # Buscar el event_template
    result = await db.execute(
        select(EventTemplate).where(EventTemplate.id == event_template_id)
    )
    event_template = result.scalar_one_or_none()

    if not event_template:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")

    # Verificar si hay reglas activas asociadas
    result = await db.execute(
        select(CompanyEvent).where(
            and_(
                CompanyEvent.event_template_id == event_template_id,
                CompanyEvent.is_active == True
            )
        )
    )
    active_rules = result.scalars().all()

    if active_rules:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar. Hay {len(active_rules)} empresa(s) con este evento activo. Desactiva primero todas las reglas."
        )

    # Eliminar event_template (las FK con CASCADE eliminarán reglas y eventos)
    await db.delete(event_template)
    await db.commit()

    return {
        "message": f"Tipo de evento '{event_template.name}' eliminado exitosamente"
    }


@router.put("/event-templates/{event_template_id}")
async def update_event_template(
    event_template_id: UUID,
    request: UpdateEventTemplateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Actualizar un tipo de evento.

    - Solo se actualizan los campos proporcionados
    - Si se cambia el código, verifica que no exista otro evento con ese código
    """
    # Buscar el event_template
    result = await db.execute(
        select(EventTemplate).where(EventTemplate.id == event_template_id)
    )
    event_template = result.scalar_one_or_none()

    if not event_template:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")

    # Si se intenta cambiar el código, verificar que no exista
    if request.code and request.code != event_template.code:
        result = await db.execute(
            select(EventTemplate).where(EventTemplate.code == request.code)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un tipo de evento con el código '{request.code}'"
            )

    # Actualizar solo los campos proporcionados
    if request.code is not None:
        event_template.code = request.code
    if request.name is not None:
        event_template.name = request.name
    if request.description is not None:
        event_template.description = request.description
    if request.category is not None:
        event_template.category = request.category
    if request.authority is not None:
        event_template.authority = request.authority
    if request.is_mandatory is not None:
        event_template.is_mandatory = request.is_mandatory
    if request.default_recurrence is not None:
        event_template.default_recurrence = request.default_recurrence
    if request.applies_to_regimes is not None:
        event_template.applies_to_regimes = request.applies_to_regimes
    if request.metadata is not None:
        event_template.extra_metadata = request.metadata

    await db.commit()
    # No refresh needed - object already has updated values

    return {
        "data": {
            "id": str(event_template.id),
            "code": event_template.code,
            "name": event_template.name,
            "description": event_template.description,
            "category": event_template.category,
            "authority": event_template.authority,
            "is_mandatory": event_template.is_mandatory,
            "applies_to_regimes": event_template.applies_to_regimes,
            "default_recurrence": event_template.default_recurrence,
            "metadata": event_template.extra_metadata,
        },
        "message": "Tipo de evento actualizado exitosamente"
    }


# ============================================================================
# COMPANY EVENTS (Vínculos Empresa-Evento)
# ============================================================================

@router.get("/rules")
async def list_company_events(
    company_id: UUID,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Obtener vínculos empresa-evento configurados para una empresa.

    - **company_id**: ID de la empresa
    - **is_active**: Filtrar por eventos activos (true) o inactivos (false)
    """
    query = select(CompanyEvent).options(
        selectinload(CompanyEvent.event_template)
    ).where(CompanyEvent.company_id == company_id)

    if is_active is not None:
        query = query.where(CompanyEvent.is_active == is_active)

    result = await db.execute(query)
    company_events = result.scalars().all()

    return {
        "data": [
            {
                "id": str(company_event.id),
                "company_id": str(company_event.company_id),
                "event_template": {
                    "id": str(company_event.event_template.id),
                    "code": company_event.event_template.code,
                    "name": company_event.event_template.name,
                    "category": company_event.event_template.category,
                },
                "is_active": company_event.is_active,
                "custom_config": company_event.custom_config,
                "created_at": company_event.created_at.isoformat(),
                "updated_at": company_event.updated_at.isoformat(),
            }
            for company_event in company_events
        ],
        "total": len(company_events)
    }


@router.post("/rules")
async def create_company_event(
    company_id: UUID,
    event_template_code: str,
    is_active: bool = True,
    custom_config: dict = None,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Vincular un template de evento a una empresa.

    - **company_id**: ID de la empresa
    - **event_template_code**: Código del evento (f29, f22, previred, etc.)
    - **is_active**: Si está activo (default: true)
    - **custom_config**: Configuración personalizada (opcional, para casos edge)
    """
    # Verificar que el event_template existe
    result = await db.execute(
        select(EventTemplate).where(EventTemplate.code == event_template_code)
    )
    event_template = result.scalar_one_or_none()

    if not event_template:
        raise HTTPException(status_code=404, detail=f"Template de evento '{event_template_code}' no encontrado")

    # Verificar que la empresa existe
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    # Verificar que no existe ya este vínculo
    result = await db.execute(
        select(CompanyEvent).where(
            and_(
                CompanyEvent.company_id == company_id,
                CompanyEvent.event_template_id == event_template.id
            )
        )
    )
    existing_company_event = result.scalar_one_or_none()

    if existing_company_event:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un vínculo para el evento '{event_template_code}' en esta empresa"
        )

    # Crear el vínculo empresa-evento
    new_company_event = CompanyEvent(
        company_id=company_id,
        event_template_id=event_template.id,
        is_active=is_active,
        custom_config=custom_config or {}
    )

    db.add(new_company_event)
    await db.commit()
    # No refresh needed - all data is in memory

    return {
        "data": {
            "id": str(new_company_event.id),
            "company_id": str(new_company_event.company_id),
            "event_template_id": str(new_company_event.event_template_id),
            "is_active": new_company_event.is_active,
            "custom_config": new_company_event.custom_config,
        },
        "message": f"Evento '{event_template_code}' vinculado a la empresa exitosamente"
    }


@router.patch("/rules/{company_event_id}")
async def update_company_event(
    company_event_id: UUID,
    is_active: Optional[bool] = None,
    custom_config: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Actualizar configuración de un vínculo empresa-evento."""
    result = await db.execute(
        select(CompanyEvent).where(CompanyEvent.id == company_event_id)
    )
    company_event = result.scalar_one_or_none()

    if not company_event:
        raise HTTPException(status_code=404, detail="Vínculo empresa-evento no encontrado")

    # Actualizar campos proporcionados
    if is_active is not None:
        company_event.is_active = is_active
    if custom_config is not None:
        company_event.custom_config = custom_config

    await db.commit()
    # No refresh needed - updated object is already in memory

    return {
        "data": {
            "id": str(company_event.id),
            "company_id": str(company_event.company_id),
            "event_template_id": str(company_event.event_template_id),
            "is_active": company_event.is_active,
            "custom_config": company_event.custom_config,
        },
        "message": "Vínculo empresa-evento actualizado exitosamente"
    }


# ============================================================================
# CALENDAR EVENTS (Instancias Concretas)
# ============================================================================

@router.get("/events")
async def list_calendar_events(
    company_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    event_template_code: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Obtener eventos del calendario para una empresa.

    - **company_id**: ID de la empresa
    - **start_date**: Fecha de inicio (formato: YYYY-MM-DD)
    - **end_date**: Fecha de fin (formato: YYYY-MM-DD)
    - **status**: Filtrar por estado (pending, in_progress, completed, overdue, cancelled)
    - **event_template_code**: Filtrar por tipo de evento (f29, f22, etc.)
    - **limit**: Máximo de resultados (default: 50, max: 200)
    """
    query = select(CalendarEvent).options(
        selectinload(CalendarEvent.event_template),
        selectinload(CalendarEvent.tasks)
    ).where(CalendarEvent.company_id == company_id)

    if start_date:
        query = query.where(CalendarEvent.due_date >= start_date)
    if end_date:
        query = query.where(CalendarEvent.due_date <= end_date)
    if status:
        query = query.where(CalendarEvent.status == status)
    if event_template_code:
        # Join con event_template para filtrar por code
        query = query.join(EventTemplate).where(EventTemplate.code == event_template_code)

    query = query.order_by(CalendarEvent.due_date).limit(limit)

    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "data": [
            {
                "id": str(event.id),
                "title": event.title,
                "description": event.description,
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


@router.get("/events/upcoming")
async def get_upcoming_events(
    company_id: UUID,
    days_ahead: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Obtener eventos próximos a vencer.

    - **company_id**: ID de la empresa
    - **days_ahead**: Días hacia adelante (default: 30, max: 365)
    """
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    query = select(CalendarEvent).options(
        selectinload(CalendarEvent.event_template)
    ).where(
        and_(
            CalendarEvent.company_id == company_id,
            CalendarEvent.due_date >= today,
            CalendarEvent.due_date <= end_date,
            CalendarEvent.status.in_(["pending", "in_progress"])
        )
    ).order_by(CalendarEvent.due_date)

    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "data": [
            {
                "id": str(event.id),
                "title": event.title,
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


@router.get("/events/{event_id}")
async def get_calendar_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Obtener detalle completo de un evento del calendario."""
    result = await db.execute(
        select(CalendarEvent).options(
            selectinload(CalendarEvent.event_template),
            selectinload(CalendarEvent.tasks)
        ).where(CalendarEvent.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    return {
        "data": {
            "id": str(event.id),
            "title": event.title,
            "description": event.description,
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


@router.post("/events/{event_id}/complete")
async def complete_calendar_event(
    event_id: UUID,
    completion_data: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Marcar un evento como completado.

    - **event_id**: ID del evento
    - **completion_data**: Datos opcionales del cumplimiento (folio, monto, etc.)
    """
    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    event.status = "completed"
    event.completion_date = datetime.now()
    event.completion_data = completion_data or {}

    await db.commit()
    # No refresh needed - all updated data is in memory

    return {
        "data": {
            "id": str(event.id),
            "title": event.title,
            "status": event.status,
            "completion_date": event.completion_date.isoformat(),
            "completion_data": event.completion_data,
        },
        "message": "Evento marcado como completado"
    }


@router.patch("/events/{event_id}/status")
async def update_event_status(
    event_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Actualizar el estado de un evento.

    - **event_id**: ID del evento
    - **status**: Nuevo estado (pending, in_progress, completed, overdue, cancelled)
    """
    valid_statuses = ["pending", "in_progress", "completed", "overdue", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Debe ser uno de: {', '.join(valid_statuses)}"
        )

    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    event.status = status

    if status == "completed" and not event.completion_date:
        event.completion_date = datetime.now()

    await db.commit()
    # No refresh needed - updated data is in memory

    return {
        "data": {
            "id": str(event.id),
            "title": event.title,
            "status": event.status,
        },
        "message": f"Estado actualizado a '{status}'"
    }


# ============================================================================
# STATISTICS
# ============================================================================

@router.get("/stats")
async def get_calendar_stats(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Obtener estadísticas del calendario de una empresa.

    - **company_id**: ID de la empresa
    """
    today = date.today()

    # Eventos pendientes
    pending_query = select(CalendarEvent).where(
        and_(
            CalendarEvent.company_id == company_id,
            CalendarEvent.status == "pending"
        )
    )
    pending_result = await db.execute(pending_query)
    pending_events = pending_result.scalars().all()

    # Eventos vencidos
    overdue_query = select(CalendarEvent).where(
        and_(
            CalendarEvent.company_id == company_id,
            CalendarEvent.due_date < today,
            CalendarEvent.status.in_(["pending", "in_progress"])
        )
    )
    overdue_result = await db.execute(overdue_query)
    overdue_events = overdue_result.scalars().all()

    # Próximos 7 días
    next_week = today + timedelta(days=7)
    upcoming_query = select(CalendarEvent).where(
        and_(
            CalendarEvent.company_id == company_id,
            CalendarEvent.due_date >= today,
            CalendarEvent.due_date <= next_week,
            CalendarEvent.status.in_(["pending", "in_progress"])
        )
    )
    upcoming_result = await db.execute(upcoming_query)
    upcoming_events = upcoming_result.scalars().all()

    # Eventos completados este mes
    month_start = today.replace(day=1)
    completed_query = select(CalendarEvent).where(
        and_(
            CalendarEvent.company_id == company_id,
            CalendarEvent.status == "completed",
            CalendarEvent.completion_date >= month_start
        )
    )
    completed_result = await db.execute(completed_query)
    completed_events = completed_result.scalars().all()

    return {
        "data": {
            "pending": len(pending_events),
            "overdue": len(overdue_events),
            "upcoming_7_days": len(upcoming_events),
            "completed_this_month": len(completed_events),
            "today": today.isoformat(),
        }
    }


# ============================================================================
# EVENT HISTORY
# ============================================================================

class CreateEventHistoryRequest(BaseModel):
    event_type: str
    title: str
    description: Optional[str] = None
    metadata: Optional[dict] = None


@router.get("/events/{event_id}/history")
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
    # Verificar que el evento existe y el usuario tiene acceso
    event_result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id)
    )
    event = event_result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    # Obtener historial
    history_query = select(EventHistory).where(
        EventHistory.calendar_event_id == event_id
    ).order_by(EventHistory.created_at.desc()).limit(limit)

    history_result = await db.execute(history_query)
    history_entries = history_result.scalars().all()

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


@router.post("/events/{event_id}/history")
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

    # Verificar que el evento existe
    event_result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == event_id)
    )
    event = event_result.scalar_one_or_none()

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

    db.add(history_entry)
    await db.commit()
    # No refresh needed - all data is in memory (created_at is auto-generated but available)

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

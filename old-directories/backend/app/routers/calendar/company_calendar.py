"""REST API endpoints for company calendar configuration and management."""

import logging
import time
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...config.database import get_db
from ...db.models import CalendarEvent, Company, CompanyEvent, EventTemplate, Profile, Session as SessionModel
from ...dependencies import get_current_user_id, require_auth

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["company-calendar"],
    dependencies=[Depends(require_auth)]
)


# ============================================================================
# Request/Response Models
# ============================================================================

class ActivateEventRequest(BaseModel):
    """Request para activar un evento para una empresa"""
    event_template_id: UUID
    custom_config: Optional[dict] = None  # Opcional: overrides solo para casos edge


class CalendarEventInfo(BaseModel):
    """Calendar event information"""
    id: str
    title: str
    description: Optional[str]
    event_template_code: str
    event_template_name: str
    category: str
    due_date: date
    period_start: Optional[date]
    period_end: Optional[date]
    status: str
    completion_date: Optional[datetime]
    completion_data: Optional[dict]
    auto_generated: bool
    created_at: datetime


# ============================================================================
# Calendar Configuration Endpoints
# ============================================================================

@router.get("/companies/{company_id}/calendar-config")
async def get_company_calendar_config(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Obtiene la configuración de eventos tributarios para una empresa.

    Retorna:
    - Todos los event types disponibles
    - Cuáles están activos para esta empresa
    - Configuración de recurrencia personalizada
    """
    import asyncio

    start_time = time.time()
    logger.info(f"[PERF] START get calendar config for company {company_id}")

    # Verificar empresa
    company_stmt = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_stmt)
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    logger.info(f"[PERF] Company query took {(time.time() - start_time)*1000:.2f}ms")

    # Obtener todos los templates y los company_events de esta empresa en paralelo
    templates_start = time.time()
    event_templates_stmt = select(EventTemplate).order_by(EventTemplate.category, EventTemplate.name)
    rules_stmt = select(CompanyEvent).where(CompanyEvent.company_id == company_id)

    # Ejecutar ambas queries en paralelo
    templates_result, rules_result = await asyncio.gather(
        db.execute(event_templates_stmt),
        db.execute(rules_stmt)
    )

    all_event_templates = templates_result.scalars().all()
    active_rules = {rule.event_template_id: rule for rule in rules_result.scalars().all()}

    logger.info(f"[PERF] Templates + rules query took {(time.time() - templates_start)*1000:.2f}ms")

    # Construir respuesta
    build_start = time.time()
    event_templates_config = []
    total_active = 0

    for event_template in all_event_templates:
        company_event = active_rules.get(event_template.id)
        is_active = company_event is not None and company_event.is_active
        if is_active:
            total_active += 1

        event_templates_config.append({
            "event_template_id": str(event_template.id),
            "code": event_template.code,
            "name": event_template.name,
            "description": event_template.description,
            "category": event_template.category,
            "authority": event_template.authority,
            "is_mandatory": event_template.is_mandatory,
            "default_recurrence": event_template.default_recurrence,
            "is_active": is_active,
            "company_event_id": str(company_event.id) if company_event else None,
            "custom_config": company_event.custom_config if company_event else {},
        })

    logger.info(f"[PERF] Build response took {(time.time() - build_start)*1000:.2f}ms")
    logger.info(f"[PERF] TOTAL get calendar config took {(time.time() - start_time)*1000:.2f}ms")

    return {
        "company_id": str(company_id),
        "company_name": company.business_name,
        "event_templates": event_templates_config,
        "total_available": len(event_templates_config),
        "total_active": total_active
    }


@router.post("/companies/{company_id}/calendar-config/activate")
async def activate_event_for_company(
    company_id: UUID,
    request: ActivateEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Activa un tipo de evento tributario para una empresa.

    Crea o actualiza un CompanyEvent vinculando el evento a la empresa.

    Este endpoint delega la lógica de negocio a CalendarService.
    """
    from app.services.calendar import CalendarService

    start_time = time.time()
    logger.info(
        f"[PERF] START activate event {request.event_template_id} "
        f"for company {company_id} by user {current_user_id}"
    )

    try:
        # Delegar a la capa de servicio
        service = CalendarService(db)
        result = await service.activate_event(
            company_id=company_id,
            event_template_id=request.event_template_id,
            custom_config=request.custom_config
        )

        logger.info(
            f"[PERF] TOTAL activate took {(time.time() - start_time)*1000:.2f}ms - "
            f"{result['action']}"
        )

        return result

    except ValueError as e:
        # Event template no existe
        logger.error(f"Activate event validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Activate event failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al activar evento: {str(e)}"
        )


@router.post("/companies/{company_id}/calendar-config/deactivate")
async def deactivate_event_for_company(
    company_id: UUID,
    request: ActivateEventRequest,  # Solo usamos event_template_id
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Desactiva un tipo de evento tributario para una empresa.

    Marca el CompanyEvent como inactivo (no lo elimina para mantener historial).

    Este endpoint delega la lógica de negocio a CalendarService.
    """
    from app.services.calendar import CalendarService

    start_time = time.time()
    logger.info(
        f"[PERF] START deactivate event {request.event_template_id} "
        f"for company {company_id} by user {current_user_id}"
    )

    try:
        # Delegar a la capa de servicio
        service = CalendarService(db)
        result = await service.deactivate_event(
            company_id=company_id,
            event_template_id=request.event_template_id
        )

        logger.info(
            f"[PERF] TOTAL deactivate took {(time.time() - start_time)*1000:.2f}ms"
        )

        return result

    except ValueError as e:
        # Company event no existe
        logger.error(f"Deactivate event validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Deactivate event failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desactivar evento: {str(e)}"
        )


@router.post("/companies/{company_id}/sync-calendar")
async def sync_calendar_events(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Sincroniza el calendario de eventos tributarios para una empresa.

    IMPORTANTE: Este endpoint es idempotente. Puede ejecutarse múltiples veces sin duplicar eventos.
    Solo sincroniza eventos para los company_events activos (is_active=true).

    Este endpoint delega la lógica de negocio a CalendarService:
    1. Verifica que la empresa existe
    2. Obtiene los vínculos empresa-evento activos (company_events)
    3. Para cada tipo de evento (F29, F22, etc.):
       - Crea eventos faltantes para los próximos periodos
       - Actualiza el estado de eventos existentes
       - Solo el próximo a vencer queda con estado 'in_progress'
       - Los demás quedan con estado 'saved'
    4. No modifica eventos completados o cancelados

    Args:
        company_id: UUID de la empresa

    Returns:
        Resumen de eventos creados y actualizados
    """
    from app.services.calendar import CalendarService

    logger.info(f"Calendar sync requested for company {company_id} by user {current_user_id}")

    try:
        # Delegar a la capa de servicio
        service = CalendarService(db)
        result = await service.sync_company_calendar(company_id=company_id)

        logger.info(
            f"Calendar sync completed for company {company_id}: "
            f"{result['total_created']} created, {result['total_updated']} updated"
        )

        return result

    except ValueError as e:
        # Empresa no existe o no tiene eventos activos
        logger.error(f"Calendar sync validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Calendar sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al sincronizar calendario: {str(e)}"
        )


@router.get("/company/{company_id}/calendar-events", response_model=List[CalendarEventInfo])
async def get_company_calendar_events(
    company_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """
    Get calendar events for a company.

    Returns all CalendarEvent records for the specified company.
    Can be filtered by date range and status.

    Args:
        company_id: Company UUID
        current_user_id: Authenticated user ID
        db: Database session
        start_date: Optional start date filter
        end_date: Optional end date filter
        status: Optional status filter (pending, in_progress, completed, overdue, cancelled)
        limit: Maximum number of results (default 100, max 500)

    Returns:
        List of CalendarEventInfo

    Raises:
        404: Company not found
        403: User doesn't have access to this company
    """
    logger.info(f"Calendar events requested for company {company_id} by user {current_user_id}")

    # Check user role and access permissions
    user_stmt = select(Profile).where(Profile.id == current_user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    is_admin = user.rol == "admin-kaiken"

    # If not admin, check if user has access to this company
    if not is_admin:
        session_check_stmt = select(SessionModel).where(
            SessionModel.user_id == current_user_id,
            SessionModel.company_id == company_id
        )
        session_check = await db.execute(session_check_stmt)
        if not session_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )

    # Verify company exists
    company_stmt = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_stmt)
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company {company_id} not found"
        )

    # Build calendar events query
    events_stmt = select(CalendarEvent).options(
        selectinload(CalendarEvent.event_template)
    ).where(
        CalendarEvent.company_id == company_id
    ).order_by(
        CalendarEvent.due_date
    )

    # Apply filters
    if start_date:
        events_stmt = events_stmt.where(CalendarEvent.due_date >= start_date)

    if end_date:
        events_stmt = events_stmt.where(CalendarEvent.due_date <= end_date)

    if status:
        events_stmt = events_stmt.where(CalendarEvent.status == status)

    events_stmt = events_stmt.limit(limit)

    result = await db.execute(events_stmt)
    calendar_events = result.scalars().all()

    return [
        CalendarEventInfo(
            id=str(event.id),
            title=event.event_template.name,
            description=event.event_template.description,
            event_template_code=event.event_template.code,
            event_template_name=event.event_template.name,
            category=event.event_template.category,
            due_date=event.due_date,
            period_start=event.period_start,
            period_end=event.period_end,
            status=event.status,
            completion_date=event.completion_date,
            completion_data=event.completion_data,
            auto_generated=event.auto_generated,
            created_at=event.created_at
        )
        for event in calendar_events
    ]

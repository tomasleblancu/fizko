"""REST API endpoints for company event (rules) management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import CompanyEvent
from ...dependencies import get_current_user_id, require_auth
from ...repositories.calendar import CalendarRepository

router = APIRouter(
    prefix="/rules",
    tags=["calendar-rules"],
    dependencies=[Depends(require_auth)]
)


@router.get("")
async def list_company_events(
    company_id: UUID,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Obtener vínculos empresa-evento configurados para una empresa.

    - **company_id**: ID de la empresa
    - **is_active**: Filtrar por eventos activos (true) o inactivos (false)
    """
    repo = CalendarRepository(db)
    company_events = await repo.get_company_events(company_id, is_active)

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


@router.post("")
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
    repo = CalendarRepository(db)

    # Verificar que el event_template existe
    event_template = await repo.get_event_template_by_code(event_template_code)
    if not event_template:
        raise HTTPException(status_code=404, detail=f"Template de evento '{event_template_code}' no encontrado")

    # Verificar que la empresa existe
    company = await repo.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    # Verificar que no existe ya este vínculo
    existing_company_event = await repo.get_company_event_by_company_and_template(
        company_id,
        event_template.id
    )
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

    new_company_event = await repo.create_company_event(new_company_event)

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


@router.patch("/{company_event_id}")
async def update_company_event(
    company_event_id: UUID,
    is_active: bool | None = None,
    custom_config: dict | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Actualizar configuración de un vínculo empresa-evento."""
    repo = CalendarRepository(db)

    company_event = await repo.get_company_event_by_id(company_event_id)
    if not company_event:
        raise HTTPException(status_code=404, detail="Vínculo empresa-evento no encontrado")

    # Actualizar campos proporcionados
    if is_active is not None:
        company_event.is_active = is_active
    if custom_config is not None:
        company_event.custom_config = custom_config

    company_event = await repo.update_company_event(company_event)

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

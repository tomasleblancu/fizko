"""REST API endpoints for event template management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import EventTemplate
from ...dependencies import get_current_user_id, require_auth
from ...repositories.calendar import CalendarRepository
from ...schemas.calendar import CreateEventTemplateRequest, UpdateEventTemplateRequest

router = APIRouter(
    prefix="/event-templates",
    tags=["calendar-templates"],
    dependencies=[Depends(require_auth)]
)


@router.get("")
async def list_event_templates(
    category: str | None = None,
    is_mandatory: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Obtener catálogo de tipos de eventos tributarios.

    - **category**: Filtrar por categoría (impuesto_mensual, impuesto_anual, prevision, etc.)
    - **is_mandatory**: Filtrar por obligatorios (true) u opcionales (false)
    """
    repo = CalendarRepository(db)
    event_templates = await repo.get_event_templates(category, is_mandatory)

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


@router.get("/{event_template_id}")
async def get_event_template(
    event_template_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtener detalle de un tipo de evento."""
    repo = CalendarRepository(db)
    event_template = await repo.get_event_template_by_id(event_template_id)

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


@router.post("")
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
    repo = CalendarRepository(db)

    # Verificar que el código no existe
    existing = await repo.get_event_template_by_code(request.code)
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

    new_event_template = await repo.create_event_template(new_event_template)

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


@router.delete("/{event_template_id}")
async def delete_event_template(
    event_template_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Eliminar un tipo de evento.

    ADVERTENCIA: Esto eliminará todas las reglas y eventos asociados.
    """
    repo = CalendarRepository(db)

    # Buscar el event_template
    event_template = await repo.get_event_template_by_id(event_template_id)
    if not event_template:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")

    # Verificar si hay reglas activas asociadas
    active_rules = await repo.get_active_company_events_by_template(event_template_id)
    if active_rules:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar. Hay {len(active_rules)} empresa(s) con este evento activo. Desactiva primero todas las reglas."
        )

    # Eliminar event_template (las FK con CASCADE eliminarán reglas y eventos)
    await repo.delete_event_template(event_template)

    return {
        "message": f"Tipo de evento '{event_template.name}' eliminado exitosamente"
    }


@router.put("/{event_template_id}")
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
    repo = CalendarRepository(db)

    # Buscar el event_template
    event_template = await repo.get_event_template_by_id(event_template_id)
    if not event_template:
        raise HTTPException(status_code=404, detail="Tipo de evento no encontrado")

    # Si se intenta cambiar el código, verificar que no exista
    if request.code and request.code != event_template.code:
        existing = await repo.get_event_template_by_code(request.code)
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

    event_template = await repo.update_event_template(event_template)

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

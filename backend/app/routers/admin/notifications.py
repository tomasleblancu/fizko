"""REST API endpoints for notification template management (Admin)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import NotificationTemplate, NotificationSubscription
from ...dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/notifications",
    tags=["notifications-admin"],
    dependencies=[Depends(require_auth)]
)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CreateNotificationTemplateRequest(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    category: str
    entity_type: Optional[str] = None
    message_template: str
    timing_config: dict
    priority: str = "normal"
    is_active: bool = True
    metadata: Optional[dict] = None


class UpdateNotificationTemplateRequest(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    entity_type: Optional[str] = None
    message_template: Optional[str] = None
    timing_config: Optional[dict] = None
    priority: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


# ============================================================================
# NOTIFICATION TEMPLATES (Admin CRUD)
# ============================================================================

@router.get("/notification-templates")
async def list_notification_templates(
    category: Optional[str] = None,
    entity_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Obtener catálogo de templates de notificaciones.

    - **category**: Filtrar por categoría (calendar, tax_document, payroll, system, custom)
    - **entity_type**: Filtrar por tipo de entidad (calendar_event, form29, etc.)
    - **is_active**: Filtrar por activos/inactivos
    """
    query = select(NotificationTemplate)

    if category:
        query = query.where(NotificationTemplate.category == category)
    if entity_type:
        query = query.where(NotificationTemplate.entity_type == entity_type)
    if is_active is not None:
        query = query.where(NotificationTemplate.is_active == is_active)

    query = query.order_by(NotificationTemplate.category, NotificationTemplate.name)

    result = await db.execute(query)
    templates = result.scalars().all()

    return {
        "data": [
            {
                "id": str(t.id),
                "code": t.code,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "entity_type": t.entity_type,
                "message_template": t.message_template,
                "timing_config": t.timing_config,
                "priority": t.priority,
                "is_active": t.is_active,
                "metadata": t.extra_metadata,
            }
            for t in templates
        ],
        "total": len(templates)
    }


@router.get("/notification-templates/{template_id}")
async def get_notification_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtener detalle de un template de notificación."""
    result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template de notificación no encontrado")

    return {
        "data": {
            "id": str(template.id),
            "code": template.code,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "entity_type": template.entity_type,
            "message_template": template.message_template,
            "timing_config": template.timing_config,
            "priority": template.priority,
            "is_active": template.is_active,
            "metadata": template.extra_metadata,
        }
    }


@router.post("/notification-templates")
async def create_notification_template(
    request: CreateNotificationTemplateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Crear un nuevo template de notificación.

    - **code**: Código único del template (ej: custom_reminder)
    - **name**: Nombre descriptivo
    - **category**: Categoría (calendar, tax_document, payroll, system, custom)
    - **entity_type**: Tipo de entidad relacionada (opcional)
    - **message_template**: Template del mensaje con variables {{variable}}
    - **timing_config**: Configuración de timing (tipo: relative/absolute/immediate)
    - **priority**: Prioridad (low, normal, high, urgent)
    - **is_active**: Si está activo
    - **metadata**: Metadatos adicionales (opcional)
    """
    # Verificar que el código no existe
    result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.code == request.code)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un template con el código '{request.code}'"
        )

    # Crear nuevo template
    new_template = NotificationTemplate(
        code=request.code,
        name=request.name,
        description=request.description,
        category=request.category,
        entity_type=request.entity_type,
        message_template=request.message_template,
        timing_config=request.timing_config,
        priority=request.priority,
        is_active=request.is_active,
        extra_metadata=request.metadata or {},
    )

    db.add(new_template)
    await db.commit()

    return {
        "data": {
            "id": str(new_template.id),
            "code": new_template.code,
            "name": new_template.name,
            "description": new_template.description,
            "category": new_template.category,
            "entity_type": new_template.entity_type,
            "message_template": new_template.message_template,
            "timing_config": new_template.timing_config,
            "priority": new_template.priority,
            "is_active": new_template.is_active,
            "metadata": new_template.extra_metadata,
        },
        "message": "Template de notificación creado exitosamente"
    }


@router.delete("/notification-templates/{template_id}")
async def delete_notification_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Eliminar un template de notificación.

    ADVERTENCIA: Esto eliminará todas las suscripciones asociadas.
    """
    # Buscar el template
    result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template de notificación no encontrado")

    # Verificar si hay suscripciones activas asociadas
    result = await db.execute(
        select(NotificationSubscription).where(
            NotificationSubscription.notification_template_id == template_id
        )
    )
    active_subscriptions = result.scalars().all()

    if active_subscriptions:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar. Hay {len(active_subscriptions)} suscripción(es) a este template. Elimina primero las suscripciones."
        )

    # Eliminar template
    await db.delete(template)
    await db.commit()

    return {
        "message": f"Template '{template.name}' eliminado exitosamente"
    }


@router.put("/notification-templates/{template_id}")
async def update_notification_template(
    template_id: UUID,
    request: UpdateNotificationTemplateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Actualizar un template de notificación.

    - Solo se actualizan los campos proporcionados
    - Si se cambia el código, verifica que no exista otro template con ese código
    """
    # Buscar el template
    result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template de notificación no encontrado")

    # Si se intenta cambiar el código, verificar que no exista
    if request.code and request.code != template.code:
        result = await db.execute(
            select(NotificationTemplate).where(NotificationTemplate.code == request.code)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un template con el código '{request.code}'"
            )

    # Actualizar solo los campos proporcionados
    if request.code is not None:
        template.code = request.code
    if request.name is not None:
        template.name = request.name
    if request.description is not None:
        template.description = request.description
    if request.category is not None:
        template.category = request.category
    if request.entity_type is not None:
        template.entity_type = request.entity_type
    if request.message_template is not None:
        template.message_template = request.message_template
    if request.timing_config is not None:
        template.timing_config = request.timing_config
    if request.priority is not None:
        template.priority = request.priority
    if request.is_active is not None:
        template.is_active = request.is_active
    if request.metadata is not None:
        template.extra_metadata = request.metadata

    await db.commit()

    return {
        "data": {
            "id": str(template.id),
            "code": template.code,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "entity_type": template.entity_type,
            "message_template": template.message_template,
            "timing_config": template.timing_config,
            "priority": template.priority,
            "is_active": template.is_active,
            "metadata": template.extra_metadata,
        },
        "message": "Template de notificación actualizado exitosamente"
    }

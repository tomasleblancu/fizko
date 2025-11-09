"""REST API endpoints for notification template management (Admin)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id
from ...schemas.notifications import CreateNotificationTemplateRequest, UpdateNotificationTemplateRequest

router = APIRouter()


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

    Delega a NotificationService.

    - **category**: Filtrar por categoría (calendar, tax_document, payroll, system, custom)
    - **entity_type**: Filtrar por tipo de entidad (calendar_event, form29, etc.)
    - **is_active**: Filtrar por activos/inactivos
    """
    from app.services.notifications import get_notification_service

    notification_service = get_notification_service()
    templates = await notification_service.list_templates(
        db=db,
        category=category,
        entity_type=entity_type,
        is_active=is_active
    )

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
                "auto_assign_to_new_companies": t.auto_assign_to_new_companies,
                "metadata": t.extra_metadata,
                "whatsapp_template_id": t.whatsapp_template_id,
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
    """
    Obtener detalle de un template de notificación.

    Delega a NotificationService.
    """
    from app.services.notifications import get_notification_service

    notification_service = get_notification_service()
    template = await notification_service.get_template(db=db, template_id=template_id)

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
            "auto_assign_to_new_companies": template.auto_assign_to_new_companies,
            "metadata": template.extra_metadata,
            "whatsapp_template_id": template.whatsapp_template_id,
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

    Delega a NotificationService.

    - **code**: Código único del template (ej: custom_reminder)
    - **name**: Nombre descriptivo
    - **category**: Categoría (calendar, tax_document, payroll, system, custom)
    - **entity_type**: Tipo de entidad relacionada (opcional)
    - **message_template**: Template del mensaje con variables {{variable}}
    - **timing_config**: Configuración de timing (tipo: relative/absolute/immediate)
    - **priority**: Prioridad (low, normal, high, urgent)
    - **is_active**: Si está activo
    - **metadata**: Metadatos adicionales (opcional)
    - **whatsapp_template_id**: ID del template de WhatsApp creado manualmente en Meta Business Manager (opcional)
    """
    from app.services.notifications import get_notification_service

    notification_service = get_notification_service()

    try:
        new_template = await notification_service.create_template(
            db=db,
            code=request.code,
            name=request.name,
            category=request.category,
            message_template=request.message_template,
            timing_config=request.timing_config,
            description=request.description,
            entity_type=request.entity_type,
            priority=request.priority,
            is_active=request.is_active,
            auto_assign_to_new_companies=request.auto_assign_to_new_companies,
            metadata=request.metadata,
            whatsapp_template_id=request.whatsapp_template_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

    # Build response
    response_data = {
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
        "auto_assign_to_new_companies": new_template.auto_assign_to_new_companies,
        "metadata": new_template.extra_metadata,
        "whatsapp_template_id": new_template.whatsapp_template_id,
    }

    return {
        "data": response_data,
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

    Delega a NotificationService.

    ADVERTENCIA: Esto eliminará todas las suscripciones asociadas.
    """
    from app.services.notifications import get_notification_service

    notification_service = get_notification_service()

    try:
        await notification_service.delete_template(db=db, template_id=template_id)
    except ValueError as e:
        if "no encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))

    return {
        "message": "Template eliminado exitosamente"
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

    Delega a NotificationService.

    - Solo se actualizan los campos proporcionados
    - Si se cambia el código, verifica que no exista otro template con ese código
    """
    from app.services.notifications import get_notification_service

    notification_service = get_notification_service()

    try:
        template = await notification_service.update_template(
            db=db,
            template_id=template_id,
            code=request.code,
            name=request.name,
            description=request.description,
            category=request.category,
            entity_type=request.entity_type,
            message_template=request.message_template,
            timing_config=request.timing_config,
            priority=request.priority,
            is_active=request.is_active,
            auto_assign_to_new_companies=request.auto_assign_to_new_companies,
            metadata=request.metadata,
            whatsapp_template_id=request.whatsapp_template_id,
        )
    except ValueError as e:
        if "no encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))

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
            "auto_assign_to_new_companies": template.auto_assign_to_new_companies,
            "metadata": template.extra_metadata,
            "whatsapp_template_id": template.whatsapp_template_id,
        },
        "message": "Template de notificación actualizado exitosamente"
    }

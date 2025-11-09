"""REST API endpoints for notification subscription management (Admin)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id
from ...repositories import NotificationTemplateRepository, NotificationSubscriptionRepository
from ...db.models import NotificationSubscription

router = APIRouter()


# ============================================================================
# NOTIFICATION SUBSCRIPTIONS
# ============================================================================

@router.get("/company/{company_id}/notification-subscriptions")
async def get_company_notification_subscriptions(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user_id)
):
    """
    Obtener todas las suscripciones de notificaciones de una empresa.

    Returns:
        Dict with list of subscriptions including template information
    """
    subscription_repo = NotificationSubscriptionRepository(db)

    subscriptions = await subscription_repo.find_by_company_with_templates(company_id)

    subscriptions_data = []
    for subscription, template in subscriptions:
        subscriptions_data.append({
            "id": str(subscription.id),
            "notification_template_id": str(subscription.notification_template_id),
            "is_enabled": subscription.is_enabled,
            "custom_timing_config": subscription.custom_timing_config,
            "custom_message_template": subscription.custom_message_template,
            "created_at": subscription.created_at.isoformat(),
            "template": {
                "id": str(template.id),
                "code": template.code,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "entity_type": template.entity_type,
                "is_active": template.is_active,
            }
        })

    return {"data": subscriptions_data}


@router.post("/company/{company_id}/notification-subscriptions")
async def create_company_notification_subscription(
    company_id: UUID,
    notification_template_id: UUID = Body(...),
    is_enabled: bool = Body(True),
    custom_timing_config: Optional[dict] = Body(None),
    custom_message_template: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user_id)
):
    """
    Crear una nueva suscripción de notificación para una empresa.

    Args:
        company_id: Company UUID
        notification_template_id: Template UUID to subscribe to
        is_enabled: Whether subscription is enabled
        custom_timing_config: Optional custom timing configuration
        custom_message_template: Optional custom message template

    Returns:
        Dict with created subscription data

    Raises:
        404: Template not found
        400: Subscription already exists
    """
    template_repo = NotificationTemplateRepository(db)
    subscription_repo = NotificationSubscriptionRepository(db)

    # Verificar que el template existe
    template = await template_repo.get(notification_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template de notificación no encontrado")

    # Verificar si ya existe una suscripción
    existing = await subscription_repo.find_by_company_and_template(
        company_id=company_id,
        template_id=notification_template_id,
        enabled_only=False
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una suscripción a este template para esta empresa"
        )

    # Crear suscripción
    subscription = NotificationSubscription(
        company_id=company_id,
        notification_template_id=notification_template_id,
        is_enabled=is_enabled,
        custom_timing_config=custom_timing_config,
        custom_message_template=custom_message_template
    )

    created = await subscription_repo.create(subscription)

    return {
        "data": {
            "id": str(created.id),
            "notification_template_id": str(created.notification_template_id),
            "is_enabled": created.is_enabled,
            "custom_timing_config": created.custom_timing_config,
            "custom_message_template": created.custom_message_template,
            "created_at": created.created_at.isoformat(),
        },
        "message": "Suscripción creada exitosamente"
    }


@router.put("/company/{company_id}/notification-subscriptions/{subscription_id}")
async def update_company_notification_subscription(
    company_id: UUID,
    subscription_id: UUID,
    is_enabled: Optional[bool] = Body(None),
    custom_timing_config: Optional[dict] = Body(None),
    custom_message_template: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user_id)
):
    """
    Actualizar una suscripción de notificación.

    Args:
        company_id: Company UUID
        subscription_id: Subscription UUID
        is_enabled: Optional new enabled status
        custom_timing_config: Optional new timing configuration
        custom_message_template: Optional new message template

    Returns:
        Dict with updated subscription data

    Raises:
        404: Subscription not found
    """
    subscription_repo = NotificationSubscriptionRepository(db)

    subscription = await subscription_repo.find_by_company_and_subscription_id(
        company_id=company_id,
        subscription_id=subscription_id
    )

    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")

    # Actualizar campos
    if is_enabled is not None:
        subscription.is_enabled = is_enabled
    if custom_timing_config is not None:
        subscription.custom_timing_config = custom_timing_config
    if custom_message_template is not None:
        subscription.custom_message_template = custom_message_template

    updated = await subscription_repo.update(subscription)

    return {
        "data": {
            "id": str(updated.id),
            "notification_template_id": str(updated.notification_template_id),
            "is_enabled": updated.is_enabled,
            "custom_timing_config": updated.custom_timing_config,
            "custom_message_template": updated.custom_message_template,
        },
        "message": "Suscripción actualizada exitosamente"
    }


@router.delete("/company/{company_id}/notification-subscriptions/{subscription_id}")
async def delete_company_notification_subscription(
    company_id: UUID,
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UUID = Depends(get_current_user_id)
):
    """
    Eliminar una suscripción de notificación.

    Args:
        company_id: Company UUID
        subscription_id: Subscription UUID

    Returns:
        Dict with success message

    Raises:
        404: Subscription not found
    """
    subscription_repo = NotificationSubscriptionRepository(db)

    subscription = await subscription_repo.find_by_company_and_subscription_id(
        company_id=company_id,
        subscription_id=subscription_id
    )

    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")

    await subscription_repo.delete(subscription_id)

    return {"message": "Suscripción eliminada exitosamente"}

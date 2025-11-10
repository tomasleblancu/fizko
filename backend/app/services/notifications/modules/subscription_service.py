"""
Subscription management service for notifications
Handles company subscriptions to notification templates
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationSubscription
from app.repositories import (
    NotificationTemplateRepository,
    NotificationSubscriptionRepository,
)
from .base_service import BaseNotificationService

logger = logging.getLogger(__name__)


class SubscriptionService(BaseNotificationService):
    """
    Service for managing notification subscriptions.
    Handles company subscriptions to notification templates using repository pattern.
    """

    async def subscribe_company(
        self,
        db: AsyncSession,
        company_id: UUID,
        template_id: UUID,
        custom_timing: Optional[Dict] = None,
        custom_message: Optional[str] = None,
        is_enabled: bool = True,
    ) -> NotificationSubscription:
        """
        Subscribe a company to a notification template.

        Args:
            db: Database session
            company_id: Company ID
            template_id: Template ID
            custom_timing: Custom timing configuration (optional)
            custom_message: Custom message template (optional)
            is_enabled: Whether subscription is active

        Returns:
            Created or updated NotificationSubscription

        Raises:
            HTTPException: If template not found or subscription already exists
        """
        template_repo = NotificationTemplateRepository(db)
        subscription_repo = NotificationSubscriptionRepository(db)

        # Verify template exists
        template = await template_repo.get(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template de notificación no encontrado")

        # Check if subscription already exists
        existing = await subscription_repo.find_by_company_and_template(
            company_id=company_id,
            template_id=template_id,
            enabled_only=False
        )

        if existing:
            # Update existing subscription
            existing.is_enabled = is_enabled
            if custom_timing:
                existing.custom_timing_config = custom_timing
            if custom_message:
                existing.custom_message_template = custom_message
            existing.updated_at = datetime.utcnow()

            updated = await subscription_repo.update(existing)
            logger.info(f"✅ Company {company_id} subscription updated for template {template_id}")
            return updated
        else:
            # Create new subscription
            subscription = NotificationSubscription(
                company_id=company_id,
                notification_template_id=template_id,
                custom_timing_config=custom_timing,
                custom_message_template=custom_message,
                is_enabled=is_enabled,
            )

            created = await subscription_repo.create(subscription)
            logger.info(f"✅ Company {company_id} subscribed to template {template_id}")
            return created

    async def create_subscription(
        self,
        db: AsyncSession,
        company_id: UUID,
        template_id: UUID,
        is_enabled: bool = True,
        custom_timing_config: Optional[dict] = None,
        custom_message_template: Optional[str] = None,
    ) -> NotificationSubscription:
        """
        Create a new subscription (strict - raises error if already exists).

        Args:
            db: Database session
            company_id: Company ID
            template_id: Template ID
            is_enabled: Whether subscription is active
            custom_timing_config: Custom timing configuration
            custom_message_template: Custom message template

        Returns:
            Created NotificationSubscription

        Raises:
            HTTPException: If template not found or subscription already exists
        """
        template_repo = NotificationTemplateRepository(db)
        subscription_repo = NotificationSubscriptionRepository(db)

        # Verify template exists
        template = await template_repo.get(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template de notificación no encontrado")

        # Check if subscription already exists
        existing = await subscription_repo.find_by_company_and_template(
            company_id=company_id,
            template_id=template_id,
            enabled_only=False
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una suscripción a este template para esta empresa"
            )

        # Create new subscription
        subscription = NotificationSubscription(
            company_id=company_id,
            notification_template_id=template_id,
            is_enabled=is_enabled,
            custom_timing_config=custom_timing_config,
            custom_message_template=custom_message_template
        )

        created = await subscription_repo.create(subscription)
        logger.info(f"✅ Company {company_id} subscribed to template {template_id}")
        return created

    async def get_company_subscriptions_with_templates(
        self,
        db: AsyncSession,
        company_id: UUID,
    ) -> List[Tuple]:
        """
        Get company subscriptions with template information.

        Args:
            db: Database session
            company_id: Company ID

        Returns:
            List of (subscription, template) tuples
        """
        subscription_repo = NotificationSubscriptionRepository(db)
        return await subscription_repo.find_by_company_with_templates(company_id)

    async def update_subscription(
        self,
        db: AsyncSession,
        company_id: UUID,
        subscription_id: UUID,
        is_enabled: Optional[bool] = None,
        custom_timing_config: Optional[dict] = None,
        custom_message_template: Optional[str] = None,
    ) -> NotificationSubscription:
        """
        Update a subscription.

        Args:
            db: Database session
            company_id: Company ID
            subscription_id: Subscription ID
            is_enabled: New enabled status
            custom_timing_config: New timing configuration
            custom_message_template: New message template

        Returns:
            Updated NotificationSubscription

        Raises:
            HTTPException: If subscription not found
        """
        subscription_repo = NotificationSubscriptionRepository(db)

        # Find subscription
        subscription = await subscription_repo.find_by_company_and_subscription_id(
            company_id=company_id,
            subscription_id=subscription_id
        )

        if not subscription:
            raise HTTPException(status_code=404, detail="Suscripción no encontrada")

        # Update fields
        if is_enabled is not None:
            subscription.is_enabled = is_enabled
        if custom_timing_config is not None:
            subscription.custom_timing_config = custom_timing_config
        if custom_message_template is not None:
            subscription.custom_message_template = custom_message_template

        updated = await subscription_repo.update(subscription)
        logger.info(f"✅ Updated subscription {subscription_id} for company {company_id}")
        return updated

    async def delete_subscription(
        self,
        db: AsyncSession,
        company_id: UUID,
        subscription_id: UUID,
    ) -> bool:
        """
        Delete a subscription.

        Args:
            db: Database session
            company_id: Company ID
            subscription_id: Subscription ID

        Returns:
            True if deleted

        Raises:
            HTTPException: If subscription not found
        """
        subscription_repo = NotificationSubscriptionRepository(db)

        # Find subscription
        subscription = await subscription_repo.find_by_company_and_subscription_id(
            company_id=company_id,
            subscription_id=subscription_id
        )

        if not subscription:
            raise HTTPException(status_code=404, detail="Suscripción no encontrada")

        await subscription_repo.delete(subscription_id)
        logger.info(f"🗑️ Deleted subscription {subscription_id} for company {company_id}")
        return True

    async def unsubscribe_company(
        self,
        db: AsyncSession,
        company_id: UUID,
        template_id: UUID,
    ) -> bool:
        """
        Unsubscribe a company from a notification template.

        Args:
            db: Database session
            company_id: Company ID
            template_id: Template ID

        Returns:
            True if successfully unsubscribed
        """
        subscription_repo = NotificationSubscriptionRepository(db)

        subscription = await subscription_repo.find_by_company_and_template(
            company_id=company_id,
            template_id=template_id,
            enabled_only=False
        )

        if subscription:
            subscription.is_enabled = False
            subscription.updated_at = datetime.utcnow()
            await subscription_repo.update(subscription)
            logger.info(f"🔕 Company {company_id} unsubscribed from template {template_id}")
            return True

        return False

    async def get_company_subscriptions(
        self,
        db: AsyncSession,
        company_id: UUID,
        is_enabled: Optional[bool] = None,
    ) -> List[NotificationSubscription]:
        """
        Get a company's notification subscriptions.

        Args:
            db: Database session
            company_id: Company ID
            is_enabled: Filter by enabled status (optional)

        Returns:
            List of subscriptions
        """
        subscription_repo = NotificationSubscriptionRepository(db)
        return await subscription_repo.find_by_company(
            company_id=company_id,
            enabled_only=is_enabled
        )

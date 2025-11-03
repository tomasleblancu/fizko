"""
Subscription management service for notifications
Handles company subscriptions to notification templates
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationSubscription
from .base_service import BaseNotificationService

logger = logging.getLogger(__name__)


class SubscriptionService(BaseNotificationService):
    """
    Service for managing notification subscriptions.
    Handles company subscriptions to notification templates.
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
        """
        # Check if already exists
        result = await db.execute(
            select(NotificationSubscription).where(
                and_(
                    NotificationSubscription.company_id == company_id,
                    NotificationSubscription.notification_template_id == template_id,
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            # Update existing
            subscription.is_enabled = is_enabled
            if custom_timing:
                subscription.custom_timing_config = custom_timing
            if custom_message:
                subscription.custom_message_template = custom_message
            subscription.updated_at = datetime.utcnow()
        else:
            # Create new
            subscription = NotificationSubscription(
                company_id=company_id,
                notification_template_id=template_id,
                custom_timing_config=custom_timing,
                custom_message_template=custom_message,
                is_enabled=is_enabled,
            )
            db.add(subscription)

        await db.commit()
        await db.refresh(subscription)

        logger.info(f"✅ Company {company_id} subscribed to template {template_id}")
        return subscription

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
        result = await db.execute(
            select(NotificationSubscription).where(
                and_(
                    NotificationSubscription.company_id == company_id,
                    NotificationSubscription.notification_template_id == template_id,
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.is_enabled = False
            subscription.updated_at = datetime.utcnow()
            await db.commit()
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
        query = select(NotificationSubscription).where(
            NotificationSubscription.company_id == company_id
        )

        if is_enabled is not None:
            query = query.where(NotificationSubscription.is_enabled == is_enabled)

        result = await db.execute(query)
        return list(result.scalars().all())

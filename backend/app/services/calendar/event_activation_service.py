"""
Event and Notification Activation Service.

Business logic for activating mandatory events and assigning auto-notifications.
"""
import logging
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import EventTemplateRepository, NotificationTemplateRepository, NotificationSubscriptionRepository
from app.services.calendar import EventConfigService
from app.db.models.notifications import NotificationSubscription

logger = logging.getLogger(__name__)


class EventActivationService:
    """Service for activating events and notifications for companies."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def activate_mandatory_events(self, company_id: UUID) -> List[str]:
        """
        Activate all mandatory event templates for a company.

        Args:
            company_id: UUID of the company

        Returns:
            List of activated event codes
        """
        # Get mandatory event templates
        event_template_repo = EventTemplateRepository(self.db)
        mandatory_templates = await event_template_repo.find_mandatory()

        if not mandatory_templates:
            logger.warning("[Event Service] No mandatory event templates found")
            return []

        # Activate each mandatory event
        event_config_service = EventConfigService(self.db)
        activated_events = []

        for template in mandatory_templates:
            try:
                await event_config_service.activate_event(
                    company_id=company_id,
                    event_template_id=template.id,
                    custom_config=None
                )
                activated_events.append(template.code)
                logger.info(
                    f"[Event Service] ✅ Activated mandatory event: {template.code}"
                )
            except Exception as e:
                logger.error(
                    f"[Event Service] ❌ Error activating event {template.code}: {e}",
                    exc_info=True
                )

        return activated_events

    async def assign_auto_notifications(
        self,
        company_id: UUID,
        is_new_company: bool
    ) -> List[str]:
        """
        Assign auto-assign notifications to a company.

        Args:
            company_id: UUID of the company
            is_new_company: Whether this is a newly created company

        Returns:
            List of assigned notification codes
        """
        # Only assign if new company
        if not is_new_company:
            logger.info(
                f"[Event Service] Skipping auto-assign for existing company {company_id}"
            )
            return []

        # Get auto-assign templates
        template_repo = NotificationTemplateRepository(self.db)
        auto_assign_templates = await template_repo.find_auto_assign_templates()

        if not auto_assign_templates:
            logger.info("[Event Service] No auto-assign notification templates found")
            return []

        # Assign each notification
        subscription_repo = NotificationSubscriptionRepository(self.db)
        assigned_notifications = []

        for template in auto_assign_templates:
            try:
                # Check if subscription already exists
                existing = await subscription_repo.find_by_company_and_template(
                    company_id=company_id,
                    template_id=template.id,
                    enabled_only=False
                )

                if existing:
                    logger.debug(
                        f"[Event Service] Subscription already exists for {template.code}"
                    )
                    continue

                # Create new subscription
                subscription = NotificationSubscription(
                    company_id=company_id,
                    notification_template_id=template.id,
                    is_enabled=True,
                    channels=["whatsapp"],
                    custom_timing_config=None,
                    custom_message_template=None
                )
                self.db.add(subscription)
                assigned_notifications.append(template.code)

                logger.info(
                    f"[Event Service] ✅ Auto-assigned notification: {template.code}"
                )
            except Exception as e:
                logger.error(
                    f"[Event Service] ❌ Error assigning notification {template.code}: {e}",
                    exc_info=True
                )

        return assigned_notifications

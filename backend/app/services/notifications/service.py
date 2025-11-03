"""
Main Notification Service for Fizko
Orchestrates notification management, scheduling, and delivery via WhatsApp
"""
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    NotificationTemplate,
    NotificationSubscription,
    ScheduledNotification,
    NotificationHistory,
    UserNotificationPreference,
)
from app.services.whatsapp.service import WhatsAppService

from .modules import (
    TemplateService,
    SubscriptionService,
    SchedulingService,
    SendingService,
    PreferenceService,
    HistoryService,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Main orchestrator service for notifications.
    Delegates to specialized modules for different aspects of notification management.
    """

    def __init__(self, whatsapp_service: WhatsAppService):
        """
        Initialize the notification service with all sub-services.

        Args:
            whatsapp_service: WhatsApp service instance
        """
        self.whatsapp_service = whatsapp_service

        # Initialize sub-services
        self.templates = TemplateService(whatsapp_service)
        self.subscriptions = SubscriptionService(whatsapp_service)
        self.scheduling = SchedulingService(whatsapp_service)
        self.sending = SendingService(whatsapp_service)
        self.preferences = PreferenceService(whatsapp_service)
        self.history = HistoryService(whatsapp_service)

    # ========== Template Management ==========

    async def get_template(
        self,
        db: AsyncSession,
        template_id: Optional[UUID] = None,
        code: Optional[str] = None,
    ) -> Optional[NotificationTemplate]:
        """
        Get a notification template by ID or code.
        Delegates to TemplateService.
        """
        return await self.templates.get_template(db, template_id, code)

    async def list_templates(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        entity_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[NotificationTemplate]:
        """
        List notification templates with optional filters.
        Delegates to TemplateService.
        """
        return await self.templates.list_templates(db, category, entity_type, is_active)

    async def create_template(
        self,
        db: AsyncSession,
        code: str,
        name: str,
        category: str,
        message_template: str,
        timing_config: dict,
        description: Optional[str] = None,
        entity_type: Optional[str] = None,
        priority: str = "normal",
        is_active: bool = True,
        auto_assign_to_new_companies: bool = False,
        metadata: Optional[dict] = None
    ) -> NotificationTemplate:
        """
        Create a new notification template.
        Delegates to TemplateService.
        """
        return await self.templates.create_template(
            db, code, name, category, message_template, timing_config,
            description, entity_type, priority, is_active,
            auto_assign_to_new_companies, metadata
        )

    async def update_template(
        self,
        db: AsyncSession,
        template_id: UUID,
        **kwargs
    ) -> NotificationTemplate:
        """
        Update a notification template.
        Delegates to TemplateService.
        """
        return await self.templates.update_template(db, template_id, **kwargs)

    async def delete_template(
        self,
        db: AsyncSession,
        template_id: UUID
    ) -> bool:
        """
        Delete a notification template.
        Delegates to TemplateService.
        """
        return await self.templates.delete_template(db, template_id)

    # ========== Subscription Management ==========

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
        Delegates to SubscriptionService.
        """
        return await self.subscriptions.subscribe_company(
            db, company_id, template_id, custom_timing, custom_message, is_enabled
        )

    async def unsubscribe_company(
        self,
        db: AsyncSession,
        company_id: UUID,
        template_id: UUID,
    ) -> bool:
        """
        Unsubscribe a company from a notification template.
        Delegates to SubscriptionService.
        """
        return await self.subscriptions.unsubscribe_company(db, company_id, template_id)

    async def get_company_subscriptions(
        self,
        db: AsyncSession,
        company_id: UUID,
        is_enabled: Optional[bool] = None,
    ) -> List[NotificationSubscription]:
        """
        Get a company's notification subscriptions.
        Delegates to SubscriptionService.
        """
        return await self.subscriptions.get_company_subscriptions(db, company_id, is_enabled)

    # ========== Scheduling ==========

    async def schedule_notification(
        self,
        db: AsyncSession,
        company_id: UUID,
        template_id: UUID,
        recipients: List[Dict[str, Any]],
        message_context: Dict[str, Any],
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        reference_date: Optional[Union[datetime, date]] = None,
        custom_timing: Optional[Dict] = None,
    ) -> ScheduledNotification:
        """
        Schedule a notification for future sending.
        Delegates to SchedulingService.
        """
        return await self.scheduling.schedule_notification(
            db, company_id, template_id, recipients, message_context,
            entity_type, entity_id, reference_date, custom_timing
        )

    async def get_pending_notifications(
        self,
        db: AsyncSession,
        limit: int = 50,
    ) -> List[ScheduledNotification]:
        """
        Get pending notifications ready to send.
        Delegates to SchedulingService.
        """
        return await self.scheduling.get_pending_notifications(db, limit)

    # ========== Sending ==========

    async def send_scheduled_notification(
        self,
        db: AsyncSession,
        scheduled_id: UUID,
    ) -> Dict[str, Any]:
        """
        Send a scheduled notification.
        Delegates to SendingService.
        """
        return await self.sending.send_scheduled_notification(db, scheduled_id)

    async def process_pending_notifications(
        self,
        db: AsyncSession,
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Process a batch of pending notifications.
        Delegates to SendingService.
        """
        return await self.sending.process_pending_notifications(db, batch_size)

    # ========== User Preferences ==========

    async def get_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID
    ) -> Dict[str, Any]:
        """
        Get a user's notification preferences.
        Delegates to PreferenceService.
        """
        return await self.preferences.get_user_preferences(db, user_id, company_id)

    async def update_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        **kwargs
    ) -> UserNotificationPreference:
        """
        Update a user's notification preferences.
        Delegates to PreferenceService.
        """
        return await self.preferences.update_user_preferences(
            db, user_id, company_id, **kwargs
        )

    # ========== History & Analytics ==========

    async def get_notification_history(
        self,
        db: AsyncSession,
        company_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[NotificationHistory]:
        """
        Get notification history with filters.
        Delegates to HistoryService.
        """
        return await self.history.get_notification_history(
            db, company_id, user_id, entity_type, entity_id, status, limit
        )

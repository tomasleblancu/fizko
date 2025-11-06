"""
Scheduling service for notifications
Handles creation and management of scheduled notifications
"""
import logging
from datetime import datetime, timedelta, time as dt_time, date
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    NotificationTemplate,
    NotificationSubscription,
    ScheduledNotification,
)
from .base_service import BaseNotificationService

logger = logging.getLogger(__name__)


class SchedulingService(BaseNotificationService):
    """
    Service for scheduling notifications.
    Handles timing calculations and creation of scheduled notifications.
    """

    def _build_whatsapp_components(
        self,
        template: NotificationTemplate,
        message_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build WhatsApp Meta API components from template structure and message context.

        Template extra_metadata should contain:
        {
            "whatsapp_template_structure": {
                "header_params": ["day_name"],
                "body_params": ["sales_count", "sales_total_ft", ...]
            }
        }

        Returns:
            List of components in Meta API v21.0 format (without "name" field)
        """
        components = []

        # Get template structure from extra_metadata
        template_structure = template.extra_metadata.get("whatsapp_template_structure", {})
        header_params = template_structure.get("header_params", [])
        body_params = template_structure.get("body_params", [])

        # Build header component
        if header_params:
            header_parameters = []
            for param_name in header_params:
                if param_name in message_context:
                    # Meta API v21.0 uses "parameter_name" for named parameters
                    header_parameters.append({
                        "type": "text",
                        "parameter_name": param_name,
                        "text": str(message_context[param_name])
                    })

            if header_parameters:
                components.append({
                    "type": "header",
                    "parameters": header_parameters
                })

        # Build body component
        if body_params:
            body_parameters = []
            for param_name in body_params:
                if param_name in message_context:
                    # Meta API v21.0 uses "parameter_name" for named parameters
                    body_parameters.append({
                        "type": "text",
                        "parameter_name": param_name,
                        "text": str(message_context[param_name])
                    })

            if body_parameters:
                components.append({
                    "type": "body",
                    "parameters": body_parameters
                })

        return components

    def _render_message(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a message by replacing variables.

        Args:
            template: Message template with {{variable}} placeholders
            context: Dictionary with variable values

        Returns:
            Rendered message
        """
        message = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            message = message.replace(placeholder, str(value))
        return message

    def _calculate_scheduled_time(
        self,
        timing_config: Dict,
        reference_date: Optional[Union[datetime, date]] = None,
    ) -> datetime:
        """
        Calculate scheduled time based on timing configuration.

        Args:
            timing_config: Timing configuration from template
            reference_date: Reference date (e.g., event due_date)

        Returns:
            Timestamp when notification should be sent
        """
        timing_type = timing_config.get("type", "immediate")

        if timing_type == "immediate":
            return datetime.utcnow()

        elif timing_type == "relative":
            # Relative to a reference date (e.g., -1 day before event)
            if not reference_date:
                raise ValueError("reference_date required for relative timing")

            offset_days = timing_config.get("offset_days", 0)
            time_str = timing_config.get("time", "09:00")  # HH:MM

            # Parse time
            hour, minute = map(int, time_str.split(":"))

            # Handle both datetime and date objects
            ref_date = reference_date.date() if isinstance(reference_date, datetime) else reference_date

            # Calculate date/time
            target_date = ref_date + timedelta(days=offset_days)
            scheduled_time = datetime.combine(
                target_date,
                dt_time(hour=hour, minute=minute),
            )

            return scheduled_time

        elif timing_type == "absolute":
            # Same day as event, specific time
            if not reference_date:
                raise ValueError("reference_date required for absolute timing")

            time_str = timing_config.get("time", "09:00")
            hour, minute = map(int, time_str.split(":"))

            # Handle both datetime and date objects
            ref_date = reference_date.date() if isinstance(reference_date, datetime) else reference_date

            scheduled_time = datetime.combine(
                ref_date,
                dt_time(hour=hour, minute=minute),
            )

            return scheduled_time

        else:
            raise ValueError(f"Unknown timing type: {timing_type}")

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

        Args:
            db: Database session
            company_id: Company ID
            template_id: Template ID
            recipients: List of recipients [{"user_id": "...", "phone": "+56..."}, ...]
            message_context: Context for rendering message
            entity_type: Related entity type (optional)
            entity_id: Entity ID (optional)
            reference_date: Reference date for timing calculation
            custom_timing: Custom timing (overrides template)

        Returns:
            Created ScheduledNotification
        """
        # Get template
        result = await db.execute(
            select(NotificationTemplate).where(NotificationTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Check company subscription
        subscription_result = await db.execute(
            select(NotificationSubscription).where(
                and_(
                    NotificationSubscription.company_id == company_id,
                    NotificationSubscription.notification_template_id == template_id,
                    NotificationSubscription.is_enabled == True,
                )
            )
        )
        subscription = subscription_result.scalar_one_or_none()

        # Use custom timing from subscription, parameter, or template
        timing_config = (
            custom_timing
            or (subscription.custom_timing_config if subscription else None)
            or template.timing_config
        )

        # Calculate scheduled time
        scheduled_for = self._calculate_scheduled_time(timing_config, reference_date)

        # If time already passed and is "immediate", send now
        if scheduled_for < datetime.utcnow():
            scheduled_for = datetime.utcnow()

        # Render message
        message_template = (
            (subscription.custom_message_template if subscription else None)
            or template.message_template
        )
        message_content = self._render_message(message_template, message_context)

        # Build extra_metadata
        extra_metadata = {"message_context": message_context}

        # Add whatsapp_components if template has whatsapp_template_id
        if template.whatsapp_template_id and template.extra_metadata:
            whatsapp_components = self._build_whatsapp_components(template, message_context)
            if whatsapp_components:
                extra_metadata["whatsapp_components"] = whatsapp_components

        # Create scheduled notification
        scheduled = ScheduledNotification(
            company_id=company_id,
            notification_template_id=template_id,
            entity_type=entity_type,
            entity_id=entity_id,
            recipients=recipients,
            message_content=message_content,
            scheduled_for=scheduled_for,
            status="pending",
            extra_metadata=extra_metadata,
        )

        db.add(scheduled)
        await db.commit()
        await db.refresh(scheduled)

        logger.info(
            f"📅 Notification scheduled: {template.name} for {len(recipients)} "
            f"recipients, sending at: {scheduled_for}"
        )

        return scheduled

    async def get_pending_notifications(
        self,
        db: AsyncSession,
        limit: int = 50,
    ) -> List[ScheduledNotification]:
        """
        Get pending notifications ready to send.

        Args:
            db: Database session
            limit: Result limit

        Returns:
            List of pending notifications
        """
        now = datetime.utcnow()

        result = await db.execute(
            select(ScheduledNotification)
            .where(
                and_(
                    ScheduledNotification.status == "pending",
                    ScheduledNotification.scheduled_for <= now,
                    ScheduledNotification.send_attempts < 3,  # Max 3 attempts
                )
            )
            .order_by(ScheduledNotification.scheduled_for)
            .limit(limit)
        )

        return list(result.scalars().all())

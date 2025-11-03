"""
Sending service for notifications
Handles actual delivery of notifications via WhatsApp
"""
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    NotificationTemplate,
    NotificationHistory,
    ScheduledNotification,
    UserNotificationPreference,
    Conversation,
    CalendarEvent,
)
from .base_service import BaseNotificationService

logger = logging.getLogger(__name__)


class SendingService(BaseNotificationService):
    """
    Service for sending notifications.
    Handles user preferences, message delivery, and history tracking.
    """

    async def _check_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        template: NotificationTemplate,
    ) -> bool:
        """
        Check if user allows receiving this notification based on preferences.

        Args:
            db: Database session
            user_id: User ID
            company_id: Company ID
            template: Notification template

        Returns:
            True if should send, False if should skip
        """
        # Get user preferences
        result = await db.execute(
            select(UserNotificationPreference).where(
                and_(
                    UserNotificationPreference.user_id == user_id,
                    UserNotificationPreference.company_id == company_id,
                )
            )
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            # No preferences = send
            return True

        # Check if notifications are enabled
        if not prefs.notifications_enabled:
            logger.info(f"🔕 User {user_id} has notifications disabled")
            return False

        # Check quiet hours
        now = datetime.utcnow()
        if prefs.quiet_hours_start and prefs.quiet_hours_end:
            current_time = now.time()
            if prefs.quiet_hours_start <= current_time <= prefs.quiet_hours_end:
                logger.info(f"🔕 Quiet hours for user {user_id}")
                return False

        # Check quiet days
        if prefs.quiet_days:
            weekday = now.strftime("%A").lower()
            if weekday in prefs.quiet_days:
                logger.info(f"🔕 Quiet day for user {user_id}: {weekday}")
                return False

        # Check muted categories
        if prefs.muted_categories and template.category in prefs.muted_categories:
            logger.info(f"🔕 Muted category for user {user_id}: {template.category}")
            return False

        # Check muted templates
        if prefs.muted_templates and str(template.id) in prefs.muted_templates:
            logger.info(f"🔕 Muted template for user {user_id}")
            return False

        # TODO: Check frequency limits (max_notifications_per_day, min_interval_minutes)

        return True

    async def _generate_notification_context(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID,
        company_id: UUID,
        notification_content: Optional[str] = None,
    ) -> str:
        """
        Generate notification context to insert as assistant message.
        Reuses UITools logic but returns only structured text.

        Args:
            db: Database session
            entity_type: Entity type (calendar_event, tax_obligation, etc.)
            entity_id: Entity ID
            company_id: Company ID
            notification_content: Sent notification content (optional)

        Returns:
            str: Structured context in XML
        """
        try:
            if entity_type == "calendar_event":
                # Load event
                result = await db.execute(
                    select(CalendarEvent).where(
                        and_(
                            CalendarEvent.id == entity_id,
                            CalendarEvent.company_id == company_id,
                        )
                    )
                )
                event = result.scalar_one_or_none()

                if not event:
                    logger.warning(f"⚠️ CalendarEvent {entity_id} not found")
                    return """<notification_context>
I sent you a reminder about an event.
</notification_context>"""

                # Format dates
                due_date_str = event.due_date.strftime("%d/%m/%Y") if event.due_date else "No date"

                context = f"""<notification_context>
I sent you a reminder about:

📅 Event: {event.title}
Due: {due_date_str}
Status: {event.status or 'Pending'}"""

                if event.description:
                    context += f"\nDescription: {event.description}"

                if notification_content:
                    context += f"\n\nSent message: {notification_content}"

                context += "\n</notification_context>"

                return context

            # Add more entity types as needed
            elif entity_type == "tax_obligation":
                # TODO: Implement tax obligation context
                return """<notification_context>
I sent you a reminder about a tax obligation.
</notification_context>"""

            elif entity_type == "payroll_deadline":
                # TODO: Implement payroll deadline context
                return """<notification_context>
I sent you a reminder about a payroll deadline.
</notification_context>"""

            else:
                # Generic context for unimplemented types
                logger.debug(f"ℹ️ Entity type '{entity_type}' without specific context")
                return f"""<notification_context>
I sent you a reminder.
{f'Message: {notification_content}' if notification_content else ''}
</notification_context>"""

        except Exception as e:
            logger.error(f"⚠️ Error generating notification context: {e}")
            # Return minimal context on error
            return """<notification_context>
I sent you a reminder.
</notification_context>"""

    async def send_scheduled_notification(
        self,
        db: AsyncSession,
        scheduled_id: UUID,
    ) -> Dict[str, Any]:
        """
        Send a scheduled notification.

        Args:
            db: Database session
            scheduled_id: Scheduled notification ID

        Returns:
            Sending results with statistics
        """
        # Get notification
        result = await db.execute(
            select(ScheduledNotification).where(ScheduledNotification.id == scheduled_id)
        )
        scheduled = result.scalar_one_or_none()

        if not scheduled:
            raise ValueError(f"Notification {scheduled_id} not found")

        if scheduled.status != "pending":
            raise ValueError(f"Notification already processed: {scheduled.status}")

        # Mark as processing
        scheduled.status = "processing"
        scheduled.last_attempt_at = datetime.utcnow()
        scheduled.send_attempts += 1
        await db.commit()

        # Get template
        template_result = await db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.id == scheduled.notification_template_id
            )
        )
        template = template_result.scalar_one_or_none()

        # Send to each recipient
        results = {
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "details": [],
        }

        for recipient in scheduled.recipients:
            user_id = recipient.get("user_id")
            phone = recipient.get("phone")

            if not phone:
                logger.warning(f"⚠️ Recipient without phone: {recipient}")
                results["skipped"] += 1
                continue

            # Check user preferences
            if user_id:
                should_send = await self._check_user_preferences(
                    db, UUID(user_id), scheduled.company_id, template
                )
                if not should_send:
                    results["skipped"] += 1
                    continue

            try:
                # Normalize phone number (remove '+' if exists)
                normalized_phone = phone.lstrip('+') if phone.startswith('+') else phone

                # Get whatsapp_config_id from ENV
                whatsapp_config_id = os.getenv("DEFAULT_WHATSAPP_CONFIG_ID")
                if not whatsapp_config_id:
                    raise ValueError("DEFAULT_WHATSAPP_CONFIG_ID not configured in environment")

                # Send via WhatsApp
                send_result = await self.whatsapp_service.send_text(
                    phone_number=normalized_phone,
                    message=scheduled.message_content,
                    whatsapp_config_id=whatsapp_config_id,
                )

                # Record in history
                conversation_id = send_result.get("conversation_id")
                message_id = send_result.get("message_id") or send_result.get("id")

                history = NotificationHistory(
                    company_id=scheduled.company_id,
                    notification_template_id=scheduled.notification_template_id,
                    scheduled_notification_id=scheduled.id,
                    entity_type=scheduled.entity_type,
                    entity_id=scheduled.entity_id,
                    user_id=UUID(user_id) if user_id else None,
                    phone_number=phone,
                    message_content=scheduled.message_content,
                    status="sent",
                    whatsapp_conversation_id=conversation_id,
                    whatsapp_message_id=message_id,
                    sent_at=datetime.utcnow(),
                )
                db.add(history)

                results["sent"] += 1
                results["details"].append(
                    {
                        "phone": phone,
                        "status": "sent",
                        "message_id": message_id,
                        "conversation_id": conversation_id,
                    }
                )

                logger.info(f"✅ Notification sent to {phone} | conv_id={conversation_id} | msg_id={message_id}")

                # OPTIMIZATION: Anchor notification context to conversation
                # This eliminates the need to search notifications when user responds
                if conversation_id and scheduled.entity_type:
                    try:
                        from app.services.whatsapp.conversation_manager import WhatsAppConversationManager

                        # 1. Find internal conversation by Kapso ID
                        internal_conv_result = await db.execute(
                            select(Conversation).where(
                                Conversation.meta_data["whatsapp_conversation_id"].astext == conversation_id
                            )
                        )
                        internal_conversation = internal_conv_result.scalar_one_or_none()

                        if internal_conversation:
                            # 2. Generate context based on entity_type
                            context_text = await self._generate_notification_context(
                                db=db,
                                entity_type=scheduled.entity_type,
                                entity_id=scheduled.entity_id,
                                company_id=scheduled.company_id,
                                notification_content=scheduled.message_content,
                            )

                            # 3. Insert as assistant message
                            await WhatsAppConversationManager.add_notification_context_message(
                                db=db,
                                conversation_id=internal_conversation.id,
                                notification_context=context_text,
                            )

                            logger.info(f"📌 Context anchored to conversation {internal_conversation.id}")
                        else:
                            logger.debug(f"ℹ️ Internal conversation not found for Kapso ID {conversation_id}")
                    except Exception as e:
                        logger.error(f"⚠️ Error anchoring context: {e}")
                        # Don't fail notification sending if this fails

            except Exception as e:
                logger.error(f"❌ Error sending to {phone}: {e}")

                # Record error in history
                history = NotificationHistory(
                    company_id=scheduled.company_id,
                    notification_template_id=scheduled.notification_template_id,
                    scheduled_notification_id=scheduled.id,
                    entity_type=scheduled.entity_type,
                    entity_id=scheduled.entity_id,
                    user_id=UUID(user_id) if user_id else None,
                    phone_number=phone,
                    message_content=scheduled.message_content,
                    status="failed",
                    error_message=str(e),
                    sent_at=datetime.utcnow(),
                )
                db.add(history)

                results["failed"] += 1
                results["details"].append({"phone": phone, "status": "failed", "error": str(e)})

        # Update scheduled notification status
        if results["sent"] > 0:
            scheduled.status = "sent"
            scheduled.sent_at = datetime.utcnow()
            scheduled.send_results = results
        elif results["failed"] > 0 and results["sent"] == 0:
            scheduled.status = "failed"
            scheduled.error_message = f"{results['failed']} sends failed"
        else:
            scheduled.status = "skipped"

        await db.commit()

        logger.info(
            f"📊 Notification {scheduled_id} processed: "
            f"{results['sent']} sent, {results['failed']} failed, {results['skipped']} skipped"
        )

        return results

    async def process_pending_notifications(
        self,
        db: AsyncSession,
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Process a batch of pending notifications.
        This function should be called periodically (manually or via Celery).

        Args:
            db: Database session
            batch_size: Batch size to process

        Returns:
            Processing statistics
        """
        logger.info(f"🔄 Processing pending notifications (batch: {batch_size})...")

        # Get pending notifications
        now = datetime.utcnow()
        result = await db.execute(
            select(ScheduledNotification)
            .where(
                and_(
                    ScheduledNotification.status == "pending",
                    ScheduledNotification.scheduled_for <= now,
                    ScheduledNotification.send_attempts < 3,
                )
            )
            .order_by(ScheduledNotification.scheduled_for)
            .limit(batch_size)
        )
        pending = list(result.scalars().all())

        stats = {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0,
        }

        for notification in pending:
            try:
                result = await self.send_scheduled_notification(db, notification.id)
                stats["processed"] += 1
                stats["sent"] += result["sent"]
                stats["failed"] += result["failed"]
                stats["skipped"] += result["skipped"]
            except Exception as e:
                logger.error(f"❌ Error processing notification {notification.id}: {e}")
                stats["failed"] += 1

        logger.info(
            f"✅ Processing completed: {stats['processed']} notifications, "
            f"{stats['sent']} messages sent"
        )

        return stats

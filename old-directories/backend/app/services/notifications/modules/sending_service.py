"""
Sending service for notifications
Handles actual delivery of notifications via WhatsApp
"""
import logging
import os
import re
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
    Supports conditional WhatsApp template usage (production) vs plain text (development).
    """

    def _is_production_environment(self) -> bool:
        """
        Check if running in production environment.

        Returns:
            True if production, False if development/local
        """
        env = os.getenv("ENVIRONMENT", "development")
        return env.lower() in ["production", "prod", "railway"]

    def _extract_variables_from_text(self, text: str) -> List[str]:
        """
        Extract {{variables}} from text.

        Args:
            text: Text with variables

        Returns:
            List of variable names
        """
        if not text:
            return []
        return re.findall(r'\{\{(\w+)\}\}', text)

    def _build_template_components(
        self,
        message_context: dict,
        template: NotificationTemplate
    ) -> List[Dict[str, Any]]:
        """
        Build Meta API components from message_context and template configuration.

        Template extra_metadata should contain:
        {
            "whatsapp_template_structure": {
                "header_params": ["day_name"],  # Parameters for header component
                "body_params": ["sales_count", "sales_total_ft", "purchases_count", "purchases_total_ft"]
            }
        }

        Returns:
            List of components in Meta API v21.0 format (without "name" field)
        """
        components = []

        # Get template structure from extra_metadata
        template_structure = template.extra_metadata.get("whatsapp_template_structure", {})
        header_params_names = template_structure.get("header_params", [])
        body_params_names = template_structure.get("body_params", [])

        # Build header component if needed
        if header_params_names:
            header_parameters = []
            for param_name in header_params_names:
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

        # Build body component if needed
        if body_params_names:
            body_parameters = []
            for param_name in body_params_names:
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
        entity_type: Optional[str],
        entity_id: Optional[UUID],
        company_id: UUID,
        notification_content: Optional[str] = None,
    ) -> str:
        """
        Generate notification context to insert as assistant message.
        Reuses UITools logic but returns only structured text.

        Args:
            db: Database session
            entity_type: Entity type (calendar_event, tax_obligation, etc.) - can be None
            entity_id: Entity ID - can be None
            company_id: Company ID
            notification_content: Sent notification content (optional)

        Returns:
            str: Structured context in XML
        """
        try:
            if entity_type == "calendar_event":
                # Load event with event_template
                result = await db.execute(
                    select(CalendarEvent)
                    .options(selectinload(CalendarEvent.event_template))
                    .where(
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

📅 Event: {event.event_template.name if event.event_template else "Sin título"}
Due: {due_date_str}
Status: {event.status or 'Pending'}"""

                if event.event_template and event.event_template.description:
                    context += f"\nDescription: {event.event_template.description}"

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

                # Get WhatsApp configuration from ENV
                whatsapp_config_id = os.getenv("DEFAULT_WHATSAPP_CONFIG_ID")
                phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

                if not whatsapp_config_id:
                    raise ValueError("DEFAULT_WHATSAPP_CONFIG_ID not configured in environment")
                if not phone_number_id:
                    raise ValueError("WHATSAPP_PHONE_NUMBER_ID not configured in environment")

                # Determine if we should use WhatsApp template or plain text
                is_production = self._is_production_environment()
                use_whatsapp_template = (
                    # is_production and
                    template and
                    template.whatsapp_template_id  # Use the correct field
                )

                if use_whatsapp_template:
                    # Use WhatsApp template via Meta API
                    logger.info(f"📱 Using WhatsApp template: {template.whatsapp_template_id}")

                    # Extract components from extra_metadata (already formatted by scheduler)
                    components = scheduled.extra_metadata.get("whatsapp_components")
                    logger.info(f"📋 WhatsApp components: {components}")

                    # Send via WhatsApp template (Meta API format)
                    send_result = await self.whatsapp_service.send_template(
                        phone_number=normalized_phone,
                        template_name=template.whatsapp_template_id,
                        phone_number_id=phone_number_id,
                        components=components,
                        template_language="es_CL",  # Spanish (Chile) - Meta format
                        whatsapp_config_id=whatsapp_config_id,  # Pass config ID to fetch conversation_id
                    )

                else:
                    # DEVELOPMENT: Skip if no active conversation
                    if not is_production:
                        logger.info(f"📝 Development: Attempting to send plain text message")

                        try:
                            # Try to send as plain text (requires active conversation)
                            send_result = await self.whatsapp_service.send_text(
                                phone_number=normalized_phone,
                                message=scheduled.message_content,
                                whatsapp_config_id=whatsapp_config_id,
                            )
                        except ValueError as e:
                            # No active conversation - skip in development
                            if "No se encontró conversación activa" in str(e):
                                logger.warning(f"⚠️ Skipping {phone}: No active conversation (development mode)")
                                results["skipped"] += 1
                                continue
                            else:
                                raise
                    else:
                        # PRODUCTION without template: Error
                        raise ValueError(
                            f"Template {template.code if template else 'N/A'} has no whatsapp_template_id. "
                            "Cannot send notification in production without WhatsApp template."
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
                if conversation_id and user_id:
                    try:
                        from app.services.whatsapp.conversation_manager import WhatsAppConversationManager

                        # 1. Find or create internal conversation by Kapso ID
                        # Since we use Kapso conversation_id as our Conversation.id, just query by ID
                        internal_conv_result = await db.execute(
                            select(Conversation).where(Conversation.id == UUID(conversation_id))
                        )
                        internal_conversation = internal_conv_result.scalar_one_or_none()

                        if not internal_conversation:
                            # Create conversation if it doesn't exist
                            # Use Kapso conversation_id directly as our Conversation.id (both are UUIDs)
                            logger.info(f"📝 Creating new conversation with Kapso ID: {conversation_id}")

                            internal_conversation = Conversation(
                                id=UUID(conversation_id),  # Use Kapso ID directly!
                                user_id=UUID(user_id),
                                meta_data={
                                    "channel": "whatsapp",
                                    "phone_number": phone,
                                    "created_from": "notification_template",
                                    "template_code": template.code if template else None,
                                    # Cache auth for faster webhook processing
                                    "user_id": str(user_id),
                                    "company_id": str(scheduled.company_id),
                                },
                            )

                            db.add(internal_conversation)
                            await db.commit()
                            await db.refresh(internal_conversation)

                            logger.info(f"✅ Conversation created with ID: {internal_conversation.id}")

                        # 2. Generate context based on entity_type (if exists)
                        # Always save context, even if entity_type is null (generic notifications)
                        context_text = await self._generate_notification_context(
                            db=db,
                            entity_type=scheduled.entity_type,
                            entity_id=scheduled.entity_id,
                            company_id=scheduled.company_id,
                            notification_content=scheduled.message_content,
                        )

                        # 3. Insert as assistant message in PostgreSQL
                        await WhatsAppConversationManager.add_notification_context_message(
                            db=db,
                            conversation_id=internal_conversation.id,
                            notification_context=context_text,
                        )

                        logger.info(f"📌 Context anchored to PostgreSQL conversation {internal_conversation.id}")

                        # 4. ALSO save to SQLite session for agent context
                        # This ensures the agent sees the notification context in its history
                        try:
                            from agents import SQLiteSession

                            # Get SQLite session file path (same as WhatsAppAgentRunner)
                            import os as os_module
                            sessions_dir = os_module.path.join(
                                os_module.path.dirname(__file__), "..", "..", "..", "sessions"
                            )
                            os_module.makedirs(sessions_dir, exist_ok=True)
                            session_file = os_module.path.join(sessions_dir, "whatsapp_agent_sessions.db")

                            # Create SQLite session
                            sqlite_session = SQLiteSession(str(internal_conversation.id), session_file)

                            # Add context as assistant message to SQLite history
                            # Format must match ChatKit's MessageOutputItem format
                            assistant_message = {
                                "role": "assistant",
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": context_text
                                    }
                                ]
                            }

                            # Add notification context to session (correct API: add_items)
                            await sqlite_session.add_items([assistant_message])

                            # Close session to commit changes to SQLite (not async)
                            sqlite_session.close()

                            logger.info(f"📌 Context also saved to SQLite session for agent")

                        except Exception as sqlite_error:
                            logger.error(f"⚠️ Error saving context to SQLite: {sqlite_error}")
                            import traceback
                            logger.error(traceback.format_exc())
                            # Don't fail the whole flow if SQLite save fails

                    except Exception as e:
                        logger.error(f"⚠️ Error creating/anchoring conversation: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
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

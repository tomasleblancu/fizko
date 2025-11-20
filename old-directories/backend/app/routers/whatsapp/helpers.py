"""
Helper functions para el router de WhatsApp
"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationHistory


async def find_recent_notification(
    db: AsyncSession,
    whatsapp_conversation_id: str,
    hours_ago: int = 48,
) -> Optional[NotificationHistory]:
    """
    Find most recent notification in a WhatsApp conversation.

    Args:
        db: Database session
        whatsapp_conversation_id: The Kapso conversation ID from WhatsApp
        hours_ago: How many hours back to search (default 48)

    Returns:
        NotificationHistory object or None if not found
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours_ago)

    stmt = (
        select(NotificationHistory)
        .where(
            NotificationHistory.whatsapp_conversation_id == whatsapp_conversation_id,
            NotificationHistory.sent_at >= cutoff,
        )
        .order_by(NotificationHistory.sent_at.desc())
        .limit(1)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def get_notification_ui_component(entity_type: Optional[str]) -> str:
    """
    Map notification entity_type to UI Tool component name.

    Args:
        entity_type: The entity type from notification_history (e.g., "calendar_event", "form29")

    Returns:
        UI Tool component name (e.g., "notification_calendar_event", "notification_generic")
    """
    if not entity_type:
        return "notification_generic"

    NOTIFICATION_UI_COMPONENTS = {
        "calendar_event": "notification_calendar_event",
        # Add more mappings as needed:
        # "form29": "notification_form29",
        # "payroll": "notification_payroll",
    }

    return NOTIFICATION_UI_COMPONENTS.get(entity_type, "notification_generic")

"""
Unified Notification Service

Supports multiple channels:
- WhatsApp (via Kapso)
- Push notifications (via Expo)

Example usage:
    # Send to multiple channels
    await send_notification(
        db=db,
        company_id="uuid",
        channels=["whatsapp", "push"],
        title="F29 Due Soon",
        body="Your F29 is due in 3 days",
        data={"type": "f29_reminder"}
    )

    # Send push only
    await send_push_notification_to_company(
        db=db,
        company_id="uuid",
        title="Document Ready",
        body="Your invoice is ready"
    )
"""

from .service import (
    send_notification,
    send_push_notification_to_company,
    send_push_notification_to_user,
)

__all__ = [
    "send_notification",
    "send_push_notification_to_company",
    "send_push_notification_to_user",
]

"""
Unified Notification Service

Manages multi-channel notification delivery (WhatsApp + Push).
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.services.push_notifications import (
    send_push_to_user,
    send_push_to_users,
)

logger = logging.getLogger(__name__)


async def send_push_notification_to_user(
    user_id: str | UUID,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    badge: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Send push notification to a single user.

    Args:
        user_id: User UUID
        title: Notification title
        body: Notification body
        data: Optional payload data (available in app when tapped)
        badge: Badge count for app icon

    Returns:
        Dict with status and any error info

    Example:
        await send_push_notification_to_user(
            user_id="uuid",
            title="F29 Due Soon",
            body="Your F29 is due in 3 days",
            data={"type": "f29_reminder", "company_id": "123"},
            badge=1
        )
    """
    try:
        result = await send_push_to_user(
            user_id=user_id,
            title=title,
            body=body,
            data=data,
            badge=badge,
        )

        if result is None:
            return {"status": "no_token", "user_id": str(user_id)}

        return {"status": "sent", "user_id": str(user_id), "result": result}

    except Exception as e:
        logger.error(f"Failed to send push to user {user_id}: {e}", exc_info=True)
        return {"status": "error", "user_id": str(user_id), "error": str(e)}


async def send_push_notification_to_company(
    company_id: str | UUID,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    badge: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Send push notification to all users in a company.

    Looks up all users associated with the company and sends push notifications
    to those who have registered push tokens.

    Args:
        company_id: Company UUID
        title: Notification title
        body: Notification body
        data: Optional payload data
        badge: Badge count for app icon

    Returns:
        Dict with counts of sent/skipped/errors

    Example:
        await send_push_notification_to_company(
            company_id="uuid",
            title="Document Synced",
            body="Your documents have been synced from SII",
            data={"type": "sii_sync", "company_id": "uuid"}
        )
    """
    from app.config.supabase import get_supabase_client

    company_id_str = str(company_id)

    try:
        # Get all users for this company via sessions table
        supabase = get_supabase_client()

        # Query sessions to get user IDs for this company
        sessions_response = supabase.client.table("sessions").select("user_id").eq("company_id", company_id_str).execute()

        if not sessions_response.data:
            logger.info(f"No users found for company {company_id_str}")
            return {"status": "no_users", "company_id": company_id_str}

        user_ids = [session["user_id"] for session in sessions_response.data]

        # Send to all users in company
        result = await send_push_to_users(
            user_ids=user_ids,
            title=title,
            body=body,
            data=data,
            badge=badge,
        )

        result["company_id"] = company_id_str
        return result

    except Exception as e:
        logger.error(f"Failed to send push to company {company_id_str}: {e}", exc_info=True)
        return {
            "status": "error",
            "company_id": company_id_str,
            "error": str(e),
            "sent": 0,
            "skipped": 0,
            "errors": []
        }


async def send_notification(
    company_id: str | UUID,
    channels: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    whatsapp_recipients: Optional[List[str]] = None,
    badge: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Send notification through multiple channels.

    Supports:
    - "push": Mobile push notifications via Expo
    - "whatsapp": WhatsApp messages via Kapso

    Args:
        company_id: Company UUID
        channels: List of channels to use ["push", "whatsapp"]
        title: Notification title (used for push, may be adapted for WhatsApp)
        body: Notification body text
        data: Optional payload data
        whatsapp_recipients: Optional list of phone numbers for WhatsApp
        badge: Badge count for push notifications

    Returns:
        Dict with results per channel

    Example:
        # Send to both channels
        await send_notification(
            company_id="uuid",
            channels=["push", "whatsapp"],
            title="F29 Reminder",
            body="Your F29 is due tomorrow",
            data={"type": "f29_reminder"},
            whatsapp_recipients=["+56912345678"]
        )
    """
    results = {}

    # Send push notifications
    if "push" in channels:
        logger.info(f"Sending push notification to company {company_id}")
        push_result = await send_push_notification_to_company(
            company_id=company_id,
            title=title,
            body=body,
            data=data,
            badge=badge,
        )
        results["push"] = push_result

    # Send WhatsApp notifications
    if "whatsapp" in channels:
        logger.info(f"Sending WhatsApp notification to company {company_id}")

        if not whatsapp_recipients:
            results["whatsapp"] = {
                "status": "skipped",
                "reason": "no_recipients"
            }
        else:
            # Import here to avoid circular dependency
            try:
                from app.services.whatsapp import WhatsAppService

                whatsapp_service = WhatsAppService()

                # Send WhatsApp messages to all recipients
                whatsapp_results = []
                for recipient in whatsapp_recipients:
                    try:
                        # Format: WhatsApp doesn't support rich notifications like push
                        # Just send the body text
                        message = f"*{title}*\n\n{body}"

                        # Note: You'll need to implement send_text_message in WhatsAppService
                        # This is a placeholder
                        await whatsapp_service.send_text_message(
                            phone_number=recipient,
                            message=message,
                            company_id=str(company_id)
                        )

                        whatsapp_results.append({
                            "recipient": recipient,
                            "status": "sent"
                        })

                    except Exception as e:
                        logger.error(f"Failed to send WhatsApp to {recipient}: {e}")
                        whatsapp_results.append({
                            "recipient": recipient,
                            "status": "error",
                            "error": str(e)
                        })

                results["whatsapp"] = {
                    "status": "completed",
                    "results": whatsapp_results
                }

            except ImportError:
                logger.warning("WhatsApp service not available")
                results["whatsapp"] = {
                    "status": "error",
                    "error": "WhatsApp service not available"
                }
            except Exception as e:
                logger.error(f"WhatsApp notification failed: {e}", exc_info=True)
                results["whatsapp"] = {
                    "status": "error",
                    "error": str(e)
                }

    return results

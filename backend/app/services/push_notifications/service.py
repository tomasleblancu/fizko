"""
Push Notifications Service

Handles sending push notifications to mobile devices via Expo Push Service.
Supports both individual and batch notifications.

Example usage:
    # Send to a specific token
    await send_push_notification(
        expo_push_token="ExponentPushToken[...]",
        title="F29 Due Soon",
        body="Your F29 is due in 3 days",
        data={"type": "f29_reminder", "company_id": "123"}
    )

    # Send to a user by ID
    await send_push_to_user(
        db=db,
        user_id="uuid",
        title="Document Ready",
        body="Your invoice is ready to view"
    )

    # Send to multiple users
    await send_push_to_users(
        db=db,
        user_ids=["uuid1", "uuid2"],
        title="System Update",
        body="Fizko has been updated"
    )
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)

# Expo Push Service API endpoint
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

# Maximum batch size for Expo push notifications
MAX_BATCH_SIZE = 100


class PushNotificationError(Exception):
    """Base exception for push notification errors."""
    pass


class InvalidTokenError(PushNotificationError):
    """Raised when the Expo push token is invalid."""
    pass


class ExpoServiceError(PushNotificationError):
    """Raised when Expo service returns an error."""
    pass


async def send_push_notification(
    expo_push_token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    sound: str = "default",
    badge: Optional[int] = None,
    category_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    ttl: Optional[int] = None,
    priority: str = "default",
) -> Dict[str, Any]:
    """
    Send a single push notification via Expo Push Service.

    Args:
        expo_push_token: The Expo push token (format: ExponentPushToken[...])
        title: Notification title
        body: Notification body text
        data: Optional JSON data to include (accessible in app)
        sound: Sound to play ("default" or null for silent)
        badge: Badge count to display on app icon
        category_id: Notification category for iOS
        channel_id: Notification channel for Android
        ttl: Time-to-live in seconds (default: 0 for immediate delivery)
        priority: "default", "normal", or "high"

    Returns:
        Dict containing the Expo API response

    Raises:
        InvalidTokenError: If the token format is invalid
        ExpoServiceError: If Expo service returns an error
        httpx.HTTPError: If the request fails
    """
    # Validate token format
    if not expo_push_token or not expo_push_token.startswith("ExponentPushToken["):
        raise InvalidTokenError(f"Invalid Expo push token format: {expo_push_token}")

    # Build message payload
    message = {
        "to": expo_push_token,
        "title": title,
        "body": body,
        "data": data or {},
        "sound": sound,
        "priority": priority,
    }

    # Add optional fields
    if badge is not None:
        message["badge"] = badge

    if category_id:
        message["categoryId"] = category_id

    if channel_id:
        message["channelId"] = channel_id

    if ttl is not None:
        message["ttl"] = ttl

    # Send request to Expo
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                EXPO_PUSH_URL,
                json=message,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            result = response.json()

            # Check for errors in response
            if "data" in result and result["data"]:
                ticket = result["data"][0]
                if ticket.get("status") == "error":
                    error_msg = ticket.get("message", "Unknown error")
                    error_code = ticket.get("details", {}).get("error")

                    if error_code == "DeviceNotRegistered":
                        logger.warning(f"Device not registered for token: {expo_push_token[:20]}...")
                    else:
                        logger.error(f"Expo push error: {error_msg} (code: {error_code})")

                    raise ExpoServiceError(f"Expo push failed: {error_msg}")

            logger.info(f"Push notification sent successfully to {expo_push_token[:20]}...")
            return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error sending push notification: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending push notification: {e}")
        raise


async def send_push_notifications_batch(
    messages: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Send multiple push notifications in a single batch request.

    Args:
        messages: List of message dictionaries (same format as send_push_notification)

    Returns:
        Dict containing the Expo API response with tickets for each message

    Raises:
        ValueError: If batch exceeds maximum size
        httpx.HTTPError: If the request fails

    Note:
        Maximum batch size is 100 messages. Split larger batches manually.
    """
    if len(messages) > MAX_BATCH_SIZE:
        raise ValueError(
            f"Batch size {len(messages)} exceeds maximum {MAX_BATCH_SIZE}. "
            "Please split into smaller batches."
        )

    if not messages:
        return {"data": []}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                EXPO_PUSH_URL,
                json=messages,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            result = response.json()

            # Log any errors in batch
            if "data" in result:
                for i, ticket in enumerate(result["data"]):
                    if ticket.get("status") == "error":
                        error_msg = ticket.get("message", "Unknown error")
                        logger.error(f"Batch message {i} failed: {error_msg}")

            logger.info(f"Batch of {len(messages)} notifications sent successfully")
            return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error sending batch notifications: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending batch notifications: {e}")
        raise


async def send_push_to_user(
    user_id: str | UUID,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Send a push notification to a specific user by ID.

    Looks up the user's Expo push token from the database and sends the notification.

    Args:
        user_id: User UUID
        title: Notification title
        body: Notification body
        data: Optional JSON data
        **kwargs: Additional arguments passed to send_push_notification

    Returns:
        Dict containing the API response, or None if user has no token

    Raises:
        PushNotificationError: If sending fails
    """
    from app.config.supabase import get_supabase_client

    # Convert UUID to string if needed
    user_id_str = str(user_id)

    try:
        # Get user's push token from database
        supabase = get_supabase_client()

        result = supabase.client.table("profiles").select("expo_push_token").eq("id", user_id_str).maybe_single().execute()

        if not result.data:
            logger.warning(f"User {user_id_str} not found")
            return None

        expo_push_token = result.data.get("expo_push_token")

        if not expo_push_token:
            logger.info(f"User {user_id_str} has no push token registered")
            return None

        # Send notification
        return await send_push_notification(
            expo_push_token=expo_push_token,
            title=title,
            body=body,
            data=data,
            **kwargs
        )

    except Exception as e:
        logger.error(f"Error sending push to user {user_id_str}: {e}")
        raise PushNotificationError(f"Failed to send push to user: {e}")


async def send_push_to_users(
    user_ids: List[str | UUID],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Send push notifications to multiple users in a batch.

    Args:
        user_ids: List of user UUIDs
        title: Notification title
        body: Notification body
        data: Optional JSON data
        **kwargs: Additional arguments passed to each notification

    Returns:
        Dict with:
            - sent: Number of notifications sent
            - skipped: Number of users without tokens
            - errors: List of error messages

    Note:
        This function automatically handles batching for lists > 100 users.
    """
    from app.config.supabase import get_supabase_client

    # Convert all UUIDs to strings
    user_ids_str = [str(uid) for uid in user_ids]

    results = {
        "sent": 0,
        "skipped": 0,
        "errors": []
    }

    try:
        # Get all push tokens for these users
        supabase = get_supabase_client()

        response = supabase.client.table("profiles").select("id, expo_push_token").in_("id", user_ids_str).execute()

        # Build messages for users with tokens
        messages = []
        for profile in response.data:
            expo_push_token = profile.get("expo_push_token")

            if not expo_push_token:
                results["skipped"] += 1
                continue

            message = {
                "to": expo_push_token,
                "title": title,
                "body": body,
                "data": data or {},
                **kwargs
            }
            messages.append(message)

        if not messages:
            logger.info(f"No users with push tokens in list of {len(user_ids)} users")
            return results

        # Send in batches of MAX_BATCH_SIZE
        for i in range(0, len(messages), MAX_BATCH_SIZE):
            batch = messages[i:i + MAX_BATCH_SIZE]
            try:
                await send_push_notifications_batch(batch)
                results["sent"] += len(batch)
            except Exception as e:
                error_msg = f"Batch {i//MAX_BATCH_SIZE + 1} failed: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)

        logger.info(
            f"Batch notification complete: {results['sent']} sent, "
            f"{results['skipped']} skipped, {len(results['errors'])} errors"
        )

        return results

    except Exception as e:
        logger.error(f"Error sending batch notifications: {e}")
        raise PushNotificationError(f"Failed to send batch notifications: {e}")

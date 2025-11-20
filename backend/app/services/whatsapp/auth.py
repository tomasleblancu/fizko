"""WhatsApp authentication - authenticate users by phone number."""

import logging
from typing import Optional
from uuid import UUID

from supabase import Client

logger = logging.getLogger(__name__)


async def authenticate_user_by_whatsapp(
    client: Client,
    phone_number: str,
) -> Optional[UUID]:
    """
    Authenticate user by WhatsApp phone number.

    Looks up user profile by phone number and returns user ID.
    Phone numbers are normalized with + prefix.

    Args:
        client: Supabase client
        phone_number: Phone number (will be normalized)

    Returns:
        User ID (UUID) if found, None otherwise
    """
    try:
        # Normalize phone number (ensure + prefix)
        normalized_phone = phone_number if phone_number.startswith("+") else f"+{phone_number}"

        logger.info(f"Authenticating user by phone: {normalized_phone}")

        # Query profiles table
        response = (
            client.table("profiles")
            .select("id, full_name, email")
            .eq("phone", normalized_phone)
            .maybe_single()
            .execute()
        )

        if hasattr(response, "data") and response.data:
            profile = response.data
            user_id = UUID(profile["id"])
            logger.info(
                f"Authenticated user: {profile.get('full_name')} ({profile.get('email')})"
            )
            return user_id
        else:
            logger.warning(f"No user found with phone: {normalized_phone}")
            return None

    except Exception as e:
        logger.error(f"Error authenticating user by phone: {e}", exc_info=True)
        return None


def get_cached_auth_from_metadata(metadata: dict) -> Optional[dict]:
    """
    Extract cached authentication from conversation metadata.

    Args:
        metadata: Conversation metadata dict

    Returns:
        Dict with user_id and company_id if cached, None otherwise
    """
    if not metadata:
        return None

    user_id_str = metadata.get("user_id")
    company_id_str = metadata.get("company_id")

    if user_id_str and company_id_str:
        try:
            return {
                "user_id": UUID(user_id_str),
                "company_id": UUID(company_id_str),
            }
        except ValueError:
            logger.warning("Invalid UUID in cached auth metadata")
            return None

    return None

"""WhatsApp Conversation Manager - manage conversation state and messages."""

import logging
from typing import Any, Optional
from uuid import UUID

from supabase import Client

from app.repositories.whatsapp import WhatsAppRepository
from .auth import get_cached_auth_from_metadata

logger = logging.getLogger(__name__)


class WhatsAppConversationManager:
    """
    Manages WhatsApp conversation state and message history.

    Uses the same conversations/messages tables as ChatKit but distinguishes
    WhatsApp conversations via metadata: {"channel": "whatsapp"}
    """

    def __init__(self, client: Client):
        """
        Initialize conversation manager.

        Args:
            client: Supabase client
        """
        self.client = client
        self.repo = WhatsAppRepository(client)

    async def get_or_create_conversation(
        self,
        user_id: UUID,
        company_id: UUID,
        conversation_id: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> dict[str, Any] | None:
        """
        Get or create WhatsApp conversation.

        Optimizes by:
        1. Using Kapso conversation_id as primary key if provided
        2. Caching user_id and company_id in metadata for fast auth

        Args:
            user_id: User ID
            company_id: Company ID
            conversation_id: Optional Kapso conversation ID
            phone_number: Optional phone number for metadata

        Returns:
            Conversation dict or None
        """
        # Prepare metadata with cached auth
        metadata = {
            "channel": "whatsapp",
            "created_via": "whatsapp_webhook",
            "user_id": str(user_id),
            "company_id": str(company_id),
        }

        if phone_number:
            metadata["phone_number"] = phone_number

        # Convert conversation_id to UUID if provided
        conv_uuid = UUID(conversation_id) if conversation_id else None

        return await self.repo.get_or_create_conversation(
            user_id=user_id,
            conversation_id=conv_uuid,
            metadata=metadata,
        )

    async def add_message(
        self,
        conversation_id: UUID,
        user_id: UUID,
        content: str,
        role: str,
        message_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any] | None:
        """
        Add message to conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            content: Message content
            role: Message role ("user" or "assistant")
            message_id: Optional Kapso message ID
            metadata: Optional additional metadata

        Returns:
            Created message dict or None
        """
        msg_metadata = metadata or {}
        msg_metadata["channel"] = "whatsapp"

        if message_id:
            msg_metadata["whatsapp_message_id"] = message_id

        return await self.repo.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            role=role,
            metadata=msg_metadata,
        )

    async def get_conversation_history(
        self,
        conversation_id: UUID,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get conversation message history.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages

        Returns:
            List of messages ordered by created_at
        """
        return await self.repo.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
        )

    async def get_cached_auth(
        self,
        conversation_id: UUID,
    ) -> Optional[dict]:
        """
        Get cached authentication from conversation metadata.

        Args:
            conversation_id: Conversation ID

        Returns:
            Dict with user_id and company_id if cached, None otherwise
        """
        conversation = await self.repo.get_conversation(conversation_id)

        if not conversation:
            return None

        metadata = conversation.get("metadata", {})
        return get_cached_auth_from_metadata(metadata)

    @staticmethod
    def get_cached_auth_from_conversation(conversation: dict) -> Optional[dict]:
        """
        Extract cached auth from conversation dict.

        Args:
            conversation: Conversation dict with metadata

        Returns:
            Dict with user_id and company_id if cached, None otherwise
        """
        if not conversation:
            return None

        metadata = conversation.get("metadata", {})
        return get_cached_auth_from_metadata(metadata)

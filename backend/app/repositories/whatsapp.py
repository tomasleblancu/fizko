"""
WhatsApp Repository - Manage WhatsApp conversations and messages.

Handles database operations for WhatsApp-specific data using Supabase.
"""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from supabase import Client

from .base import BaseRepository

logger = logging.getLogger(__name__)


class WhatsAppRepository(BaseRepository):
    """Repository for WhatsApp conversation and message operations."""

    # =========================================================================
    # Conversation Operations
    # =========================================================================

    async def get_or_create_conversation(
        self,
        user_id: UUID,
        conversation_id: Optional[UUID] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any] | None:
        """
        Get existing conversation or create new one for WhatsApp.

        Args:
            user_id: User ID (from profiles table)
            conversation_id: Optional Kapso conversation ID to use as primary key
            metadata: Optional metadata (should include channel="whatsapp")

        Returns:
            Conversation dict or None if error
        """
        try:
            # If conversation_id provided, try to fetch it first
            if conversation_id:
                response = self._client.table("conversations").select("*").eq(
                    "id", str(conversation_id)
                ).maybe_single().execute()

                existing = self._extract_data(response, "get_conversation")
                if existing:
                    logger.info(f"Found existing conversation: {conversation_id}")
                    return existing

            # Search for recent WhatsApp conversation for this user
            response = (
                self._client.table("conversations")
                .select("*")
                .eq("user_id", str(user_id))
                .contains("metadata", {"channel": "whatsapp"})
                .order("updated_at", desc=True)
                .limit(1)
                .maybe_single()
                .execute()
            )

            existing = self._extract_data(response, "search_whatsapp_conversation")
            if existing:
                logger.info(f"Found recent WhatsApp conversation: {existing['id']}")
                return existing

            # Create new conversation
            default_metadata = {"channel": "whatsapp", "created_via": "whatsapp_webhook"}
            if metadata:
                default_metadata.update(metadata)

            conversation_data = {
                "user_id": str(user_id),
                "title": "WhatsApp",
                "status": "active",
                "metadata": default_metadata,
            }

            if conversation_id:
                conversation_data["id"] = str(conversation_id)

            response = self._client.table("conversations").insert(conversation_data).execute()

            result = self._extract_data(response, "create_conversation")
            if result:
                logger.info(f"Created new conversation: {result['id']}")
            return result

        except Exception as e:
            self._log_error("get_or_create_conversation", e, user_id=user_id)
            return None

    async def update_conversation_metadata(
        self,
        conversation_id: UUID,
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Update conversation metadata.

        Args:
            conversation_id: Conversation ID
            metadata: New metadata to merge

        Returns:
            Updated conversation or None
        """
        try:
            response = (
                self._client.table("conversations")
                .update({"metadata": metadata, "updated_at": datetime.utcnow().isoformat()})
                .eq("id", str(conversation_id))
                .execute()
            )

            return self._extract_data(response, "update_conversation_metadata")

        except Exception as e:
            self._log_error("update_conversation_metadata", e, conversation_id=conversation_id)
            return None

    async def get_conversation(self, conversation_id: UUID) -> dict[str, Any] | None:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation dict or None
        """
        try:
            response = (
                self._client.table("conversations")
                .select("*")
                .eq("id", str(conversation_id))
                .maybe_single()
                .execute()
            )

            return self._extract_data(response, "get_conversation")

        except Exception as e:
            self._log_error("get_conversation", e, conversation_id=conversation_id)
            return None

    # =========================================================================
    # Message Operations
    # =========================================================================

    async def add_message(
        self,
        conversation_id: UUID,
        user_id: UUID,
        content: str,
        role: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any] | None:
        """
        Add message to conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            content: Message content
            role: Message role ("user" or "assistant")
            metadata: Optional metadata (should include channel="whatsapp")

        Returns:
            Created message dict or None
        """
        try:
            default_metadata = {"channel": "whatsapp"}
            if metadata:
                default_metadata.update(metadata)

            message_data = {
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
                "content": content,
                "role": role,
                "metadata": default_metadata,
            }

            response = self._client.table("messages").insert(message_data).execute()

            result = self._extract_data(response, "add_message")

            # Update conversation timestamp
            if result:
                await self._update_conversation_timestamp(conversation_id)

            return result

        except Exception as e:
            self._log_error(
                "add_message",
                e,
                conversation_id=conversation_id,
                user_id=user_id,
                role=role,
            )
            return None

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return

        Returns:
            List of message dicts (ordered by created_at)
        """
        try:
            response = (
                self._client.table("messages")
                .select("*")
                .eq("conversation_id", str(conversation_id))
                .order("created_at", desc=False)
                .limit(limit)
                .execute()
            )

            return self._extract_data_list(response, "get_conversation_messages")

        except Exception as e:
            self._log_error("get_conversation_messages", e, conversation_id=conversation_id)
            return []

    async def _update_conversation_timestamp(self, conversation_id: UUID) -> None:
        """
        Update conversation's updated_at timestamp.

        Args:
            conversation_id: Conversation ID
        """
        try:
            self._client.table("conversations").update(
                {"updated_at": datetime.utcnow().isoformat()}
            ).eq("id", str(conversation_id)).execute()

        except Exception as e:
            self._log_error("update_conversation_timestamp", e, conversation_id=conversation_id)

    # =========================================================================
    # Profile Operations
    # =========================================================================

    async def get_profile_by_phone(self, phone: str) -> dict[str, Any] | None:
        """
        Get user profile by phone number.

        Args:
            phone: Phone number (normalized with + prefix)

        Returns:
            Profile dict or None
        """
        try:
            # Normalize phone (ensure + prefix)
            normalized_phone = phone if phone.startswith("+") else f"+{phone}"

            response = (
                self._client.table("profiles")
                .select("*")
                .eq("phone", normalized_phone)
                .maybe_single()
                .execute()
            )

            return self._extract_data(response, "get_profile_by_phone")

        except Exception as e:
            self._log_error("get_profile_by_phone", e, phone=phone)
            return None

    async def get_profile(self, user_id: UUID) -> dict[str, Any] | None:
        """
        Get user profile by ID.

        Args:
            user_id: User ID

        Returns:
            Profile dict or None
        """
        try:
            response = (
                self._client.table("profiles")
                .select("*")
                .eq("id", str(user_id))
                .maybe_single()
                .execute()
            )

            return self._extract_data(response, "get_profile")

        except Exception as e:
            self._log_error("get_profile", e, user_id=user_id)
            return None

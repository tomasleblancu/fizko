"""Conversations API - manage WhatsApp conversations."""

import logging
from typing import Any, Optional

from .base import BaseAPI
from ..models import ConversationStatus

logger = logging.getLogger(__name__)


class ConversationsAPI(BaseAPI):
    """API for WhatsApp conversation operations."""

    async def list(
        self,
        whatsapp_config_id: Optional[str] = None,
        status: Optional[ConversationStatus] = None,
        limit: int = 50,
        page: int = 1,
    ) -> dict[str, Any]:
        """
        List conversations.

        Args:
            whatsapp_config_id: Optional filter by WhatsApp config
            status: Optional filter by status (active/ended)
            limit: Max results per page
            page: Page number

        Returns:
            Paginated list of conversations
        """
        params: dict[str, Any] = {"limit": limit, "page": page}

        if whatsapp_config_id:
            params["whatsapp_config_id"] = whatsapp_config_id
        if status:
            params["status"] = status.value

        return await self._make_request(
            method="GET",
            endpoint="whatsapp_conversations",
            params=params,
        )

    async def get(self, conversation_id: str) -> dict[str, Any]:
        """
        Get a specific conversation.

        Args:
            conversation_id: Kapso conversation ID

        Returns:
            Conversation details
        """
        return await self._make_request(
            method="GET",
            endpoint=f"whatsapp_conversations/{conversation_id}",
        )

    async def get_context(
        self,
        conversation_id: str,
        message_limit: int = 30,
    ) -> dict[str, Any]:
        """
        Get conversation context with recent messages.

        Args:
            conversation_id: Kapso conversation ID
            message_limit: Number of recent messages to include

        Returns:
            Conversation with recent messages
        """
        params = {"message_limit": message_limit}

        return await self._make_request(
            method="GET",
            endpoint=f"whatsapp_conversations/{conversation_id}/context",
            params=params,
        )

    async def update_status(
        self,
        conversation_id: str,
        status: ConversationStatus,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Update conversation status (close or reopen).

        Args:
            conversation_id: Kapso conversation ID
            status: New status (active or ended)
            reason: Optional reason for status change

        Returns:
            Updated conversation
        """
        payload: dict[str, Any] = {"status": status.value}

        if reason:
            payload["reason"] = reason

        return await self._make_request(
            method="PATCH",
            endpoint=f"whatsapp_conversations/{conversation_id}",
            data=payload,
        )

    async def search(
        self,
        query: Optional[str] = None,
        status: Optional[ConversationStatus] = None,
        whatsapp_config_id: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> dict[str, Any]:
        """
        Search conversations by phone or contact name.

        Args:
            query: Search query (phone substring or contact name)
            status: Optional filter by status
            whatsapp_config_id: Optional filter by config
            limit: Max results per page
            page: Page number

        Returns:
            Matching conversations
        """
        params: dict[str, Any] = {"limit": limit, "page": page}

        if query:
            params["query"] = query
        if status:
            params["status"] = status.value
        if whatsapp_config_id:
            params["whatsapp_config_id"] = whatsapp_config_id

        return await self._make_request(
            method="GET",
            endpoint="whatsapp_conversations/search",
            params=params,
        )

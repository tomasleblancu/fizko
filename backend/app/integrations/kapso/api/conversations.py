"""
Conversations API - Manage WhatsApp conversations.
"""
import logging
from typing import Dict, Optional, Any

from .base import BaseAPI
from ..models import ConversationStatus

logger = logging.getLogger(__name__)


class ConversationsAPI(BaseAPI):
    """API for conversation operations."""

    async def create(
        self,
        phone_number: str,
        whatsapp_config_id: str,
    ) -> Dict[str, Any]:
        """
        Create a new conversation.

        Args:
            phone_number: Contact phone number
            whatsapp_config_id: WhatsApp configuration ID

        Returns:
            Created conversation info
        """
        payload = {
            "phone_number": phone_number,
            "whatsapp_config_id": whatsapp_config_id,
        }

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp_conversations",
            data=payload,
        )

        logger.info(f"✅ Conversation created for {phone_number}")
        return result

    async def get(
        self,
        conversation_id: str,
    ) -> Dict[str, Any]:
        """
        Get conversation information.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation info
        """
        result = await self._make_request(
            method="GET",
            endpoint=f"whatsapp_conversations/{conversation_id}",
        )

        return result

    async def list(
        self,
        whatsapp_config_id: Optional[str] = None,
        limit: int = 50,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        List conversations.

        Args:
            whatsapp_config_id: Filter by WhatsApp config
            limit: Results limit
            page: Page number

        Returns:
            List of conversations
        """
        params = {
            "limit": limit,
            "page": page,
        }

        if whatsapp_config_id:
            params["whatsapp_config_id"] = whatsapp_config_id

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp_conversations",
            params=params,
        )

        return result

    async def update_status(
        self,
        conversation_id: str,
        status: ConversationStatus,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update conversation status.

        Args:
            conversation_id: Conversation ID
            status: New status (active or ended)
            reason: Reason for change

        Returns:
            Updated conversation
        """
        payload = {
            "conversation_id": conversation_id,
            "status": status.value if isinstance(status, ConversationStatus) else status,
        }

        if reason:
            payload["reason"] = reason

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp/conversation_set_status",
            data=payload,
        )

        logger.info(f"✅ Conversation {conversation_id} updated to {status}")
        return result

"""
Messages API - Send and search messages.
"""
import logging
from typing import Dict, List, Optional, Any

from .base import BaseAPI
from ..models import MessageType

logger = logging.getLogger(__name__)


class MessagesAPI(BaseAPI):
    """API for WhatsApp message operations."""

    async def send_text(
        self,
        conversation_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Send a text message.

        Args:
            conversation_id: Conversation ID
            message: Message content

        Returns:
            API response with message details
        """
        payload = {
            "message": {
                "content": message,
                "message_type": "text",
            }
        }

        result = await self._make_request(
            method="POST",
            endpoint=f"whatsapp_conversations/{conversation_id}/whatsapp_messages",
            data=payload,
        )

        logger.info(f"✅ Text message sent (conv: {conversation_id})")
        return result

    async def send_media(
        self,
        conversation_id: str,
        media_url: str,
        media_type: MessageType,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a media message (image, video, audio, document).

        Args:
            conversation_id: Conversation ID
            media_url: Public URL to media file
            media_type: Type of media
            caption: Optional caption
            filename: Optional filename for documents

        Returns:
            API response
        """
        payload = {
            "message": {
                "message_type": media_type.value if isinstance(media_type, MessageType) else media_type,
                "media_url": media_url,
            }
        }

        if caption:
            payload["message"]["caption"] = caption
        if filename and media_type == MessageType.DOCUMENT:
            payload["message"]["filename"] = filename

        result = await self._make_request(
            method="POST",
            endpoint=f"whatsapp_conversations/{conversation_id}/whatsapp_messages",
            data=payload,
            timeout=60,  # Longer timeout for media
        )

        logger.info(f"✅ Media {media_type} sent (conv: {conversation_id})")
        return result

    async def send_interactive(
        self,
        conversation_id: str,
        interactive_type: str,
        body_text: str,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        buttons: Optional[List[Dict]] = None,
        sections: Optional[List[Dict]] = None,
        list_button_text: str = "Ver opciones",
    ) -> Dict[str, Any]:
        """
        Send an interactive message (buttons or list).

        Args:
            conversation_id: Conversation ID
            interactive_type: Type (button or list)
            body_text: Main text
            header_text: Header text
            footer_text: Footer text
            buttons: List of buttons (for type=button)
            sections: List sections (for type=list)
            list_button_text: Text for list button

        Returns:
            API response
        """
        payload = {
            "conversation_selector": {
                "conversation_id": conversation_id,
            },
            "interactive_type": interactive_type,
            "body_text": body_text,
        }

        if header_text:
            payload["header_text"] = header_text
        if footer_text:
            payload["footer_text"] = footer_text
        if buttons:
            payload["buttons"] = buttons
        if sections:
            payload["sections"] = sections
        if interactive_type == "list":
            payload["list_button_text"] = list_button_text

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp/send_interactive",
            data=payload,
        )

        logger.info(f"✅ Interactive {interactive_type} sent (conv: {conversation_id})")
        return result

    async def search(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Search messages by content.

        Args:
            query: Search text
            conversation_id: Filter by conversation
            limit: Results limit
            page: Page number

        Returns:
            Matching messages
        """
        params = {
            "query": query,
            "limit": limit,
            "page": page,
        }

        if conversation_id:
            params["conversation_id"] = conversation_id

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/search_messages",
            params=params,
        )

        return result

    async def mark_as_read(
        self,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mark messages as read.

        Args:
            conversation_id: Conversation ID (to mark all)
            message_id: Specific message ID
            before: ISO timestamp (mark messages before this)

        Returns:
            Operation result
        """
        payload = {}

        if conversation_id:
            payload["conversation_id"] = conversation_id
        if message_id:
            payload["message_id"] = message_id
        if before:
            payload["before"] = before

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp/mark_inbound_read",
            data=payload,
        )

        return result

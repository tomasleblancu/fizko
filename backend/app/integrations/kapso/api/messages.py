"""Messages API - send and manage WhatsApp messages."""

import logging
from typing import Any, Optional

from .base import BaseAPI
from ..models import MessageType, InteractiveType

logger = logging.getLogger(__name__)


class MessagesAPI(BaseAPI):
    """API for WhatsApp message operations."""

    async def send_text(
        self,
        conversation_id: str,
        message: str,
    ) -> dict[str, Any]:
        """
        Send a text message to a conversation.

        Args:
            conversation_id: Kapso conversation ID
            message: Text content

        Returns:
            Message creation response with id, status, etc.
        """
        payload = {
            "message": {
                "content": message,
                "message_type": "text",
            }
        }

        return await self._make_request(
            method="POST",
            endpoint=f"whatsapp_conversations/{conversation_id}/whatsapp_messages",
            data=payload,
        )

    async def send_media(
        self,
        conversation_id: str,
        media_url: str,
        media_type: MessageType,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Send a media message (image, video, audio, document).

        Args:
            conversation_id: Kapso conversation ID
            media_url: Public URL to media file
            media_type: Type of media (image, video, audio, document)
            caption: Optional caption for image/video/document
            filename: Optional filename for documents

        Returns:
            Message creation response
        """
        payload: dict[str, Any] = {
            "message": {
                "message_type": media_type.value,
                "media_url": media_url,
            }
        }

        if caption:
            payload["message"]["caption"] = caption
        if filename:
            payload["message"]["filename"] = filename

        return await self._make_request(
            method="POST",
            endpoint=f"whatsapp_conversations/{conversation_id}/whatsapp_messages",
            data=payload,
            timeout=60,  # Longer timeout for media processing
        )

    async def send_interactive(
        self,
        conversation_id: str,
        interactive_type: InteractiveType,
        body_text: str,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        buttons: Optional[list[dict[str, str]]] = None,
        sections: Optional[list[dict[str, Any]]] = None,
        list_button_text: str = "View Options",
    ) -> dict[str, Any]:
        """
        Send an interactive message (buttons or list).

        Args:
            conversation_id: Kapso conversation ID
            interactive_type: Type of interactive (button or list)
            body_text: Main body text (max 1024 chars)
            header_text: Optional header text (max 60 chars)
            footer_text: Optional footer text (max 60 chars)
            buttons: List of buttons for button type (max 3)
            sections: List of sections for list type (max 10 sections)
            list_button_text: CTA button text for list (max 20 chars)

        Returns:
            Message creation response
        """
        interactive_data: dict[str, Any] = {
            "type": interactive_type.value,
            "body": {"text": body_text},
        }

        if header_text:
            interactive_data["header"] = {"type": "text", "text": header_text}

        if footer_text:
            interactive_data["footer"] = {"text": footer_text}

        if interactive_type == InteractiveType.BUTTON and buttons:
            interactive_data["action"] = {
                "buttons": [
                    {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"]}}
                    for btn in buttons
                ]
            }
        elif interactive_type == InteractiveType.LIST and sections:
            interactive_data["action"] = {
                "button": list_button_text,
                "sections": sections,
            }

        payload = {
            "message": {
                "message_type": "interactive",
                "interactive": interactive_data,
            }
        }

        return await self._make_request(
            method="POST",
            endpoint=f"whatsapp_conversations/{conversation_id}/whatsapp_messages",
            data=payload,
        )

    async def search(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> dict[str, Any]:
        """
        Search message content.

        Args:
            query: Search query (case-insensitive substring)
            conversation_id: Optional conversation filter
            limit: Max results per page
            page: Page number

        Returns:
            Search results with matching messages
        """
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "page": page,
        }

        if conversation_id:
            params["conversation_id"] = conversation_id

        return await self._make_request(
            method="GET",
            endpoint="whatsapp_messages/search",
            params=params,
        )

    async def mark_as_read(
        self,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        before: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Mark message(s) as read.

        Args:
            conversation_id: Optional conversation for bulk marking
            message_id: Optional specific message ID
            before: Optional ISO8601 timestamp for bulk marking (all before this time)

        Returns:
            Operation result
        """
        payload: dict[str, Any] = {}

        if conversation_id:
            payload["conversation_id"] = conversation_id
        if message_id:
            payload["message_id"] = message_id
        if before:
            payload["before"] = before

        return await self._make_request(
            method="POST",
            endpoint="whatsapp_messages/mark_read",
            data=payload,
        )

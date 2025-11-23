"""WhatsApp Service - high-level wrapper for Kapso client."""

import logging
import os
from typing import Any, Optional

from supabase import Client

from app.integrations.kapso import KapsoClient, MessageType, InteractiveType
from .conversation_manager import WhatsAppConversationManager

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    High-level WhatsApp service wrapper.

    Provides simplified interface for WhatsApp operations using Kapso client.
    """

    def __init__(self, client: Client):
        """
        Initialize WhatsApp service.

        Args:
            client: Supabase client
        """
        self.client = client
        self.conversation_manager = WhatsAppConversationManager(client)

        # Initialize Kapso client
        api_token = os.getenv("KAPSO_API_TOKEN")
        if not api_token:
            logger.error("KAPSO_API_TOKEN not configured")
            raise ValueError("KAPSO_API_TOKEN environment variable is required")

        self.kapso = KapsoClient(api_token=api_token)
        logger.info("WhatsApp service initialized")

    # =========================================================================
    # Message Sending
    # =========================================================================

    async def send_text(
        self,
        conversation_id: Optional[str] = None,
        message: str = "",
        phone_number: Optional[str] = None,
        whatsapp_config_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Send text message to conversation.

        Args:
            conversation_id: Kapso conversation ID (optional if phone_number provided)
            message: Text message content
            phone_number: Optional phone number (for finding conversation)
            whatsapp_config_id: Optional WhatsApp config ID (used with phone_number)

        Returns:
            Message response from Kapso

        Raises:
            ValueError: If neither conversation_id nor valid phone_number provided
        """
        try:
            # If phone_number provided but no conversation_id, find active conversation
            if not conversation_id and phone_number:
                logger.info(f"Finding active conversation for phone: {phone_number}")
                conversation = await self._find_active_conversation(
                    phone_number=phone_number,
                    whatsapp_config_id=whatsapp_config_id,
                )
                conversation_id = conversation["id"]

            if not conversation_id:
                raise ValueError(
                    "Either conversation_id or (phone_number + whatsapp_config_id) is required"
                )

            logger.info(f"Sending text message to conversation: {conversation_id}")
            result = await self.kapso.messages.send_text(
                conversation_id=conversation_id,
                message=message,
            )

            # Ensure conversation_id is in result (Kapso API may not include it)
            if "conversation_id" not in result:
                result["conversation_id"] = conversation_id

            return result

        except Exception as e:
            logger.error(f"Error sending text message: {e}", exc_info=True)
            raise

    async def send_media(
        self,
        conversation_id: str,
        media_url: str,
        media_type: str,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Send media message.

        Args:
            conversation_id: Kapso conversation ID
            media_url: Public URL to media file
            media_type: Type of media (image, video, audio, document)
            caption: Optional caption
            filename: Optional filename for documents

        Returns:
            Message response from Kapso
        """
        try:
            logger.info(f"Sending {media_type} to conversation: {conversation_id}")

            # Convert string to MessageType enum
            msg_type = MessageType(media_type)

            return await self.kapso.messages.send_media(
                conversation_id=conversation_id,
                media_url=media_url,
                media_type=msg_type,
                caption=caption,
                filename=filename,
            )

        except Exception as e:
            logger.error(f"Error sending media: {e}", exc_info=True)
            raise

    async def send_interactive(
        self,
        conversation_id: str,
        interactive_type: str,
        body_text: str,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        buttons: Optional[list[dict[str, str]]] = None,
        sections: Optional[list[dict[str, Any]]] = None,
        list_button_text: str = "Ver opciones",
    ) -> dict[str, Any]:
        """
        Send interactive message (buttons or list).

        Args:
            conversation_id: Kapso conversation ID
            interactive_type: Type ("button" or "list")
            body_text: Main body text
            header_text: Optional header
            footer_text: Optional footer
            buttons: Optional buttons for button type
            sections: Optional sections for list type
            list_button_text: CTA button text for list

        Returns:
            Message response from Kapso
        """
        try:
            logger.info(f"Sending interactive ({interactive_type}) to: {conversation_id}")

            # Convert string to InteractiveType enum
            int_type = InteractiveType(interactive_type)

            return await self.kapso.messages.send_interactive(
                conversation_id=conversation_id,
                interactive_type=int_type,
                body_text=body_text,
                header_text=header_text,
                footer_text=footer_text,
                buttons=buttons,
                sections=sections,
                list_button_text=list_button_text,
            )

        except Exception as e:
            logger.error(f"Error sending interactive: {e}", exc_info=True)
            raise

    async def send_text_to_phone(
        self,
        phone_number: str,
        message: str,
        whatsapp_config_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Send text message to a phone number.
        Automatically finds an active conversation for the phone number.

        Args:
            phone_number: Phone number to send to (with or without + prefix)
            message: Text message content
            whatsapp_config_id: Optional WhatsApp config ID to filter conversations

        Returns:
            Message response from Kapso

        Raises:
            ValueError: If no active conversation exists for the phone number
        """
        return await self.send_text(
            phone_number=phone_number,
            message=message,
            whatsapp_config_id=whatsapp_config_id,
        )

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _find_active_conversation(
        self,
        phone_number: str,
        whatsapp_config_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Find an active conversation for a phone number.

        This method searches through existing conversations to find an active one
        matching the phone number. It does NOT create new conversations.

        IMPORTANT: WhatsApp Business API has strict rules:
        - New conversations can only be started with approved templates
        - Regular messages only work within 24-hour window after user message

        Args:
            phone_number: Phone number (will be normalized automatically)
            whatsapp_config_id: Optional WhatsApp config ID to filter

        Returns:
            Active conversation dict with 'id', 'phone_number', 'status', etc.

        Raises:
            ValueError: If no active conversation found for this phone number
        """
        try:
            # Normalize phone number (remove '+' if exists)
            normalized_phone = phone_number.lstrip("+") if phone_number.startswith("+") else phone_number

            # List conversations (increase limit to search more conversations)
            conversations_response = await self.kapso.conversations.list(
                whatsapp_config_id=whatsapp_config_id,
                limit=50,
            )

            # Extract conversation list from response (handle different formats)
            conversations = (
                conversations_response.get("data")
                or conversations_response.get("nodes")
                or conversations_response.get("conversations")
                or conversations_response.get("items")
                or []
            )

            # Find active conversation matching the phone number
            for conv in conversations:
                conv_phone = conv.get("phone_number", "").lstrip("+")
                conv_status = conv.get("status", "")

                if conv_phone == normalized_phone and conv_status == "active":
                    logger.info(f"✅ Active conversation found for {normalized_phone}")
                    return conv

            # If not found, raise informative error
            raise ValueError(
                f"No active conversation found for {normalized_phone}. "
                f"The user must first initiate a conversation by sending a message, "
                f"or you must send an approved WhatsApp template to start the conversation."
            )

        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Error searching for conversation: {e}", exc_info=True)
            raise ValueError(f"Failed to search for conversation: {str(e)}")

    # =========================================================================
    # Webhook Validation
    # =========================================================================

    @staticmethod
    def validate_webhook(
        payload: str,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Validate webhook HMAC signature.

        Args:
            payload: Raw request body as string
            signature: X-Webhook-Signature header value
            secret: Webhook secret

        Returns:
            True if valid, False otherwise
        """
        from app.integrations.kapso.api.webhooks import WebhooksAPI

        return WebhooksAPI.validate_signature(
            payload=payload,
            signature=signature,
            secret=secret,
        )

    # =========================================================================
    # Conversation Operations
    # =========================================================================

    async def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        """
        Get conversation details from Kapso.

        Args:
            conversation_id: Kapso conversation ID

        Returns:
            Conversation details
        """
        return await self.kapso.conversations.get(conversation_id)

    async def search_conversations(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search conversations.

        Args:
            query: Search query (phone or name)
            status: Optional status filter
            limit: Max results

        Returns:
            Search results
        """
        return await self.kapso.conversations.search(
            query=query,
            status=status,
            limit=limit,
        )

    # =========================================================================
    # Contact Operations
    # =========================================================================

    async def search_contacts(
        self,
        query: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search contacts.

        Args:
            query: Search query (name or phone)
            limit: Max results

        Returns:
            Search results
        """
        return await self.kapso.contacts.search(query=query, limit=limit)

    async def get_contact_context(
        self,
        identifier: str,
        include_recent_messages: bool = True,
        recent_message_limit: int = 20,
    ) -> dict[str, Any]:
        """
        Get contact context with recent messages.

        Args:
            identifier: Contact ID or phone
            include_recent_messages: Include recent messages
            recent_message_limit: Number of recent messages

        Returns:
            Contact context
        """
        return await self.kapso.contacts.get_context(
            identifier=identifier,
            include_recent_messages=include_recent_messages,
            recent_message_limit=recent_message_limit,
        )


def get_whatsapp_service(client: Client) -> WhatsAppService:
    """
    Factory function to get WhatsAppService instance.

    Args:
        client: Supabase client

    Returns:
        WhatsAppService instance
    """
    return WhatsAppService(client)

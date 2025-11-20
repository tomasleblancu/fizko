"""
Modular Kapso Client - Organized by domain.

This is the new modular version of KapsoClient.
The old client.py is kept for backward compatibility.
"""
import logging
from typing import Optional

from .api import (
    MessagesAPI,
    ConversationsAPI,
    ContactsAPI,
    TemplatesAPI,
    ConfigAPI,
    WebhooksAPI,
)

logger = logging.getLogger(__name__)


class KapsoClient:
    """
    Modular client for Kapso WhatsApp Business API.

    Organized by domain:
    - messages: Send and search messages
    - conversations: Manage conversations
    - contacts: Contact operations
    - templates: Template operations
    - config: WhatsApp configuration
    - webhooks: Webhook utilities

    Example:
        >>> client = KapsoClient(api_token="your-token")
        >>>
        >>> # Send text message
        >>> await client.messages.send_text(
        ...     conversation_id="conv-123",
        ...     message="Hello!"
        ... )
        >>>
        >>> # Get template structure
        >>> structure = await client.templates.get_structure(
        ...     template_name="daily_summary",
        ...     business_account_id="123456"
        ... )
        >>>
        >>> # Send template
        >>> await client.templates.send(
        ...     phone_number_id="647015955153740",
        ...     to="56912345678",
        ...     template_name="welcome_message",
        ...     language_code="es"
        ... )
    """

    def __init__(
        self,
        api_token: str,
        base_url: str | None = None,
        timeout: int = 30,
    ):
        """
        Initialize modular Kapso client.

        Args:
            api_token: Kapso API token
            base_url: Base URL for API (default: https://app.kapso.ai/api/v1)
            timeout: Default timeout in seconds
        """
        self.api_token = api_token

        # Use default base URL if not provided
        if base_url is None:
            base_url = "https://app.kapso.ai/api/v1"

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Initialize domain-specific API modules
        self.messages = MessagesAPI(
            api_token=api_token,
            base_url=self.base_url,
            timeout=timeout
        )

        self.conversations = ConversationsAPI(
            api_token=api_token,
            base_url=self.base_url,
            timeout=timeout
        )

        self.contacts = ContactsAPI(
            api_token=api_token,
            base_url=self.base_url,
            timeout=timeout
        )

        self.templates = TemplatesAPI(
            api_token=api_token,
            base_url=self.base_url,
            timeout=timeout
        )

        self.config = ConfigAPI(
            api_token=api_token,
            base_url=self.base_url,
            timeout=timeout
        )

        self.webhooks = WebhooksAPI()

        logger.info(f"✅ Modular KapsoClient initialized (base_url: {self.base_url})")

    async def health_check(self):
        """
        Overall health check.

        Returns:
            Health status of all modules
        """
        return {
            "status": "healthy",
            "api_token": "configured" if self.api_token else "missing",
            "base_url": self.base_url,
            "timeout": self.timeout,
            "modules": [
                "messages",
                "conversations",
                "contacts",
                "templates",
                "config",
                "webhooks"
            ]
        }

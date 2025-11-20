"""Main Kapso client that orchestrates all API modules."""

import logging
from typing import Optional

from .api import (
    ContactsAPI,
    ConversationsAPI,
    MessagesAPI,
    TemplatesAPI,
    WebhooksAPI,
)

logger = logging.getLogger(__name__)


class KapsoClient:
    """
    Modular client for Kapso WhatsApp Business API.

    This client provides access to all Kapso API endpoints through
    domain-specific API modules.

    Example:
        ```python
        client = KapsoClient(api_token="your_token")

        # Send text message
        await client.messages.send_text(
            conversation_id="conv_123",
            message="Hello!"
        )

        # Get conversation
        conversation = await client.conversations.get("conv_123")

        # Search contacts
        contacts = await client.contacts.search(query="John")
        ```
    """

    def __init__(
        self,
        api_token: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize Kapso client.

        Args:
            api_token: Kapso API token
            base_url: Optional custom base URL (defaults to production)
            timeout: Default request timeout in seconds
        """
        self.api_token = api_token
        self.base_url = base_url or "https://app.kapso.ai/api/v1"
        self.timeout = timeout

        # Initialize domain-specific API modules
        self.messages = MessagesAPI(api_token, self.base_url, timeout)
        self.conversations = ConversationsAPI(api_token, self.base_url, timeout)
        self.contacts = ContactsAPI(api_token, self.base_url, timeout)
        self.templates = TemplatesAPI(api_token, self.base_url, timeout)
        self.webhooks = WebhooksAPI(api_token, self.base_url, timeout)

        logger.info("Kapso client initialized")

    def __repr__(self) -> str:
        """String representation of client."""
        return f"KapsoClient(base_url={self.base_url})"

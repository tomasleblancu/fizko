"""
API modules for Kapso integration.

Organized by domain:
- messages: Send and search messages
- conversations: Manage conversations
- contacts: Contact management
- templates: WhatsApp template operations
- config: WhatsApp configuration
- webhooks: Webhook utilities
"""

from .messages import MessagesAPI
from .conversations import ConversationsAPI
from .contacts import ContactsAPI
from .templates import TemplatesAPI
from .config import ConfigAPI
from .webhooks import WebhooksAPI

__all__ = [
    "MessagesAPI",
    "ConversationsAPI",
    "ContactsAPI",
    "TemplatesAPI",
    "ConfigAPI",
    "WebhooksAPI",
]

"""
Kapso WhatsApp Business API Integration

Modular client organized by domain:
    client.messages      - Send and search messages
    client.conversations - Manage conversations
    client.contacts      - Contact operations
    client.templates     - Template operations
    client.config        - WhatsApp configuration
    client.webhooks      - Webhook utilities

Legacy monolithic client available as LegacyKapsoClient (from client_old.py)
for backward compatibility if needed.
"""

# Import modular client (main client)
from .client import KapsoClient

# Also export legacy client for backward compatibility
from .client_old import KapsoClient as LegacyKapsoClient

from .models import (
    MessageType,
    ConversationStatus,
    WhatsAppMessage,
    WhatsAppConversation,
    TemplateMessage,
    MediaMessage,
)
from .exceptions import (
    KapsoAPIError,
    KapsoAuthenticationError,
    KapsoValidationError,
    KapsoTimeoutError,
    KapsoNotFoundError,
)

__all__ = [
    "KapsoClient",
    "LegacyKapsoClient",
    "MessageType",
    "ConversationStatus",
    "WhatsAppMessage",
    "WhatsAppConversation",
    "TemplateMessage",
    "MediaMessage",
    "KapsoAPIError",
    "KapsoAuthenticationError",
    "KapsoValidationError",
    "KapsoTimeoutError",
    "KapsoNotFoundError",
]

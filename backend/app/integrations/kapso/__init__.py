"""
Kapso WhatsApp Business API integration.

This module provides a modular client for interacting with the Kapso WhatsApp API.
"""

from .client import KapsoClient
from .exceptions import (
    KapsoAPIError,
    KapsoAuthenticationError,
    KapsoNotFoundError,
    KapsoTimeoutError,
    KapsoValidationError,
)
from .models import (
    ConversationStatus,
    MessageType,
    InteractiveType,
)

__all__ = [
    "KapsoClient",
    "KapsoAPIError",
    "KapsoAuthenticationError",
    "KapsoNotFoundError",
    "KapsoTimeoutError",
    "KapsoValidationError",
    "ConversationStatus",
    "MessageType",
    "InteractiveType",
]

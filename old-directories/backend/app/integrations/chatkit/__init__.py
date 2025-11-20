"""
ChatKit SDK integration module.

This module provides integration with OpenAI's ChatKit SDK, separating
the ChatKit-specific implementation from the core agent system.

Components:
- server: ChatKitServerAdapter (implements ChatKitServer interface)
- attachment_processor: Converts ChatKit attachments to agent format
- types: Type adapters between ChatKit and Fizko types
"""

from .server import ChatKitServerAdapter
from .attachment_processor import convert_attachments_to_content
from .types import extract_user_message_text

__all__ = [
    "ChatKitServerAdapter",
    "convert_attachments_to_content",
    "extract_user_message_text",
]

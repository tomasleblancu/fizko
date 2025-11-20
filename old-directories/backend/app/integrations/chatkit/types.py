"""
ChatKit type utilities and converters.

Handles conversion between ChatKit SDK types and our internal types.

NOTE: The ChatKit Python SDK does not expose message metadata sent from the frontend.
To pass structured data (ui_component, entity_id, entity_type), use URL query parameters
instead. See app/routers/chat/chatkit.py for implementation.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from chatkit.types import UserMessageItem

logger = logging.getLogger(__name__)


def extract_user_message_text(item: UserMessageItem) -> str:
    """
    Extract text content from UserMessageItem.

    Args:
        item: ChatKit UserMessageItem

    Returns:
        Concatenated text from all text content parts
    """
    parts: List[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()



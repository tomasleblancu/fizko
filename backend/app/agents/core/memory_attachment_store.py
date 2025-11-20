"""
Memory Attachment Store - Simple in-memory storage for ChatKit attachments.

Stores attachment content in memory during the request lifecycle.
"""
from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Global in-memory storage for attachments
_attachment_storage: Dict[str, bytes] = {}


class MemoryAttachmentStore:
    """
    Simple in-memory attachment store for ChatKit.

    Stores file bytes temporarily during the session.
    In production, this should be replaced with proper storage (S3, Supabase Storage, etc.)
    """

    def __init__(self):
        """Initialize memory attachment store."""
        logger.info("📎 MemoryAttachmentStore initialized")

    def store(self, attachment_id: str, content: bytes) -> None:
        """Store attachment content."""
        global _attachment_storage
        _attachment_storage[attachment_id] = content
        logger.info(f"📎 Stored attachment {attachment_id} ({len(content)} bytes)")

    def get(self, attachment_id: str) -> bytes | None:
        """Get attachment content."""
        global _attachment_storage
        return _attachment_storage.get(attachment_id)

    def delete(self, attachment_id: str) -> None:
        """Delete attachment content."""
        global _attachment_storage
        if attachment_id in _attachment_storage:
            del _attachment_storage[attachment_id]
            logger.info(f"📎 Deleted attachment {attachment_id}")


# Global helper functions for compatibility
def store_attachment_content(attachment_id: str, content: bytes) -> None:
    """Store attachment content (global helper)."""
    global _attachment_storage
    _attachment_storage[attachment_id] = content
    logger.info(f"📎 Stored attachment {attachment_id} ({len(content)} bytes)")


def get_attachment_content(attachment_id: str) -> bytes | None:
    """Get attachment content (global helper)."""
    global _attachment_storage
    return _attachment_storage.get(attachment_id)

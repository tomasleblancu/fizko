"""
Memory Attachment Store - Simple in-memory storage for ChatKit attachments.

Stores attachment content in memory during the request lifecycle.
Based on old-directory implementation with ChatKit AttachmentStore interface.
"""
from __future__ import annotations

import base64
import logging
import os
import uuid
from typing import Any, Dict

from chatkit.server import AttachmentStore
from chatkit.types import (
    Attachment,
    AttachmentCreateParams,
    FileAttachment,
    ImageAttachment,
)

logger = logging.getLogger(__name__)


def generate_attachment_id(prefix: str = "attachment") -> str:
    """Generate a unique attachment ID."""
    unique_id = str(uuid.uuid4()).replace('-', '')[:12]
    return f"{prefix}_{unique_id}"


# Global in-memory storage for attachments (persists between requests)
_attachment_storage: Dict[str, bytes] = {}
_global_attachments_content: Dict[str, str] = {}  # Base64 content storage


class MemoryAttachmentStore(AttachmentStore):
    """
    Simple in-memory attachment store for ChatKit.

    Stores file bytes temporarily during the session.
    In production, this should be replaced with proper storage (S3, Supabase Storage, etc.)

    Implements ChatKit AttachmentStore interface with two-phase upload.
    """

    def __init__(self):
        """Initialize memory attachment store."""
        self._attachments: Dict[str, Attachment] = {}
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        logger.info("📎 MemoryAttachmentStore initialized")

    async def create_attachment(
        self,
        input: AttachmentCreateParams,
        context: Dict[str, Any]
    ) -> Attachment:
        """
        Phase 1 of two-phase upload: Generate attachment ID and upload URL.

        Args:
            input: Attachment metadata (name, size, mime_type)
            context: Request context

        Returns:
            ImageAttachment or FileAttachment with upload_url
        """
        # Generate unique attachment ID
        attachment_id = generate_attachment_id("atc")

        # Generate upload URL for Phase 2
        upload_url = f"{self.backend_url}/chatkit/upload/{attachment_id}"

        # Determine type (image vs file)
        is_image = input.mime_type.startswith('image/')

        if is_image:
            # Use CSP-safe placeholder data URL for images
            placeholder_data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

            attachment = ImageAttachment(
                id=attachment_id,
                name=input.name,
                mime_type=input.mime_type,
                upload_url=upload_url,
                preview_url=placeholder_data_url,
            )
        else:
            attachment = FileAttachment(
                id=attachment_id,
                name=input.name,
                mime_type=input.mime_type,
                upload_url=upload_url,
            )

        # Save metadata in memory
        self._attachments[attachment_id] = attachment

        logger.info(f"✅ Created attachment: {attachment_id} ({input.name}, {input.mime_type})")

        return attachment

    async def get_attachment(self, attachment_id: str) -> Attachment | None:
        """Retrieve attachment by ID."""
        return self._attachments.get(attachment_id)

    def get_attachment_metadata(self, attachment_id: str) -> Dict[str, Any] | None:
        """
        Retrieve attachment metadata (mime_type, name) by ID.
        Used by the upload endpoint to get the correct file metadata.
        """
        attachment = self._attachments.get(attachment_id)
        if attachment is None:
            return None

        return {
            "mime_type": attachment.mime_type,
            "name": attachment.name
        }

    async def delete_attachment(self, attachment_id: str) -> None:
        """Delete attachment from memory."""
        if attachment_id in self._attachments:
            del self._attachments[attachment_id]
            logger.info(f"🗑️  Deleted attachment metadata: {attachment_id}")

        if attachment_id in _global_attachments_content:
            del _global_attachments_content[attachment_id]
            logger.info(f"🗑️  Deleted attachment content: {attachment_id}")

    def store(self, attachment_id: str, content: bytes) -> None:
        """Store attachment content (Phase 2 upload, backwards compat)."""
        global _attachment_storage
        _attachment_storage[attachment_id] = content
        logger.info(f"📎 Stored attachment {attachment_id} ({len(content)} bytes)")

    def get(self, attachment_id: str) -> bytes | None:
        """Get attachment content (backwards compat)."""
        global _attachment_storage
        return _attachment_storage.get(attachment_id)

    def delete(self, attachment_id: str) -> None:
        """Delete attachment content (backwards compat, non-async)."""
        global _attachment_storage
        if attachment_id in _attachment_storage:
            del _attachment_storage[attachment_id]
            logger.info(f"📎 Deleted attachment {attachment_id}")


# Global helper functions for compatibility
def store_attachment_content(attachment_id: str, content: bytes) -> None:
    """
    Store attachment content in memory (Phase 2 of upload).

    This is called by the /chatkit/upload/{attachment_id} endpoint.

    Args:
        attachment_id: The attachment identifier
        content: Raw file bytes
    """
    # Convert to base64 for storage
    base64_content = base64.b64encode(content).decode('utf-8')

    # Store in global dict (persists between requests but NOT server restarts)
    global _global_attachments_content
    _global_attachments_content[attachment_id] = base64_content

    # Also store raw bytes for backwards compatibility
    global _attachment_storage
    _attachment_storage[attachment_id] = content

    logger.info(
        f"💾 Stored attachment {attachment_id}: "
        f"{len(base64_content)} chars (base64), {len(content)} bytes"
    )


def get_attachment_content(attachment_id: str) -> str | None:
    """
    Retrieve attachment content from memory.

    Args:
        attachment_id: The attachment identifier

    Returns:
        Base64-encoded content or None if not found
    """
    global _global_attachments_content
    return _global_attachments_content.get(attachment_id)

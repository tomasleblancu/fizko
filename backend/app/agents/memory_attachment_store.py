"""
In-memory AttachmentStore for development and testing.

This is a fallback when Supabase is not available.
Uses two-phase upload pattern with temporary in-memory storage.
"""

import base64
import logging
import os
import uuid
from typing import Any

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

# Global storage for attachment content (persists between requests)
# In production, this should be replaced with Redis, S3, or database storage
_global_attachments_content: dict[str, str] = {}


class MemoryAttachmentStore(AttachmentStore):
    """
    In-memory attachment store with two-phase upload.

    WARNING: This is for DEVELOPMENT ONLY. Content is lost on server restart.
    For production, use SupabaseAttachmentStore.

    How it works:
    1. Phase 1: Generate attachment_id and upload URL
    2. Phase 2: Receive file upload at /chatkit/upload/{attachment_id}
    3. Store base64 content in global dict
    4. Convert to OpenAI format when processing message
    """

    def __init__(self):
        """Initialize the memory attachment store."""
        self._attachments: dict[str, Attachment] = {}
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8089")

        # Import Store to persist attachment metadata
        # This allows ChatKit to find attachments when building messages
        from ..stores.supabase_store import SupabaseStore
        self.store = SupabaseStore()

        # Memory attachment store initialized

    async def create_attachment(
        self,
        input: AttachmentCreateParams,
        context: dict[str, Any]
    ) -> Attachment:
        """
        Phase 1: Generate attachment ID and upload URL.

        Args:
            input: {name: str, size: int, mime_type: str}
            context: Request context

        Returns:
            Attachment with upload_url for Phase 2
        """
        # Generate unique ID
        attachment_id = generate_attachment_id("atc")

        # Generate upload URL for Phase 2
        # This endpoint receives the actual file content
        upload_url = f"{self.backend_url}/chatkit/upload/{attachment_id}"

        # Determine type (image vs file)
        is_image = input.mime_type.startswith('image/')

        if is_image:
            # Use a transparent 1x1 pixel PNG as placeholder to avoid CSP violations
            # CSP blocks http:// URLs but allows data: URLs
            # The real image will be loaded when the message is sent via data URL
            placeholder_data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

            attachment = ImageAttachment(
                id=attachment_id,
                name=input.name,
                mime_type=input.mime_type,
                upload_url=upload_url,
                preview_url=placeholder_data_url,  # CSP-safe placeholder
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

        # CRITICAL: Also persist to Store (DB) so ChatKit can find it later
        await self.store.save_attachment(attachment, context)

        logger.info(f"✅ Created attachment: {attachment_id} ({input.name})")
        logger.info(f"💾 Persisted attachment metadata to database")

        return attachment

    async def get_attachment(self, attachment_id: str) -> Attachment | None:
        """
        Retrieve attachment by ID.

        Args:
            attachment_id: The unique attachment identifier

        Returns:
            Attachment object or None if not found
        """
        return self._attachments.get(attachment_id)

    async def delete_attachment(self, attachment_id: str) -> None:
        """
        Delete attachment from memory.

        Args:
            attachment_id: The unique attachment identifier
        """
        # Remove from attachments dict
        if attachment_id in self._attachments:
            del self._attachments[attachment_id]
            logger.info(f"🗑️  Deleted attachment metadata: {attachment_id}")

        # Remove from content storage
        if attachment_id in _global_attachments_content:
            del _global_attachments_content[attachment_id]
            logger.info(f"🗑️  Deleted attachment content: {attachment_id}")


# Helper function to store uploaded content
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
    _global_attachments_content[attachment_id] = base64_content

    logger.info(
        f"💾 Stored attachment {attachment_id}: "
        f"{len(base64_content)} chars (base64)"
    )


def get_attachment_content(attachment_id: str) -> str | None:
    """
    Retrieve attachment content from memory.

    Args:
        attachment_id: The attachment identifier

    Returns:
        Base64-encoded content or None if not found
    """
    return _global_attachments_content.get(attachment_id)

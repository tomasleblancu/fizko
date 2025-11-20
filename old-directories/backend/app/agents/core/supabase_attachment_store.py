"""
Supabase-backed AttachmentStore for ChatKit.

This implementation uses the existing Supabase infrastructure
instead of duplicating upload logic or storage.
"""

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


class SupabaseAttachmentStore(AttachmentStore):
    """
    AttachmentStore that uses Supabase Storage.

    This implementation REUSES the existing /api/attachments/upload endpoint
    and Supabase Storage infrastructure instead of creating a duplicate system.

    How it works:
    1. ChatKit requests upload URL → we generate attachment_id and return /api/attachments/upload
    2. ChatKit uploads file → existing endpoint handles it and stores in Supabase
    3. ChatKit sends message → we retrieve public URL from Supabase
    4. OpenAI processes → downloads directly from Supabase public URL
    """

    def __init__(self):
        """Initialize the Supabase attachment store."""
        # Store metadata for attachments created but not yet uploaded
        self._attachments: dict[str, dict[str, Any]] = {}

        # Get backend URL from environment
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8089")

        # Import Store here to avoid circular import
        from app.stores import SupabaseStore
        self.store = SupabaseStore()

        logger.info("Initialized SupabaseAttachmentStore")

    async def create_attachment(
        self,
        input: AttachmentCreateParams,
        context: dict[str, Any]
    ) -> Attachment:
        """
        Phase 1 of two-phase upload: Generate attachment ID and upload URL.

        This REUSES the existing /api/attachments/upload endpoint instead
        of creating a duplicate upload system.

        Args:
            input: Attachment metadata (name, size, mime_type)
            context: Request context (may contain user_id)

        Returns:
            ImageAttachment or FileAttachment with upload_url pointing to
            the existing /api/attachments/upload endpoint
        """
        # Generate unique attachment ID
        attachment_id = generate_attachment_id("atc")

        # IMPORTANT: We REUSE the existing upload endpoint
        # This avoids duplicating upload logic and storage
        # Include attachment_id as query parameter so backend can update metadata
        upload_url = f"{self.backend_url}/api/attachments/upload?attachment_id={attachment_id}"

        # Store metadata to track this attachment
        # We'll need this later to retrieve the file from Supabase
        self._attachments[attachment_id] = {
            "name": input.name,
            "mime_type": input.mime_type,
            "size": input.size,
            "user_id": context.get("user_id"),
        }

        logger.info(
            f"✅ Created attachment: {attachment_id} ({input.name}, {input.mime_type})"
        )

        # Determine attachment type based on MIME type
        is_image = input.mime_type.startswith('image/')

        if is_image:
            attachment = ImageAttachment(
                id=attachment_id,
                name=input.name,
                mime_type=input.mime_type,
                upload_url=upload_url,  # REUSES existing endpoint
                preview_url=upload_url,  # Use same URL for preview (will be updated after upload)
            )
        else:
            attachment = FileAttachment(
                id=attachment_id,
                name=input.name,
                mime_type=input.mime_type,
                upload_url=upload_url,  # REUSES existing endpoint
            )

        # IMPORTANT: Persist attachment metadata to database immediately
        # This allows ChatKit to load it later when building the message
        await self.store.save_attachment(attachment, context)
        logger.info(f"💾 Persisted attachment metadata to database: {attachment_id}")

        return attachment

    async def get_attachment(self, attachment_id: str) -> Attachment | None:
        """
        Retrieve attachment metadata.

        Args:
            attachment_id: The unique attachment identifier

        Returns:
            Attachment object or None if not found
        """
        metadata = self._attachments.get(attachment_id)

        if metadata is None:
            logger.warning(f"Attachment not found: {attachment_id}")
            return None

        is_image = metadata["mime_type"].startswith('image/')

        # Note: We don't have the Supabase public URL yet
        # This would need to be stored after the upload completes
        # For now, return basic attachment info
        upload_url = f"{self.backend_url}/api/attachments/upload"
        if is_image:
            return ImageAttachment(
                id=attachment_id,
                name=metadata["name"],
                mime_type=metadata["mime_type"],
                upload_url=upload_url,
                preview_url=upload_url,  # Use upload URL as preview temporarily
            )
        else:
            return FileAttachment(
                id=attachment_id,
                name=metadata["name"],
                mime_type=metadata["mime_type"],
                upload_url=f"{self.backend_url}/api/attachments/upload",
            )

    async def delete_attachment(self, attachment_id: str) -> None:
        """
        Delete attachment metadata.

        Note: This does NOT delete the file from Supabase Storage.
        For production, you should implement actual deletion from Supabase.

        Args:
            attachment_id: The unique attachment identifier
        """
        if attachment_id in self._attachments:
            del self._attachments[attachment_id]
            logger.info(f"🗑️  Deleted attachment metadata: {attachment_id}")

        # TODO: For production, delete from Supabase Storage:
        # metadata = self._attachments.get(attachment_id)
        # if metadata and 'storage_path' in metadata:
        #     supabase.storage.from_("product-images").remove([metadata['storage_path']])

    def set_openai_metadata(
        self,
        attachment_id: str,
        file_id: str,
        vector_store_id: str
    ) -> None:
        """
        Store OpenAI file_id and vector_store_id for an attachment.

        Note: This stores in memory only. Database persistence is handled
        via save_attachment() with context containing the OpenAI metadata.

        Args:
            attachment_id: The unique attachment identifier
            file_id: OpenAI file ID
            vector_store_id: OpenAI vector store ID
        """
        if attachment_id in self._attachments:
            self._attachments[attachment_id]["openai_file_id"] = file_id
            self._attachments[attachment_id]["openai_vector_store_id"] = vector_store_id
            logger.info(f"✅ Stored OpenAI metadata for {attachment_id}: file={file_id}, vs={vector_store_id}")

    async def get_openai_metadata(self, attachment_id: str) -> dict[str, str] | None:
        """
        Get OpenAI file_id and vector_store_id for an attachment.

        This first checks memory, then falls back to database if not found.

        Args:
            attachment_id: The unique attachment identifier

        Returns:
            Dict with file_id and vector_store_id, or None if not found
        """
        # Check memory first
        metadata = self._attachments.get(attachment_id)
        if metadata and "openai_file_id" in metadata and "openai_vector_store_id" in metadata:
            return {
                "file_id": metadata["openai_file_id"],
                "vector_store_id": metadata["openai_vector_store_id"],
            }

        # Fall back to database
        return await self.store.get_attachment_openai_metadata(attachment_id)

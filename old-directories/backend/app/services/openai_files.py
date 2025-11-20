"""
Service for managing file uploads to OpenAI Files API and Vector Stores.

This service handles:
- Uploading PDFs to OpenAI Files API
- Creating and managing Vector Stores for file_search
- Associating files with Vector Stores
"""

import logging
import os
from typing import Optional, Tuple

from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIFilesService:
    """
    Service for managing OpenAI Files API and Vector Stores.

    Used for file_search tool to enable agents to read and analyze PDFs.
    """

    def __init__(self):
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")

        self.client = OpenAI(api_key=api_key)
        logger.info("📤 OpenAIFilesService initialized")

    def upload_file_for_file_search(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a file to OpenAI Files API for use with file_search.

        Args:
            file_content: File content as bytes
            filename: Original filename
            mime_type: MIME type of the file

        Returns:
            Tuple (success, file_id, error_message)
            - success: True if upload succeeded
            - file_id: OpenAI file ID (e.g., "file_abc123")
            - error_message: Error message if success=False
        """
        try:
            logger.info(f"📤 Uploading file to OpenAI: {filename} ({mime_type})")

            # Create a file-like object from bytes
            from io import BytesIO
            file_obj = BytesIO(file_content)
            file_obj.name = filename

            # Upload file to OpenAI with purpose="assistants"
            # This makes it available for file_search
            file = self.client.files.create(
                file=file_obj,
                purpose="assistants"
            )

            logger.info(f"✅ File uploaded to OpenAI: {file.id}")
            return True, file.id, None

        except Exception as e:
            error_msg = f"Failed to upload file to OpenAI: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, None, error_msg

    def create_vector_store_with_file(
        self,
        file_id: str,
        store_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a Vector Store and add a file to it.

        Args:
            file_id: OpenAI file ID to add to the vector store
            store_name: Optional name for the vector store

        Returns:
            Tuple (success, vector_store_id, error_message)
            - success: True if creation succeeded
            - vector_store_id: Vector Store ID (e.g., "vs_abc123")
            - error_message: Error message if success=False
        """
        try:
            logger.info(f"📦 Creating Vector Store for file: {file_id}")

            # Try beta.vector_stores first (newer SDK versions)
            try:
                vector_store = self.client.beta.vector_stores.create(
                    name=store_name or f"Document {file_id}",
                    file_ids=[file_id]
                )
                vs_api = self.client.beta.vector_stores
            except AttributeError:
                # If beta.vector_stores doesn't exist, try without beta
                logger.info("📦 Trying vector_stores without beta prefix")
                vector_store = self.client.vector_stores.create(
                    name=store_name or f"Document {file_id}",
                    file_ids=[file_id]
                )
                vs_api = self.client.vector_stores

            logger.info(f"✅ Vector Store created: {vector_store.id}")

            # Wait for the file to be indexed (poll until status is 'completed')
            # This is crucial - file_search won't work until indexing is done
            import time
            max_wait = 60  # Maximum 60 seconds
            poll_interval = 2  # Check every 2 seconds
            elapsed = 0

            logger.info(f"⏳ Waiting for file to be indexed in Vector Store...")
            while elapsed < max_wait:
                # Check the vector store file status
                try:
                    vs_file = vs_api.files.retrieve(
                        vector_store_id=vector_store.id,
                        file_id=file_id
                    )

                    if vs_file.status == "completed":
                        logger.info(f"✅ File indexed successfully (took {elapsed}s)")
                        break
                    elif vs_file.status == "failed":
                        logger.error(f"❌ File indexing failed: {getattr(vs_file, 'last_error', 'Unknown error')}")
                        return False, None, "File indexing failed"

                    # Still in progress
                    logger.info(f"⏳ File status: {vs_file.status} (waited {elapsed}s)")

                except Exception as poll_error:
                    # 404 errors are expected initially - file not yet registered in vector store
                    error_str = str(poll_error)
                    if "404" in error_str or "not found" in error_str.lower():
                        logger.debug(f"⏳ File not yet indexed (waited {elapsed}s, will retry)")
                    else:
                        # Other errors should be logged but we continue polling
                        logger.warning(f"⚠️ Error polling file status: {poll_error}")

                # Wait before next poll
                time.sleep(poll_interval)
                elapsed += poll_interval

            if elapsed >= max_wait:
                logger.warning(f"⚠️ File indexing timeout (waited {max_wait}s), but Vector Store created")

            return True, vector_store.id, None

        except Exception as e:
            error_msg = f"Failed to create vector store: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, None, error_msg

    def add_file_to_vector_store(
        self,
        vector_store_id: str,
        file_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Add a file to an existing Vector Store.

        Args:
            vector_store_id: ID of the vector store
            file_id: OpenAI file ID to add

        Returns:
            Tuple (success, error_message)
        """
        try:
            logger.info(f"➕ Adding file {file_id} to Vector Store {vector_store_id}")

            # Try beta.vector_stores first (newer SDK versions)
            try:
                self.client.beta.vector_stores.files.create(
                    vector_store_id=vector_store_id,
                    file_id=file_id
                )
            except AttributeError:
                # If beta.vector_stores doesn't exist, try without beta
                self.client.vector_stores.files.create(
                    vector_store_id=vector_store_id,
                    file_id=file_id
                )

            logger.info(f"✅ File added to Vector Store")
            return True, None

        except Exception as e:
            error_msg = f"Failed to add file to vector store: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, error_msg

    def delete_file(self, file_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file from OpenAI Files API.

        Args:
            file_id: OpenAI file ID to delete

        Returns:
            Tuple (success, error_message)
        """
        try:
            logger.info(f"🗑️  Deleting file from OpenAI: {file_id}")

            self.client.files.delete(file_id)

            logger.info(f"✅ File deleted from OpenAI")
            return True, None

        except Exception as e:
            error_msg = f"Failed to delete file: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, error_msg


# Singleton instance
_openai_files_service: Optional[OpenAIFilesService] = None


def get_openai_files_service() -> OpenAIFilesService:
    """
    Get the singleton instance of OpenAIFilesService.

    Returns:
        OpenAIFilesService instance
    """
    global _openai_files_service

    if _openai_files_service is None:
        _openai_files_service = OpenAIFilesService()

    return _openai_files_service

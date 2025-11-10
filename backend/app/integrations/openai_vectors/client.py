"""
OpenAI Vector Store client for managing file uploads and vector stores
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from openai import OpenAI

from app.integrations.openai_vectors.models import (
    UploadedFile,
    VectorStoreInfo,
    VectorStoreBatch
)

logger = logging.getLogger(__name__)


class OpenAIVectorClient:
    """
    Client for managing OpenAI vector stores and file uploads

    Usage:
        client = OpenAIVectorClient()

        # Upload files
        files = client.upload_files_from_directory("output/20251110_115900")

        # Create vector store
        vector_store = client.create_vector_store(
            name="SII FAQs - 2025-11-10",
            files=files,
            metadata={"extraction_date": "2025-11-10"}
        )

        # Use vector_store.vector_store_id in agent configuration
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var
        """
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

    def upload_file(
        self,
        file_path: str | Path,
        purpose: str = "assistants",
        expires_after_days: Optional[int] = 30
    ) -> UploadedFile:
        """
        Upload a single file to OpenAI

        Args:
            file_path: Path to the file to upload
            purpose: Purpose of the file (default: "assistants" for vector stores)
            expires_after_days: Number of days until file expires (default: 30)

        Returns:
            UploadedFile object with file metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Uploading file: {file_path.name}")

        # Prepare expiration config
        expires_after = None
        if expires_after_days:
            expires_after = {
                "anchor": "created_at",
                "seconds": expires_after_days * 24 * 60 * 60  # days to seconds
            }

        # Upload file
        with open(file_path, "rb") as f:
            file_obj = self.client.files.create(
                file=f,
                purpose=purpose,
                **({"expires_after": expires_after} if expires_after else {})
            )

        logger.info(f"File uploaded: {file_obj.id} ({file_path.name})")

        # Convert to our model
        return UploadedFile(
            file_id=file_obj.id,
            filename=file_obj.filename,
            purpose=file_obj.purpose,
            bytes=file_obj.bytes,
            created_at=datetime.fromtimestamp(file_obj.created_at),
            status=file_obj.status,
            expires_at=datetime.fromtimestamp(file_obj.expires_at) if hasattr(file_obj, 'expires_at') and file_obj.expires_at else None
        )

    def upload_files_from_directory(
        self,
        directory: str | Path,
        pattern: str = "*.md",
        exclude_index: bool = True,
        purpose: str = "assistants",
        expires_after_days: Optional[int] = 30
    ) -> List[UploadedFile]:
        """
        Upload all files from a directory matching a pattern

        Args:
            directory: Directory containing files to upload
            pattern: Glob pattern for files (default: "*.md")
            exclude_index: Skip INDEX.md file (default: True)
            purpose: Purpose of the files (default: "assistants")
            expires_after_days: Number of days until files expire (default: 30)

        Returns:
            List of UploadedFile objects
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        # Find all matching files
        files = sorted(directory.glob(pattern))

        if exclude_index:
            files = [f for f in files if f.name.lower() != "index.md"]

        logger.info(f"Found {len(files)} files to upload from {directory}")

        uploaded_files = []
        for file_path in files:
            try:
                uploaded_file = self.upload_file(
                    file_path,
                    purpose=purpose,
                    expires_after_days=expires_after_days
                )
                uploaded_files.append(uploaded_file)
            except Exception as e:
                logger.error(f"Failed to upload {file_path.name}: {e}")

        logger.info(f"Successfully uploaded {len(uploaded_files)}/{len(files)} files")
        return uploaded_files

    def list_files(self, purpose: Optional[str] = None) -> List[UploadedFile]:
        """
        List all uploaded files

        Args:
            purpose: Filter by purpose (e.g., "assistants")

        Returns:
            List of UploadedFile objects
        """
        logger.info("Listing uploaded files...")

        params = {}
        if purpose:
            params["purpose"] = purpose

        files_page = self.client.files.list(**params)

        uploaded_files = []
        for file_obj in files_page.data:
            uploaded_files.append(UploadedFile(
                file_id=file_obj.id,
                filename=file_obj.filename,
                purpose=file_obj.purpose,
                bytes=file_obj.bytes,
                created_at=datetime.fromtimestamp(file_obj.created_at),
                status=file_obj.status,
                expires_at=datetime.fromtimestamp(file_obj.expires_at) if hasattr(file_obj, 'expires_at') and file_obj.expires_at else None
            ))

        logger.info(f"Found {len(uploaded_files)} files")
        return uploaded_files

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from OpenAI

        Args:
            file_id: ID of the file to delete

        Returns:
            True if successful
        """
        logger.info(f"Deleting file: {file_id}")

        try:
            self.client.files.delete(file_id)
            logger.info(f"File deleted: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False

    def create_vector_store(
        self,
        name: str,
        files: Optional[List[UploadedFile]] = None,
        file_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> VectorStoreInfo:
        """
        Create a new vector store

        Args:
            name: Name of the vector store
            files: List of UploadedFile objects to add
            file_ids: List of file IDs to add (alternative to files)
            metadata: Optional metadata for the vector store

        Returns:
            VectorStoreInfo object
        """
        logger.info(f"Creating vector store: {name}")

        # Prepare file_ids list
        if files:
            file_ids = [f.file_id for f in files]
        elif not file_ids:
            file_ids = []

        # Create vector store
        vector_store = self.client.vector_stores.create(
            name=name,
            file_ids=file_ids,
            metadata=metadata or {}
        )

        logger.info(f"Vector store created: {vector_store.id} ({name})")

        return VectorStoreInfo(
            vector_store_id=vector_store.id,
            name=vector_store.name,
            created_at=datetime.fromtimestamp(vector_store.created_at),
            file_counts=vector_store.file_counts,
            status=vector_store.status,
            metadata=vector_store.metadata
        )

    def create_vector_store_batch(
        self,
        vector_store_id: str,
        files: List[UploadedFile],
        topic_name: Optional[str] = None,
        subtopic_name: Optional[str] = None,
        chunking_strategy: Optional[Dict[str, Any]] = None
    ) -> VectorStoreBatch:
        """
        Add a batch of files to a vector store with metadata

        Args:
            vector_store_id: ID of the vector store
            files: List of UploadedFile objects to add
            topic_name: Optional topic name for metadata
            subtopic_name: Optional subtopic name for metadata
            chunking_strategy: Optional chunking configuration
                Example: {
                    "type": "static",
                    "max_chunk_size_tokens": 1200,
                    "chunk_overlap_tokens": 200
                }

        Returns:
            VectorStoreBatch object
        """
        logger.info(f"Creating batch for vector store {vector_store_id} with {len(files)} files")

        # Prepare file configurations
        file_configs = []
        for file in files:
            config: Dict[str, Any] = {"file_id": file.file_id}

            # Add attributes (topic/subtopic metadata)
            attributes = {}
            if topic_name:
                attributes["topic"] = topic_name
            if subtopic_name:
                attributes["subtopic"] = subtopic_name

            if attributes:
                config["attributes"] = attributes

            # Add chunking strategy if provided
            if chunking_strategy:
                config["chunking_strategy"] = chunking_strategy

            file_configs.append(config)

        # Create batch
        batch = self.client.vector_stores.file_batches.create(
            vector_store_id=vector_store_id,
            files=file_configs
        )

        logger.info(f"Batch created: {batch.id}")

        return VectorStoreBatch(
            batch_id=batch.id,
            vector_store_id=batch.vector_store_id,
            status=batch.status,
            file_counts=batch.file_counts,
            created_at=datetime.fromtimestamp(batch.created_at),
            metadata={
                "topic": topic_name,
                "subtopic": subtopic_name
            } if topic_name or subtopic_name else None
        )

    def get_vector_store_batch(
        self,
        vector_store_id: str,
        batch_id: str
    ) -> VectorStoreBatch:
        """
        Retrieve information about a vector store batch

        Args:
            vector_store_id: ID of the vector store
            batch_id: ID of the batch

        Returns:
            VectorStoreBatch object
        """
        logger.info(f"Retrieving batch {batch_id} from vector store {vector_store_id}")

        batch = self.client.vector_stores.file_batches.retrieve(
            vector_store_id=vector_store_id,
            batch_id=batch_id
        )

        return VectorStoreBatch(
            batch_id=batch.id,
            vector_store_id=batch.vector_store_id,
            status=batch.status,
            file_counts=batch.file_counts,
            created_at=datetime.fromtimestamp(batch.created_at)
        )

    def list_vector_stores(self) -> List[VectorStoreInfo]:
        """
        List all vector stores

        Returns:
            List of VectorStoreInfo objects
        """
        logger.info("Listing vector stores...")

        vector_stores_page = self.client.vector_stores.list()

        vector_stores = []
        for vs in vector_stores_page.data:
            vector_stores.append(VectorStoreInfo(
                vector_store_id=vs.id,
                name=vs.name,
                created_at=datetime.fromtimestamp(vs.created_at),
                file_counts=vs.file_counts,
                status=vs.status,
                metadata=vs.metadata
            ))

        logger.info(f"Found {len(vector_stores)} vector stores")
        return vector_stores

    def delete_vector_store(self, vector_store_id: str) -> bool:
        """
        Delete a vector store

        Args:
            vector_store_id: ID of the vector store to delete

        Returns:
            True if successful
        """
        logger.info(f"Deleting vector store: {vector_store_id}")

        try:
            self.client.vector_stores.delete(vector_store_id)
            logger.info(f"Vector store deleted: {vector_store_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector store {vector_store_id}: {e}")
            return False

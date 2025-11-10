"""
Integration between SII FAQ extraction and OpenAI Vector Stores

This module provides high-level functions to:
1. Extract FAQs from SII
2. Upload to OpenAI
3. Create vector stores for file search
4. Automatically register vector stores in vector_stores.json
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.integrations.sii_faq.client import SIIFAQClient
from app.integrations.sii_faq.models import FAQTopic
from app.integrations.openai_vectors.client import OpenAIVectorClient
from app.integrations.openai_vectors.models import VectorStoreInfo, UploadedFile

logger = logging.getLogger(__name__)

# Path to vector stores registry
VECTOR_STORES_JSON = Path(__file__).parent / "vector_stores.json"

# Name of uploaded files cache in each output directory
UPLOADED_FILES_CACHE = "uploaded_files.json"


class FAQVectorizer:
    """
    High-level interface for creating vector stores from SII FAQs

    Usage:
        # Extract and vectorize all FAQs
        vectorizer = FAQVectorizer()
        vector_store = vectorizer.extract_and_vectorize(
            name="SII FAQs - Complete",
            limit_topics=None  # Extract all
        )
        print(f"Vector Store ID: {vector_store.vector_store_id}")

        # Vectorize from existing extraction
        vectorizer = FAQVectorizer()
        vector_store = vectorizer.vectorize_from_directory(
            directory="app/integrations/sii_faq/output/20251110_115900",
            name="SII FAQs - Test"
        )
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize FAQ vectorizer

        Args:
            openai_api_key: OpenAI API key (optional, reads from env if not provided)
        """
        self.openai_client = OpenAIVectorClient(api_key=openai_api_key)

    def _load_registry(self) -> Dict[str, Any]:
        """Load vector stores registry from JSON file"""
        if not VECTOR_STORES_JSON.exists():
            return {"vector_stores": [], "description": "Mapping between FAQ extraction versions and OpenAI vector store IDs"}

        with open(VECTOR_STORES_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_registry(self, registry: Dict[str, Any]):
        """Save vector stores registry to JSON file"""
        with open(VECTOR_STORES_JSON, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

    def _load_uploaded_files_cache(self, directory: Path) -> Dict[str, str]:
        """
        Load uploaded files cache from directory

        Args:
            directory: Path to extraction directory

        Returns:
            Dictionary mapping filename to file_id
        """
        cache_file = directory / UPLOADED_FILES_CACHE
        if not cache_file.exists():
            return {}

        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_uploaded_files_cache(self, directory: Path, cache: Dict[str, str]):
        """
        Save uploaded files cache to directory

        Args:
            directory: Path to extraction directory
            cache: Dictionary mapping filename to file_id
        """
        cache_file = directory / UPLOADED_FILES_CACHE
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)

    def _register_vector_store(
        self,
        vector_store: VectorStoreInfo,
        version: str,
        topic_count: int,
        file_count: int
    ):
        """
        Register a new vector store in the JSON registry

        Args:
            vector_store: VectorStoreInfo object
            version: Version timestamp (e.g., "20251110_115900")
            topic_count: Number of topics extracted
            file_count: Number of files uploaded
        """
        logger.info(f"Registering vector store {vector_store.vector_store_id} in registry")

        registry = self._load_registry()

        # Check if already exists
        existing = [vs for vs in registry["vector_stores"] if vs["vector_store_id"] == vector_store.vector_store_id]
        if existing:
            logger.warning(f"Vector store {vector_store.vector_store_id} already exists in registry")
            return

        # Add new entry
        entry = {
            "version": version,
            "vector_store_id": vector_store.vector_store_id,
            "name": vector_store.name,
            "created_at": vector_store.created_at.isoformat(),
            "topic_count": topic_count,
            "file_count": file_count,
            "status": "active"
        }

        registry["vector_stores"].append(entry)
        self._save_registry(registry)

        logger.info(f"Vector store registered: {vector_store.vector_store_id}")

    def _get_version_from_directory(self, directory: Path) -> str:
        """
        Extract version timestamp from directory name

        Args:
            directory: Path to extraction directory

        Returns:
            Version string (e.g., "20251110_115900")
        """
        # Directory name is the version (e.g., "20251110_115900")
        return directory.name

    def _count_topics_from_directory(self, directory: Path) -> int:
        """
        Count number of unique topics from directory files

        Args:
            directory: Path to extraction directory

        Returns:
            Number of unique topics
        """
        # Parse INDEX.md to get topic count
        index_file = directory / "INDEX.md"
        if not index_file.exists():
            return 0

        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Look for "**Total de temas:** X"
            import re
            match = re.search(r'\*\*Total de temas:\*\* (\d+)', content)
            if match:
                return int(match.group(1))

        return 0

    def extract_and_vectorize(
        self,
        name: str,
        limit_topics: Optional[int] = None,
        expires_after_days: int = 30,
        chunking_strategy: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> VectorStoreInfo:
        """
        Extract FAQs from SII and create a vector store

        Args:
            name: Name for the vector store
            limit_topics: Limit number of topics to extract (None = all)
            expires_after_days: Days until files expire (default: 30, max: 30)
            chunking_strategy: Optional chunking config for better search
                Example: {
                    "type": "static",
                    "max_chunk_size_tokens": 1200,
                    "chunk_overlap_tokens": 200
                }
            metadata: Optional metadata for the vector store

        Returns:
            VectorStoreInfo object with vector_store_id
        """
        logger.info(f"Starting FAQ extraction and vectorization: {name}")

        # Step 1: Extract FAQs
        logger.info("Step 1: Extracting FAQs from SII...")
        with SIIFAQClient() as faq_client:
            topics = faq_client.extract_all_faqs(limit_topics=limit_topics)
            version_dir = faq_client.export_to_markdown(topics)

        logger.info(f"FAQs extracted to: {version_dir}")

        # Step 2: Upload to OpenAI
        logger.info("Step 2: Uploading files to OpenAI...")
        vector_store = self.vectorize_from_directory(
            directory=version_dir,
            name=name,
            expires_after_days=expires_after_days,
            chunking_strategy=chunking_strategy,
            metadata=metadata
        )

        logger.info(f"Vector store created: {vector_store.vector_store_id}")
        return vector_store

    def vectorize_from_directory(
        self,
        directory: str | Path,
        name: str,
        expires_after_days: int = 30,
        chunking_strategy: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> VectorStoreInfo:
        """
        Create a vector store from an existing FAQ extraction directory

        Args:
            directory: Path to extraction directory (e.g., "output/20251110_115900")
            name: Name for the vector store
            expires_after_days: Days until files expire (default: 30, max: 30)
            chunking_strategy: Optional chunking config
            metadata: Optional metadata for the vector store

        Returns:
            VectorStoreInfo object with vector_store_id
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        logger.info(f"Vectorizing FAQs from: {directory}")

        # Load uploaded files cache
        uploaded_cache = self._load_uploaded_files_cache(directory)
        logger.info(f"Found {len(uploaded_cache)} files in cache")

        # Find all markdown files (excluding INDEX.md and uploaded_files.json)
        all_files = sorted(directory.glob("*.md"))
        all_files = [f for f in all_files if f.name.lower() not in ["index.md", UPLOADED_FILES_CACHE]]

        logger.info(f"Found {len(all_files)} markdown files in directory")

        # Upload files (skip already uploaded)
        uploaded_files = []
        files_to_upload = []

        for file_path in all_files:
            if file_path.name in uploaded_cache:
                # File already uploaded - reuse file_id
                logger.info(f"Reusing cached file_id for: {file_path.name}")
                # Create UploadedFile object from cached file_id
                uploaded_files.append(UploadedFile(
                    file_id=uploaded_cache[file_path.name],
                    filename=file_path.name,
                    purpose="assistants",
                    bytes=file_path.stat().st_size,
                    created_at=datetime.now(),
                    status="processed"
                ))
            else:
                files_to_upload.append(file_path)

        # Upload new files
        if files_to_upload:
            logger.info(f"Uploading {len(files_to_upload)} new files...")
            for file_path in files_to_upload:
                try:
                    uploaded_file = self.openai_client.upload_file(
                        file_path,
                        purpose="assistants",
                        expires_after_days=expires_after_days
                    )
                    uploaded_files.append(uploaded_file)

                    # Update cache
                    uploaded_cache[file_path.name] = uploaded_file.file_id

                except Exception as e:
                    logger.error(f"Failed to upload {file_path.name}: {e}")
                    raise

            # Save updated cache
            self._save_uploaded_files_cache(directory, uploaded_cache)
            logger.info(f"Updated cache with {len(files_to_upload)} new files")
        else:
            logger.info("All files already uploaded, using cached file_ids")

        if not uploaded_files:
            raise ValueError(f"No files available from {directory}")

        # Create vector store
        vector_store = self.openai_client.create_vector_store(
            name=name,
            files=uploaded_files,
            metadata=metadata or {}
        )

        logger.info(f"Vector store created: {vector_store.vector_store_id} with {len(uploaded_files)} files")

        # Register in JSON
        version = self._get_version_from_directory(directory)
        topic_count = self._count_topics_from_directory(directory)
        self._register_vector_store(
            vector_store=vector_store,
            version=version,
            topic_count=topic_count,
            file_count=len(uploaded_files)
        )

        return vector_store

    def vectorize_by_topic(
        self,
        topics: List[FAQTopic],
        vector_store_name: str,
        version_dir: Path,
        chunking_strategy: Optional[Dict[str, Any]] = None
    ) -> VectorStoreInfo:
        """
        Create a vector store and organize files by topic with metadata

        This method uploads files in batches, adding topic/subtopic metadata
        for better filtering in agent queries.

        Args:
            topics: List of FAQTopic objects
            vector_store_name: Name for the vector store
            version_dir: Directory containing exported markdown files
            chunking_strategy: Optional chunking config

        Returns:
            VectorStoreInfo object
        """
        logger.info(f"Creating vector store with topic organization: {vector_store_name}")

        # Create empty vector store first
        vector_store = self.openai_client.create_vector_store(
            name=vector_store_name,
            files=None,
            metadata={"organized_by_topic": True}
        )

        # Process each topic
        for topic in topics:
            logger.info(f"Processing topic: {topic.name}")

            # Find all files for this topic
            topic_safe = self._sanitize_filename(topic.name)
            pattern = f"{topic_safe}_*.md"

            topic_files = list(version_dir.glob(pattern))

            if not topic_files:
                logger.warning(f"No files found for topic: {topic.name}")
                continue

            # Upload files for this topic
            uploaded_files = []
            for file_path in topic_files:
                uploaded_file = self.openai_client.upload_file(
                    file_path=file_path,
                    purpose="assistants"
                )
                uploaded_files.append(uploaded_file)

            # Add batch with topic metadata
            if uploaded_files:
                batch = self.openai_client.create_vector_store_batch(
                    vector_store_id=vector_store.vector_store_id,
                    files=uploaded_files,
                    topic_name=topic.name,
                    chunking_strategy=chunking_strategy
                )
                logger.info(f"Batch created for topic '{topic.name}': {batch.batch_id}")

        logger.info(f"Vector store fully populated: {vector_store.vector_store_id}")
        return vector_store

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string to be used as a filename (same as FAQ client)

        Args:
            name: String to sanitize

        Returns:
            Safe filename string
        """
        safe = re.sub(r'[^\w\s-]', '', name)
        safe = re.sub(r'[-\s]+', '_', safe)
        safe = safe[:200]
        return safe.lower()

    def list_vector_stores(self) -> List[VectorStoreInfo]:
        """
        List all available vector stores

        Returns:
            List of VectorStoreInfo objects
        """
        return self.openai_client.list_vector_stores()

    def delete_vector_store(self, vector_store_id: str, mark_deprecated: bool = True) -> bool:
        """
        Delete a vector store and optionally mark as deprecated in registry

        Args:
            vector_store_id: ID of the vector store to delete
            mark_deprecated: Mark as deprecated in registry instead of removing (default: True)

        Returns:
            True if successful
        """
        success = self.openai_client.delete_vector_store(vector_store_id)

        if success and mark_deprecated:
            # Mark as deprecated in registry
            registry = self._load_registry()
            for vs in registry["vector_stores"]:
                if vs["vector_store_id"] == vector_store_id:
                    vs["status"] = "deprecated"
                    break
            self._save_registry(registry)

        return success

    def get_latest_vector_store_id(self) -> Optional[str]:
        """
        Get the vector_store_id of the most recent active vector store

        Returns:
            Vector store ID or None if no active stores found
        """
        registry = self._load_registry()

        # Filter active vector stores
        active_stores = [vs for vs in registry["vector_stores"] if vs.get("status") == "active"]

        if not active_stores:
            return None

        # Sort by created_at descending
        active_stores.sort(key=lambda x: x["created_at"], reverse=True)

        return active_stores[0]["vector_store_id"]

    def get_vector_store_by_version(self, version: str) -> Optional[Dict[str, Any]]:
        """
        Get vector store info by version timestamp

        Args:
            version: Version timestamp (e.g., "20251110_115900")

        Returns:
            Vector store entry or None if not found
        """
        registry = self._load_registry()

        for vs in registry["vector_stores"]:
            if vs["version"] == version:
                return vs

        return None

    def list_registered_vector_stores(self, only_active: bool = True) -> List[Dict[str, Any]]:
        """
        List all registered vector stores from JSON registry

        Args:
            only_active: Only return active stores (default: True)

        Returns:
            List of vector store entries
        """
        registry = self._load_registry()

        if only_active:
            return [vs for vs in registry["vector_stores"] if vs.get("status") == "active"]

        return registry["vector_stores"]

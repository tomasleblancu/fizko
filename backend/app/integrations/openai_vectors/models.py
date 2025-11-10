"""
Data models for OpenAI Vector Store integration
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class UploadedFile:
    """
    Represents a file uploaded to OpenAI
    """
    file_id: str
    filename: str
    purpose: str
    bytes: int
    created_at: datetime
    status: str
    expires_at: Optional[datetime] = None


@dataclass
class VectorStoreInfo:
    """
    Represents a Vector Store in OpenAI
    """
    vector_store_id: str
    name: str
    created_at: datetime
    file_counts: Dict[str, int]  # e.g., {"total": 10, "completed": 10}
    status: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class VectorStoreBatch:
    """
    Represents a batch of files added to a Vector Store
    """
    batch_id: str
    vector_store_id: str
    status: str
    file_counts: Dict[str, int]
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

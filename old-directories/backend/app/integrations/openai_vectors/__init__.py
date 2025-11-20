"""
OpenAI Vector Store integration for SII FAQs

This module provides functionality to:
1. Upload FAQ content as files to OpenAI
2. Create vector stores for file search
3. Manage vector store file batches with metadata
"""

from app.integrations.openai_vectors.client import OpenAIVectorClient
from app.integrations.openai_vectors.models import (
    UploadedFile,
    VectorStoreInfo,
    VectorStoreBatch
)

__all__ = [
    'OpenAIVectorClient',
    'UploadedFile',
    'VectorStoreInfo',
    'VectorStoreBatch'
]

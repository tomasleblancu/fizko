"""
Mem0 Client - Async client for Mem0 memory service.

This module provides a singleton Mem0 client for long-term memory storage.
Mem0 is used by AI agents to store and retrieve user and company memories.
"""

import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Global Mem0 client (initialized lazily)
_mem0_client: Optional["AsyncMemoryClient"] = None
_mem0_client_loop: Optional[asyncio.AbstractEventLoop] = None


def get_mem0_client() -> "AsyncMemoryClient":
    """
    Get or create async Mem0 client.

    Detects if event loop has changed (e.g., in Celery tasks) and recreates
    the client if needed to avoid "Event loop is closed" errors.

    Returns:
        AsyncMemoryClient instance

    Raises:
        ValueError: If MEM0_API_KEY environment variable is not set
        ImportError: If mem0 package is not installed
    """
    global _mem0_client, _mem0_client_loop

    # Import here to avoid ImportError if mem0 is not installed
    try:
        from mem0 import AsyncMemoryClient
    except ImportError:
        raise ImportError(
            "mem0 package not installed. Install with: pip install mem0ai"
        )

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - will be created when needed
        current_loop = None

    # Recreate client if loop changed or client doesn't exist
    if _mem0_client is None or _mem0_client_loop != current_loop:
        api_key = os.getenv("MEM0_API_KEY")
        if not api_key:
            raise ValueError("MEM0_API_KEY environment variable not set")

        # Initialize Mem0 async client with API key
        _mem0_client = AsyncMemoryClient(api_key=api_key)
        _mem0_client_loop = current_loop

        if current_loop:
            logger.info(f"✨ Mem0 async client initialized for event loop {id(current_loop)}")
        else:
            logger.info("✨ Mem0 async client initialized")

    return _mem0_client


def is_mem0_configured() -> bool:
    """
    Check if Mem0 is configured.

    Returns:
        True if MEM0_API_KEY is set, False otherwise
    """
    return bool(os.getenv("MEM0_API_KEY"))

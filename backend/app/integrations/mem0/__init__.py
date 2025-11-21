"""
Mem0 Integration - Long-term memory storage for AI agents.

This module provides integration with the Mem0 service for storing
and retrieving user and company memories.

Usage:
    from app.integrations.mem0 import get_mem0_client, is_mem0_configured

    if is_mem0_configured():
        mem0 = get_mem0_client()
        result = await mem0.add(messages=[...], user_id="...")
"""

from .client import get_mem0_client, is_mem0_configured

__all__ = [
    "get_mem0_client",
    "is_mem0_configured",
]

"""Memory tools for storing and retrieving user and company context.

This module provides dual memory systems:
- User Memory: Personal preferences and information specific to each user
- Company Memory: Shared knowledge and information across the company
"""

from .memory_tools import (
    # User memory tools
    search_user_memory,
    save_user_memory,
    # Company memory tools
    search_company_memory,
    save_company_memory,
    # Legacy (deprecated)
    search_memory,
    save_memory,
)

__all__ = [
    # User memory
    "search_user_memory",
    "save_user_memory",
    # Company memory
    "search_company_memory",
    "save_company_memory",
    # Legacy (deprecated)
    "search_memory",
    "save_memory",
]

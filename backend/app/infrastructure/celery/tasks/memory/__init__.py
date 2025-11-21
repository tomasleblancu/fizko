"""
Memory Celery tasks for Backend V2.

This module contains all Celery tasks related to memory operations:
- Loading company memories from existing data
- Loading user memories from existing data
- Batch processing for all companies/users

Key differences from agent tools:
- These are background tasks, not real-time agent tools
- Focus on initial data loading and bulk operations
- Use the memory service layer for all memory operations
"""
from .load import (
    load_company_memories,
    load_user_memories,
    load_all_companies_memories,
    load_all_users_memories,
)

__all__ = [
    "load_company_memories",
    "load_user_memories",
    "load_all_companies_memories",
    "load_all_users_memories",
]

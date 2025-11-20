"""Utility functions for agent tools using Supabase repositories."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config.supabase import SupabaseClient

from app.config.supabase import get_supabase_client


def get_supabase() -> SupabaseClient:
    """
    Get Supabase client for use in agent tools.

    Returns:
        SupabaseClient instance with access to all repositories
    """
    return get_supabase_client()

"""Supabase client configuration."""

import os
from functools import lru_cache

from supabase import Client, create_client


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get a Supabase client instance.

    This function is cached to reuse the same client across requests.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables"
        )

    return create_client(supabase_url, supabase_key)

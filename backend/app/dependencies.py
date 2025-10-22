"""Shared dependencies for FastAPI routes."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .config.database import get_db
from .core.auth import get_current_user


async def get_current_active_user(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Get the current active user."""
    # You can add additional checks here (e.g., user is not banned)
    return user


async def get_current_user_id(
    user: dict[str, Any] = Depends(get_current_user),
) -> str:
    """Extract user ID from authenticated user."""
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    return user_id


async def require_auth(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Require authentication - raises 401 if not authenticated."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


async def get_db_session() -> AsyncSession:
    """Get database session dependency."""
    async for session in get_db():
        yield session

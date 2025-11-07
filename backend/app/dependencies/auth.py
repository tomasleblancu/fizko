"""Authentication and authorization dependencies."""

from __future__ import annotations

from typing import Any, Annotated

from fastapi import Depends, HTTPException, status

from ..core.auth import get_current_user as _get_current_user


async def get_current_active_user(
    user: dict[str, Any] = Depends(_get_current_user),
) -> dict[str, Any]:
    """
    Get the current active user.

    Args:
        user: JWT payload from get_current_user

    Returns:
        User data dictionary with fields like 'sub' (user_id), 'email', etc.
    """
    # You can add additional checks here (e.g., user is not banned)
    return user


async def get_current_user_id(
    user: dict[str, Any] = Depends(_get_current_user),
) -> str:
    """
    Extract user ID from authenticated user.

    Args:
        user: JWT payload from get_current_user

    Returns:
        User ID (UUID as string)

    Raises:
        HTTPException: If user ID not found in token
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    return user_id


async def require_auth(
    user: dict[str, Any] = Depends(_get_current_user),
) -> dict[str, Any]:
    """
    Require authentication - raises 401 if not authenticated.

    Use this as a router-level dependency to protect all endpoints:
        router = APIRouter(dependencies=[Depends(require_auth)])

    Args:
        user: JWT payload from get_current_user

    Returns:
        User data dictionary

    Raises:
        HTTPException: If user is not authenticated
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


# =============================================================================
# Type Aliases for Convenience
# =============================================================================

# These make endpoint signatures cleaner:
# async def my_endpoint(user: CurrentUserDep):
#     ...

CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_active_user)]
CurrentUserIdDep = Annotated[str, Depends(get_current_user_id)]


__all__ = [
    "get_current_active_user",
    "get_current_user_id",
    "require_auth",
    "CurrentUserDep",
    "CurrentUserIdDep",
]

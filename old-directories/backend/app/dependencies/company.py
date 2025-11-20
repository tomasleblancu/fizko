"""Company resolution dependencies."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from ..db.models import Session as SessionModel
from .auth import get_current_user_id


async def get_user_company_id(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """
    Get the company_id from the user's active session.

    This ensures that operations are always associated with the company
    the user is currently accessing. Most endpoints should use this
    dependency to get the company context.

    Args:
        current_user_id: User ID from JWT token
        db: Database session

    Returns:
        UUID: The company_id from the active session

    Raises:
        HTTPException: If no active session is found for the user

    Example:
        ```python
        @router.get("/documents")
        async def get_documents(
            company_id: UUID = Depends(get_user_company_id)
        ):
            # Use company_id to fetch company-specific data
            return await get_company_documents(company_id)
        ```
    """
    # Find active session for this user
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.user_id == UUID(current_user_id))
        .where(SessionModel.is_active == True)
        .order_by(desc(SessionModel.last_accessed_at))
        .limit(1)
    )
    session = result.scalar_one_or_none()

    if not session or not session.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active company session found. Please select a company first."
        )

    return session.company_id


# =============================================================================
# Type Aliases for Convenience
# =============================================================================

CompanyIdDep = Annotated[UUID, Depends(get_user_company_id)]


__all__ = [
    "get_user_company_id",
    "CompanyIdDep",
]

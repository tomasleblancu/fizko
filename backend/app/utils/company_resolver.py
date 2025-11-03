"""Company resolver utility - Get user's primary company from sessions."""

from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Session


async def get_user_primary_company_id(
    user_id: str | UUID,
    db: AsyncSession
) -> Optional[UUID]:
    """
    Get the primary company ID for a user based on their active sessions.

    Returns the company_id from the most recently accessed active session.
    If no active session is found, returns None.

    Args:
        user_id: The user's ID (string or UUID)
        db: Database session

    Returns:
        UUID of the primary company, or None if no active session found
    """
    if isinstance(user_id, str):
        user_id = UUID(user_id)

    # Get the most recently accessed active session
    stmt = select(Session).where(
        Session.user_id == user_id,
        Session.is_active == True
    ).order_by(Session.last_accessed_at.desc().nullsfirst())

    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session:
        return session.company_id

    return None

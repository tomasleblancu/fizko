"""Dependencies for scheduled tasks router."""

from datetime import datetime
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.db.models import Session as SessionModel
from app.dependencies import get_current_user_id


async def get_user_company_id(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """
    Get the company_id from the user's active session.

    This ensures that scheduled tasks are always associated with the company
    the user is currently accessing.

    Raises:
        HTTPException: If no active session is found for the user.

    Returns:
        UUID: The company_id from the active session.
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

"""Repository for Profile management."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    """Repository for managing user profiles."""

    def __init__(self, db: AsyncSession):
        super().__init__(Profile, db)

    async def get_by_user_id(self, user_id: UUID) -> Optional[Profile]:
        """
        Get profile for a user.

        Args:
            user_id: UUID of the user

        Returns:
            Profile instance or None if not found
        """
        result = await self.db.execute(
            select(Profile).where(Profile.id == user_id)
        )
        return result.scalar_one_or_none()

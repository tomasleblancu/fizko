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

    async def is_admin(self, user_id: UUID) -> bool:
        """
        Check if a user has admin-kaiken role.

        Args:
            user_id: UUID of the user

        Returns:
            True if user is admin-kaiken, False otherwise
        """
        profile = await self.get_by_user_id(user_id)
        return profile is not None and profile.rol == "admin-kaiken"

    async def get_admin_user(self, user_id: UUID) -> Optional[Profile]:
        """
        Get profile only if user is admin-kaiken.

        Args:
            user_id: UUID of the user

        Returns:
            Profile instance if user is admin, None otherwise
        """
        profile = await self.get_by_user_id(user_id)
        if profile and profile.rol == "admin-kaiken":
            return profile
        return None

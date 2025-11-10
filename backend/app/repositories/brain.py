"""
Brain Repository Pattern Implementation.

Provides repository classes for UserBrain and CompanyBrain models with
specialized methods for managing memory records.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from app.db.models import UserBrain, CompanyBrain


class UserBrainRepository(BaseRepository[UserBrain]):
    """
    Repository for UserBrain model operations.

    Provides methods to manage user memory records including
    slug-based lookups and updates.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize UserBrain repository.

        Args:
            db: Async database session
        """
        super().__init__(UserBrain, db)

    async def get_by_user_and_slug(
        self,
        user_id: UUID,
        slug: str
    ) -> Optional[UserBrain]:
        """
        Get a user brain record by user_id and slug.

        Args:
            user_id: User UUID
            slug: Memory slug identifier

        Returns:
            UserBrain instance or None if not found
        """
        stmt = select(UserBrain).where(
            UserBrain.user_id == user_id,
            UserBrain.slug == slug
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_memory_id(self, memory_id: str) -> Optional[UserBrain]:
        """
        Get a user brain record by Mem0 memory_id.

        Args:
            memory_id: Mem0 memory identifier

        Returns:
            UserBrain instance or None if not found
        """
        stmt = select(UserBrain).where(UserBrain.memory_id == memory_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: UUID) -> list[UserBrain]:
        """
        Get all brain records for a specific user.

        Args:
            user_id: User UUID

        Returns:
            List of UserBrain instances
        """
        stmt = select(UserBrain).where(UserBrain.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_all_by_user(self, user_id: UUID) -> int:
        """
        Delete all brain records for a specific user.

        Args:
            user_id: User UUID

        Returns:
            Number of deleted records
        """
        from sqlalchemy import delete
        stmt = delete(UserBrain).where(UserBrain.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.rowcount


class CompanyBrainRepository(BaseRepository[CompanyBrain]):
    """
    Repository for CompanyBrain model operations.

    Provides methods to manage company memory records including
    slug-based lookups and updates.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize CompanyBrain repository.

        Args:
            db: Async database session
        """
        super().__init__(CompanyBrain, db)

    async def get_by_company_and_slug(
        self,
        company_id: UUID,
        slug: str
    ) -> Optional[CompanyBrain]:
        """
        Get a company brain record by company_id and slug.

        Args:
            company_id: Company UUID
            slug: Memory slug identifier

        Returns:
            CompanyBrain instance or None if not found
        """
        stmt = select(CompanyBrain).where(
            CompanyBrain.company_id == company_id,
            CompanyBrain.slug == slug
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_memory_id(self, memory_id: str) -> Optional[CompanyBrain]:
        """
        Get a company brain record by Mem0 memory_id.

        Args:
            memory_id: Mem0 memory identifier

        Returns:
            CompanyBrain instance or None if not found
        """
        stmt = select(CompanyBrain).where(CompanyBrain.memory_id == memory_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_company(self, company_id: UUID) -> list[CompanyBrain]:
        """
        Get all brain records for a specific company.

        Args:
            company_id: Company UUID

        Returns:
            List of CompanyBrain instances
        """
        stmt = select(CompanyBrain).where(CompanyBrain.company_id == company_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_all_by_company(self, company_id: UUID) -> int:
        """
        Delete all brain records for a specific company.

        Args:
            company_id: Company UUID

        Returns:
            Number of deleted records
        """
        from sqlalchemy import delete
        stmt = delete(CompanyBrain).where(CompanyBrain.company_id == company_id)
        result = await self.db.execute(stmt)
        return result.rowcount

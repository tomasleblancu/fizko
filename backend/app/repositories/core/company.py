"""Repository for company management."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """Repository for managing companies."""

    def __init__(self, db: AsyncSession):
        super().__init__(Company, db)

    async def find_all(self) -> List[Company]:
        """
        Get all companies.

        Returns:
            List of all Company instances
        """
        result = await self.db.execute(select(Company))
        return list(result.scalars().all())

    async def find_by_rut(self, rut: str) -> Optional[Company]:
        """
        Find a company by RUT.

        Args:
            rut: Company RUT

        Returns:
            Company instance or None if not found
        """
        result = await self.db.execute(
            select(Company).where(Company.rut == rut)
        )
        return result.scalar_one_or_none()

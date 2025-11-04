"""Repository for CompanyTaxInfo management."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CompanyTaxInfo
from app.repositories.base import BaseRepository


class CompanyTaxInfoRepository(BaseRepository[CompanyTaxInfo]):
    """Repository for managing company tax information."""

    def __init__(self, db: AsyncSession):
        super().__init__(CompanyTaxInfo, db)

    async def get_by_company(self, company_id: UUID) -> Optional[CompanyTaxInfo]:
        """
        Get tax info for a company.

        Args:
            company_id: UUID of the company

        Returns:
            CompanyTaxInfo instance or None if not found
        """
        result = await self.db.execute(
            select(CompanyTaxInfo).where(CompanyTaxInfo.company_id == company_id)
        )
        return result.scalar_one_or_none()

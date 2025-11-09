"""Repository for company management."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Company, Session as SessionModel
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """Repository for managing companies."""

    def __init__(self, db: AsyncSession):
        super().__init__(Company, db)

    async def find_all(
        self,
        with_tax_info: bool = False,
        order_by_created: bool = True
    ) -> List[Company]:
        """
        Get all companies.

        Args:
            with_tax_info: Whether to preload tax_info relationship
            order_by_created: Whether to order by created_at DESC

        Returns:
            List of all Company instances
        """
        stmt = select(Company)

        if with_tax_info:
            stmt = stmt.options(selectinload(Company.tax_info))

        if order_by_created:
            stmt = stmt.order_by(desc(Company.created_at))

        result = await self.db.execute(stmt)
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

    async def get_with_tax_info(self, company_id: UUID) -> Optional[Company]:
        """
        Get a company with tax_info preloaded.

        Args:
            company_id: Company UUID

        Returns:
            Company instance with tax_info or None
        """
        stmt = select(Company).options(
            selectinload(Company.tax_info)
        ).where(Company.id == company_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_companies_by_user(
        self,
        user_id: UUID,
        with_tax_info: bool = False
    ) -> List[Company]:
        """
        Get all companies accessible by a user (via sessions).

        Args:
            user_id: User UUID
            with_tax_info: Whether to preload tax_info relationship

        Returns:
            List of Company instances user has access to
        """
        stmt = (
            select(Company)
            .join(SessionModel, SessionModel.company_id == Company.id)
            .where(SessionModel.user_id == user_id)
            .order_by(desc(Company.created_at))
        )

        if with_tax_info:
            stmt = stmt.options(selectinload(Company.tax_info))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

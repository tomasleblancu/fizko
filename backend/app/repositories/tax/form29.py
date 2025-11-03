"""Repository for Form 29 management."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.form29 import Form29
from app.repositories.base import BaseRepository


class Form29Repository(BaseRepository[Form29]):
    """Repository for managing Form 29 (Monthly IVA declarations)."""

    def __init__(self, db: AsyncSession):
        super().__init__(Form29, db)

    async def find_by_company(
        self,
        company_id: UUID,
        period_year: Optional[int] = None,
        period_month: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Form29]:
        """
        Find Form 29 records by company with filters.

        Args:
            company_id: Company UUID
            period_year: Filter by year
            period_month: Filter by month
            status: Filter by status
            skip: Pagination offset
            limit: Max results

        Returns:
            List of Form29 instances
        """
        query = select(Form29).where(Form29.company_id == company_id)

        if period_year:
            query = query.where(Form29.period_year == period_year)

        if period_month:
            query = query.where(Form29.period_month == period_month)

        if status:
            query = query.where(Form29.status == status)

        query = query.order_by(
            desc(Form29.period_year),
            desc(Form29.period_month)
        )
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_by_period(
        self,
        company_id: UUID,
        period_year: int,
        period_month: int
    ) -> Optional[Form29]:
        """
        Find Form 29 for a specific period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)

        Returns:
            Form29 instance or None
        """
        query = select(Form29).where(
            Form29.company_id == company_id,
            Form29.period_year == period_year,
            Form29.period_month == period_month
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def exists_for_period(
        self,
        company_id: UUID,
        period_year: int,
        period_month: int
    ) -> bool:
        """
        Check if Form 29 exists for a specific period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)

        Returns:
            True if exists, False otherwise
        """
        query = select(func.count(Form29.id)).where(
            Form29.company_id == company_id,
            Form29.period_year == period_year,
            Form29.period_month == period_month
        )

        result = await self.db.execute(query)
        return result.scalar_one() > 0

"""Repository for payroll management."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.personnel import Payroll
from app.repositories.base import BaseRepository


class PayrollRepository(BaseRepository[Payroll]):
    """Repository for managing Payroll records."""

    def __init__(self, db: AsyncSession):
        super().__init__(Payroll, db)

    async def find_by_company(
        self,
        company_id: UUID,
        period_year: Optional[int] = None,
        period_month: Optional[int] = None,
        person_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payroll]:
        """
        Find payroll records by company with filters.

        Args:
            company_id: Company UUID
            period_year: Filter by year
            period_month: Filter by month
            person_id: Filter by person
            status: Filter by status (draft, approved, paid, closed)
            skip: Pagination offset
            limit: Max results

        Returns:
            List of Payroll instances
        """
        query = select(Payroll).where(Payroll.company_id == company_id)

        if period_year:
            query = query.where(Payroll.period_year == period_year)

        if period_month:
            query = query.where(Payroll.period_month == period_month)

        if person_id:
            query = query.where(Payroll.person_id == person_id)

        if status:
            query = query.where(Payroll.status == status)

        # Order by most recent first
        query = query.order_by(
            Payroll.period_year.desc(),
            Payroll.period_month.desc()
        )
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_by_period(
        self,
        company_id: UUID,
        period_year: int,
        period_month: int
    ) -> List[Payroll]:
        """
        Find all payroll records for a specific period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)

        Returns:
            List of Payroll instances
        """
        query = select(Payroll).where(
            Payroll.company_id == company_id,
            Payroll.period_year == period_year,
            Payroll.period_month == period_month
        ).order_by(Payroll.created_at)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_period_summary(
        self,
        company_id: UUID,
        period_year: int,
        period_month: int
    ) -> dict:
        """
        Get summary statistics for a payroll period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)

        Returns:
            Dictionary with summary statistics
        """
        query = select(
            func.count(Payroll.id).label('total_employees'),
            func.sum(Payroll.total_income).label('total_gross'),
            func.sum(Payroll.total_deductions).label('total_deductions'),
            func.sum(Payroll.net_salary).label('total_net')
        ).where(
            Payroll.company_id == company_id,
            Payroll.period_year == period_year,
            Payroll.period_month == period_month
        )

        result = await self.db.execute(query)
        row = result.one()

        return {
            'period_year': period_year,
            'period_month': period_month,
            'total_employees': row.total_employees or 0,
            'total_gross_salary': float(row.total_gross or 0),
            'total_deductions': float(row.total_deductions or 0),
            'total_net_salary': float(row.total_net or 0)
        }

    async def exists_for_person_period(
        self,
        company_id: UUID,
        person_id: UUID,
        period_year: int,
        period_month: int
    ) -> bool:
        """
        Check if payroll already exists for a person in a specific period.

        Args:
            company_id: Company UUID
            person_id: Person UUID
            period_year: Year
            period_month: Month (1-12)

        Returns:
            True if exists, False otherwise
        """
        query = select(func.count(Payroll.id)).where(
            Payroll.company_id == company_id,
            Payroll.person_id == person_id,
            Payroll.period_year == period_year,
            Payroll.period_month == period_month
        )

        result = await self.db.execute(query)
        return result.scalar_one() > 0

    async def update_status(
        self,
        payroll_id: UUID,
        status: str
    ) -> Optional[Payroll]:
        """
        Update payroll status.

        Args:
            payroll_id: Payroll UUID
            status: New status (draft, approved, paid, closed)

        Returns:
            Updated Payroll instance or None
        """
        return await self.update(payroll_id, status=status)

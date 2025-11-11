"""Repository for Form 29 management."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, desc, and_
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
        period_month: int,
        revision_number: Optional[int] = None
    ) -> Optional[Form29]:
        """
        Find Form 29 for a specific period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)
            revision_number: Optional revision number (defaults to latest non-cancelled)

        Returns:
            Form29 instance or None
        """
        query = select(Form29).where(
            Form29.company_id == company_id,
            Form29.period_year == period_year,
            Form29.period_month == period_month
        )

        if revision_number:
            query = query.where(Form29.revision_number == revision_number)
        else:
            # Get latest non-cancelled revision
            query = query.where(Form29.status != "cancelled")
            query = query.order_by(desc(Form29.revision_number))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def exists_for_period(
        self,
        company_id: UUID,
        period_year: int,
        period_month: int,
        exclude_cancelled: bool = True
    ) -> bool:
        """
        Check if Form 29 exists for a specific period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)
            exclude_cancelled: Whether to exclude cancelled forms

        Returns:
            True if exists, False otherwise
        """
        query = select(func.count(Form29.id)).where(
            Form29.company_id == company_id,
            Form29.period_year == period_year,
            Form29.period_month == period_month
        )

        if exclude_cancelled:
            query = query.where(Form29.status != "cancelled")

        result = await self.db.execute(query)
        return result.scalar_one() > 0

    async def get_latest_revision_number(
        self,
        company_id: UUID,
        period_year: int,
        period_month: int
    ) -> int:
        """
        Get the latest revision number for a period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)

        Returns:
            Latest revision number (0 if none exist)
        """
        query = select(func.max(Form29.revision_number)).where(
            Form29.company_id == company_id,
            Form29.period_year == period_year,
            Form29.period_month == period_month
        )

        result = await self.db.execute(query)
        return result.scalar_one() or 0

    async def create_draft(
        self,
        company_id: UUID,
        period_year: int,
        period_month: int,
        created_by_user_id: Optional[UUID] = None,
        **kwargs
    ) -> Form29:
        """
        Create a new Form29 draft.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)
            created_by_user_id: Optional user ID who created the draft
            **kwargs: Additional form data

        Returns:
            Created Form29 instance
        """
        # Get next revision number
        revision_number = await self.get_latest_revision_number(
            company_id, period_year, period_month
        ) + 1

        form29 = Form29(
            company_id=company_id,
            period_year=period_year,
            period_month=period_month,
            revision_number=revision_number,
            created_by_user_id=created_by_user_id,
            status="draft",
            validation_status="pending",
            payment_status="unpaid",
            **kwargs
        )

        self.db.add(form29)
        await self.db.flush()
        await self.db.refresh(form29)

        return form29

    async def update_validation(
        self,
        form29_id: UUID,
        validation_status: str,
        validation_errors: Optional[List[dict]] = None
    ) -> Optional[Form29]:
        """
        Update validation status and errors for a form.

        Args:
            form29_id: Form29 UUID
            validation_status: New validation status
            validation_errors: Optional validation errors

        Returns:
            Updated Form29 or None if not found
        """
        form29 = await self.get(form29_id)
        if not form29:
            return None

        form29.validation_status = validation_status
        form29.validation_errors = validation_errors or []

        # Auto-update status if validated successfully
        if validation_status == "valid" and form29.status == "draft":
            form29.status = "validated"

        await self.db.flush()
        await self.db.refresh(form29)

        return form29

    async def confirm_draft(
        self,
        form29_id: UUID,
        confirmed_by_user_id: UUID,
        confirmation_notes: Optional[str] = None
    ) -> Optional[Form29]:
        """
        Confirm a draft for submission.

        Args:
            form29_id: Form29 UUID
            confirmed_by_user_id: User ID who confirmed
            confirmation_notes: Optional notes

        Returns:
            Updated Form29 or None if not found
        """
        form29 = await self.get(form29_id)
        if not form29:
            return None

        form29.status = "confirmed"
        form29.confirmed_by_user_id = confirmed_by_user_id
        form29.confirmed_at = datetime.utcnow()
        form29.confirmation_notes = confirmation_notes

        await self.db.flush()
        await self.db.refresh(form29)

        return form29

    async def get_active_drafts(
        self,
        company_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Form29]:
        """
        Get all active drafts (status=draft).

        Args:
            company_id: Optional company filter
            skip: Pagination offset
            limit: Max results

        Returns:
            List of Form29 drafts
        """
        query = select(Form29).where(Form29.status == "draft")

        if company_id:
            query = query.where(Form29.company_id == company_id)

        query = query.order_by(
            desc(Form29.period_year),
            desc(Form29.period_month)
        ).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

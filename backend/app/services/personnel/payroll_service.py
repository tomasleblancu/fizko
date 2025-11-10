"""
Payroll Service - Business logic for payroll management.

This service layer encapsulates all business logic for payroll operations,
using repositories for data access.
"""

from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.db.models import Payroll, Person
from app.repositories.personnel import PayrollRepository, PersonRepository
from app.schemas.personnel import PayrollCreate, PayrollUpdate


class PayrollService:
    """
    Service for managing payroll operations.

    Handles all business logic related to payroll including:
    - Creation with validation
    - Updates and status changes
    - Querying with filters
    - Summary calculations
    - Approvals and payment tracking
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the payroll service.

        Args:
            db: Database session
        """
        self.db = db
        self.payroll_repo = PayrollRepository(db)
        self.person_repo = PersonRepository(db)

    async def create_payroll(self, payroll_data: PayrollCreate) -> Payroll:
        """
        Create a new payroll record with validation.

        Validates:
        - Person exists
        - No duplicate payroll for the same person/period

        Args:
            payroll_data: Payroll creation data

        Returns:
            Created Payroll instance

        Raises:
            HTTPException: If validation fails
        """
        # Validate person exists
        person_exists = await self.person_repo.exists(payroll_data.person_id)
        if not person_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {payroll_data.person_id} not found",
            )

        # Check for duplicate payroll in the same period
        existing_payroll = await self.payroll_repo.exists_for_person_period(
            company_id=payroll_data.company_id,
            person_id=payroll_data.person_id,
            period_year=payroll_data.period_year,
            period_month=payroll_data.period_month,
        )

        if existing_payroll:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Payroll already exists for person {payroll_data.person_id} in period {payroll_data.period_month}/{payroll_data.period_year}",
            )

        # Create payroll
        new_payroll = await self.payroll_repo.create(**payroll_data.model_dump())
        await self.db.commit()
        await self.db.refresh(new_payroll)

        return new_payroll

    async def list_payroll(
        self,
        company_id: UUID,
        person_id: Optional[UUID] = None,
        period_month: Optional[int] = None,
        period_year: Optional[int] = None,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[list[Payroll], int]:
        """
        List payroll records with filtering and pagination.

        Args:
            company_id: Company ID to filter by
            person_id: Optional person filter
            period_month: Optional month filter (1-12)
            period_year: Optional year filter
            status: Optional status filter (draft, approved, paid, closed)
            payment_status: Optional payment status filter (pending, paid, failed)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (payroll_records, total_count)
        """
        offset = (page - 1) * page_size

        # Get payroll records
        payroll_records = await self.payroll_repo.find_by_company(
            company_id=company_id,
            person_id=person_id,
            period_month=period_month,
            period_year=period_year,
            status=status,
            payment_status=payment_status,
            skip=offset,
            limit=page_size,
        )

        # Get total count
        total = await self.payroll_repo.count(
            filters={
                'company_id': company_id,
                'person_id': person_id,
                'period_month': period_month,
                'period_year': period_year,
                'status': status,
                'payment_status': payment_status,
            }
        )

        return payroll_records, total

    async def get_payroll_summary(
        self,
        company_id: UUID,
        period_month: int,
        period_year: int,
    ) -> dict:
        """
        Get aggregated payroll summary for a period.

        Args:
            company_id: Company ID
            period_month: Month (1-12)
            period_year: Year

        Returns:
            Dictionary with summary statistics
        """
        return await self.payroll_repo.get_period_summary(
            company_id=company_id,
            period_year=period_year,
            period_month=period_month,
        )

    async def get_payroll_by_id(self, payroll_id: UUID) -> Payroll:
        """
        Get a single payroll record with person information.

        Args:
            payroll_id: Payroll UUID

        Returns:
            Payroll instance with person loaded

        Raises:
            HTTPException: If payroll not found
        """
        # Get payroll with person relationship
        query = select(Payroll).options(selectinload(Payroll.person)).where(
            Payroll.id == payroll_id
        )
        result = await self.db.execute(query)
        payroll = result.scalar_one_or_none()

        if not payroll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payroll with ID {payroll_id} not found",
            )

        return payroll

    async def update_payroll(
        self,
        payroll_id: UUID,
        payroll_data: PayrollUpdate,
    ) -> Payroll:
        """
        Update a payroll record.

        Args:
            payroll_id: Payroll UUID
            payroll_data: Fields to update

        Returns:
            Updated Payroll instance

        Raises:
            HTTPException: If payroll not found
        """
        # Get existing payroll
        payroll = await self.payroll_repo.get(payroll_id)
        if not payroll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payroll with ID {payroll_id} not found",
            )

        # Update fields
        update_data = payroll_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payroll, field, value)

        await self.db.commit()
        await self.db.refresh(payroll)

        return payroll

    async def delete_payroll(self, payroll_id: UUID) -> None:
        """
        Delete a payroll record.

        Args:
            payroll_id: Payroll UUID

        Raises:
            HTTPException: If payroll not found
        """
        deleted = await self.payroll_repo.delete(payroll_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payroll with ID {payroll_id} not found",
            )

        await self.db.commit()

    async def approve_payroll(self, payroll_id: UUID) -> Payroll:
        """
        Approve a payroll record.

        Changes status to 'approved' if currently in 'draft'.

        Args:
            payroll_id: Payroll UUID

        Returns:
            Updated Payroll instance

        Raises:
            HTTPException: If payroll not found or in invalid status
        """
        payroll = await self.payroll_repo.get(payroll_id)
        if not payroll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payroll with ID {payroll_id} not found",
            )

        if payroll.status not in ['draft']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payroll must be in draft status to be approved. Current status: {payroll.status}",
            )

        payroll.status = 'approved'
        await self.db.commit()
        await self.db.refresh(payroll)

        return payroll

    async def mark_payroll_paid(self, payroll_id: UUID) -> Payroll:
        """
        Mark a payroll record as paid.

        Changes payment_status to 'paid' and status to 'paid'.

        Args:
            payroll_id: Payroll UUID

        Returns:
            Updated Payroll instance

        Raises:
            HTTPException: If payroll not found or in invalid status
        """
        payroll = await self.payroll_repo.get(payroll_id)
        if not payroll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payroll with ID {payroll_id} not found",
            )

        if payroll.status not in ['approved', 'draft']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payroll must be in approved or draft status to be marked as paid. Current status: {payroll.status}",
            )

        payroll.payment_status = 'paid'
        payroll.status = 'paid'
        await self.db.commit()
        await self.db.refresh(payroll)

        return payroll

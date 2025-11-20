"""Repository for expense CRUD operations."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Expense, ExpenseCategory, ExpenseStatus


class ExpenseRepository:
    """Repository for managing expense records."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def create(
        self,
        company_id: UUID,
        created_by_user_id: UUID,
        expense_category: str,
        expense_date: date,
        description: str,
        total_amount: Decimal,
        has_tax: bool = True,
        expense_subcategory: Optional[str] = None,
        vendor_name: Optional[str] = None,
        vendor_rut: Optional[str] = None,
        receipt_number: Optional[str] = None,
        is_business_expense: bool = True,
        is_reimbursable: bool = False,
        contact_id: Optional[UUID] = None,
        project_code: Optional[str] = None,
        receipt_file_url: Optional[str] = None,
        receipt_file_name: Optional[str] = None,
        receipt_file_size: Optional[int] = None,
        receipt_mime_type: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[list] = None,
        metadata: Optional[dict] = None,
    ) -> Expense:
        """Create a new expense.

        Args:
            company_id: Company ID
            created_by_user_id: User ID who creates the expense
            expense_category: Category (must be valid ExpenseCategory)
            expense_date: Date of the expense
            description: Expense description
            total_amount: Total amount (net_amount and tax_amount auto-calculated)
            has_tax: Whether the amount includes IVA (19%)
            expense_subcategory: Optional subcategory
            vendor_name: Vendor/supplier name
            vendor_rut: Vendor RUT
            receipt_number: Receipt/invoice number
            is_business_expense: Whether it's a business expense
            is_reimbursable: Whether it should be reimbursed
            contact_id: Associated contact (vendor)
            project_code: Associated project code
            receipt_file_url: URL to receipt file
            receipt_file_name: Receipt filename
            receipt_file_size: Receipt file size in bytes
            receipt_mime_type: Receipt MIME type
            notes: Additional notes
            tags: List of tags (JSONB)
            metadata: Additional metadata (JSONB)

        Returns:
            Created Expense instance

        Note:
            net_amount and tax_amount are auto-calculated by DB trigger
        """
        expense = Expense(
            company_id=company_id,
            created_by_user_id=created_by_user_id,
            expense_category=expense_category,
            expense_subcategory=expense_subcategory,
            expense_date=expense_date,
            description=description,
            vendor_name=vendor_name,
            vendor_rut=vendor_rut,
            receipt_number=receipt_number,
            total_amount=total_amount,
            has_tax=has_tax,
            is_business_expense=is_business_expense,
            is_reimbursable=is_reimbursable,
            contact_id=contact_id,
            project_code=project_code,
            receipt_file_url=receipt_file_url,
            receipt_file_name=receipt_file_name,
            receipt_file_size=receipt_file_size,
            receipt_mime_type=receipt_mime_type,
            notes=notes,
            tags=tags or [],
            metadata=metadata or {},
            status=ExpenseStatus.DRAFT.value,
        )

        self.db.add(expense)
        await self.db.commit()
        await self.db.refresh(expense)

        return expense

    async def get(self, expense_id: UUID) -> Optional[Expense]:
        """Get expense by ID.

        Args:
            expense_id: Expense UUID

        Returns:
            Expense instance or None if not found
        """
        result = await self.db.execute(
            select(Expense).where(Expense.id == expense_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        company_id: UUID,
        status: Optional[str] = None,
        category: Optional[str] = None,
        created_by_user_id: Optional[UUID] = None,
        is_reimbursable: Optional[bool] = None,
        reimbursed: Optional[bool] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Expense], int]:
        """List expenses with filters.

        Args:
            company_id: Company ID
            status: Filter by status (draft, pending_approval, approved, etc.)
            category: Filter by expense category
            created_by_user_id: Filter by creator user ID
            is_reimbursable: Filter by reimbursable flag
            reimbursed: Filter by reimbursed flag
            date_from: Filter expenses from this date (inclusive)
            date_to: Filter expenses to this date (inclusive)
            search_query: Search in description, vendor_name, notes
            limit: Max number of results
            offset: Pagination offset

        Returns:
            Tuple of (list of expenses, total count)
        """
        # Build base query
        query = select(Expense).where(Expense.company_id == company_id)

        # Apply filters
        if status:
            query = query.where(Expense.status == status)

        if category:
            query = query.where(Expense.expense_category == category)

        if created_by_user_id:
            query = query.where(Expense.created_by_user_id == created_by_user_id)

        if is_reimbursable is not None:
            query = query.where(Expense.is_reimbursable == is_reimbursable)

        if reimbursed is not None:
            query = query.where(Expense.reimbursed == reimbursed)

        if date_from:
            query = query.where(Expense.expense_date >= date_from)

        if date_to:
            query = query.where(Expense.expense_date <= date_to)

        if search_query:
            search_filter = or_(
                Expense.description.ilike(f"%{search_query}%"),
                Expense.vendor_name.ilike(f"%{search_query}%"),
                Expense.notes.ilike(f"%{search_query}%"),
            )
            query = query.where(search_filter)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply ordering and pagination
        query = query.order_by(Expense.expense_date.desc(), Expense.created_at.desc())
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.db.execute(query)
        expenses = list(result.scalars().all())

        return expenses, total

    async def update(
        self,
        expense_id: UUID,
        **fields,
    ) -> Optional[Expense]:
        """Update expense fields.

        Args:
            expense_id: Expense UUID
            **fields: Fields to update

        Returns:
            Updated Expense instance or None if not found

        Note:
            Only allows updating draft or requires_info expenses
        """
        expense = await self.get(expense_id)
        if not expense:
            return None

        # Only allow updates for draft and requires_info statuses
        if expense.status not in [
            ExpenseStatus.DRAFT.value,
            ExpenseStatus.REQUIRES_INFO.value,
        ]:
            raise ValueError(
                f"Cannot update expense with status '{expense.status}'. "
                "Only draft and requires_info expenses can be updated."
            )

        # Update fields
        for key, value in fields.items():
            if hasattr(expense, key) and value is not None:
                setattr(expense, key, value)

        await self.db.commit()
        await self.db.refresh(expense)

        return expense

    async def delete(self, expense_id: UUID) -> bool:
        """Delete expense.

        Args:
            expense_id: Expense UUID

        Returns:
            True if deleted, False if not found

        Note:
            Only allows deleting draft expenses
        """
        expense = await self.get(expense_id)
        if not expense:
            return False

        # Only allow deleting draft expenses
        if expense.status != ExpenseStatus.DRAFT.value:
            raise ValueError(
                f"Cannot delete expense with status '{expense.status}'. "
                "Only draft expenses can be deleted."
            )

        await self.db.execute(delete(Expense).where(Expense.id == expense_id))
        await self.db.commit()

        return True

    async def submit_for_approval(
        self,
        expense_id: UUID,
    ) -> Optional[Expense]:
        """Submit expense for approval.

        Args:
            expense_id: Expense UUID

        Returns:
            Updated Expense instance or None if not found

        Note:
            submitted_at is auto-set by DB trigger
        """
        expense = await self.get(expense_id)
        if not expense:
            return None

        if expense.status != ExpenseStatus.DRAFT.value:
            raise ValueError(
                f"Cannot submit expense with status '{expense.status}'. "
                "Only draft expenses can be submitted."
            )

        expense.status = ExpenseStatus.PENDING_APPROVAL.value
        # submitted_at is set automatically by trigger

        await self.db.commit()
        await self.db.refresh(expense)

        return expense

    async def approve(
        self,
        expense_id: UUID,
        approved_by_user_id: UUID,
    ) -> Optional[Expense]:
        """Approve expense.

        Args:
            expense_id: Expense UUID
            approved_by_user_id: User ID who approves

        Returns:
            Updated Expense instance or None if not found

        Note:
            approved_at is auto-set by DB trigger
        """
        expense = await self.get(expense_id)
        if not expense:
            return None

        if expense.status != ExpenseStatus.PENDING_APPROVAL.value:
            raise ValueError(
                f"Cannot approve expense with status '{expense.status}'. "
                "Only pending_approval expenses can be approved."
            )

        expense.status = ExpenseStatus.APPROVED.value
        expense.approved_by_user_id = approved_by_user_id
        # approved_at is set automatically by trigger

        await self.db.commit()
        await self.db.refresh(expense)

        return expense

    async def reject(
        self,
        expense_id: UUID,
        rejection_reason: str,
    ) -> Optional[Expense]:
        """Reject expense.

        Args:
            expense_id: Expense UUID
            rejection_reason: Reason for rejection

        Returns:
            Updated Expense instance or None if not found
        """
        expense = await self.get(expense_id)
        if not expense:
            return None

        if expense.status != ExpenseStatus.PENDING_APPROVAL.value:
            raise ValueError(
                f"Cannot reject expense with status '{expense.status}'. "
                "Only pending_approval expenses can be rejected."
            )

        expense.status = ExpenseStatus.REJECTED.value
        expense.rejection_reason = rejection_reason

        await self.db.commit()
        await self.db.refresh(expense)

        return expense

    async def request_info(
        self,
        expense_id: UUID,
        rejection_reason: str,
    ) -> Optional[Expense]:
        """Request more information for expense.

        Args:
            expense_id: Expense UUID
            rejection_reason: Information needed

        Returns:
            Updated Expense instance or None if not found
        """
        expense = await self.get(expense_id)
        if not expense:
            return None

        if expense.status != ExpenseStatus.PENDING_APPROVAL.value:
            raise ValueError(
                f"Cannot request info for expense with status '{expense.status}'. "
                "Only pending_approval expenses can have info requested."
            )

        expense.status = ExpenseStatus.REQUIRES_INFO.value
        expense.rejection_reason = rejection_reason

        await self.db.commit()
        await self.db.refresh(expense)

        return expense

    async def mark_reimbursed(
        self,
        expense_id: UUID,
        reimbursement_date: Optional[date] = None,
    ) -> Optional[Expense]:
        """Mark expense as reimbursed.

        Args:
            expense_id: Expense UUID
            reimbursement_date: Date of reimbursement (defaults to today)

        Returns:
            Updated Expense instance or None if not found
        """
        expense = await self.get(expense_id)
        if not expense:
            return None

        if not expense.is_reimbursable:
            raise ValueError("Cannot mark non-reimbursable expense as reimbursed.")

        if expense.status != ExpenseStatus.APPROVED.value:
            raise ValueError(
                "Cannot mark expense as reimbursed. "
                "Only approved expenses can be reimbursed."
            )

        expense.reimbursed = True
        expense.reimbursement_date = reimbursement_date or date.today()

        await self.db.commit()
        await self.db.refresh(expense)

        return expense

    async def get_summary(
        self,
        company_id: UUID,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """Get expense summary statistics.

        Args:
            company_id: Company ID
            date_from: Start date for filtering
            date_to: End date for filtering
            category: Filter by category
            status: Filter by status

        Returns:
            Dictionary with summary statistics
        """
        # Build base query
        query = select(
            func.count(Expense.id).label("total_count"),
            func.coalesce(func.sum(Expense.total_amount), 0).label("total_amount"),
            func.coalesce(func.sum(Expense.net_amount), 0).label("total_net"),
            func.coalesce(func.sum(Expense.tax_amount), 0).label("total_tax"),
        ).where(Expense.company_id == company_id)

        # Apply filters
        if date_from:
            query = query.where(Expense.expense_date >= date_from)

        if date_to:
            query = query.where(Expense.expense_date <= date_to)

        if category:
            query = query.where(Expense.expense_category == category)

        if status:
            query = query.where(Expense.status == status)

        # Execute query
        result = await self.db.execute(query)
        row = result.one()

        return {
            "total_count": row.total_count,
            "total_amount": float(row.total_amount),
            "total_net": float(row.total_net),
            "total_tax": float(row.total_tax),
        }

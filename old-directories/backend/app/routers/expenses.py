"""Expense management router."""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from ..dependencies import get_current_user_id, require_auth
from ..repositories.expenses import ExpenseRepository
from ..schemas.expenses import ExpenseListResponse
from ..utils.company_resolver import get_user_primary_company_id

router = APIRouter(
    prefix="/api/expenses",
    tags=["expenses"],
    dependencies=[Depends(require_auth)],
)


async def get_expense_repo(db: AsyncSession = Depends(get_db)) -> ExpenseRepository:
    """Dependency to get expense repository."""
    return ExpenseRepository(db)


@router.get("", response_model=ExpenseListResponse)
async def list_expenses(
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    is_reimbursable: Optional[bool] = Query(None),
    reimbursed: Optional[bool] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    repo: ExpenseRepository = Depends(get_expense_repo),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List expenses for the user's company.

    **Filters:**
    - `status`: draft, pending_approval, approved, rejected, requires_info
    - `category`: transport, parking, meals, etc.
    - `is_reimbursable`: true/false
    - `reimbursed`: true/false
    - `date_from`: YYYY-MM-DD (inclusive)
    - `date_to`: YYYY-MM-DD (inclusive)
    - `search`: Search in description, vendor name, notes

    **Pagination:**
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 50, max: 100)

    **Returns:**
    - List of expenses sorted by date descending
    - Total count for pagination
    """
    # Get user's company
    company_id = await get_user_primary_company_id(str(current_user_id), db)
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active company found for user",
        )

    # Parse dates
    date_from_obj = date.fromisoformat(date_from) if date_from else None
    date_to_obj = date.fromisoformat(date_to) if date_to else None

    # Calculate offset
    offset = (page - 1) * page_size

    # Get expenses
    expenses, total = await repo.list(
        company_id=company_id,
        status=status_filter,
        category=category,
        is_reimbursable=is_reimbursable,
        reimbursed=reimbursed,
        date_from=date_from_obj,
        date_to=date_to_obj,
        search_query=search,
        limit=page_size,
        offset=offset,
    )

    return ExpenseListResponse(
        data=expenses,
        total=total,
        page=page,
        page_size=page_size,
    )

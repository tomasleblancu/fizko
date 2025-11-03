"""Tax Summary router - Get company tax summaries."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id, require_auth
from ...repositories.tax import TaxSummaryRepository
from ...schemas.tax import TaxSummary
from ...utils.company_resolver import get_user_primary_company_id

router = APIRouter(
    prefix="/api/tax-summary",
    tags=["tax-summary"],
    dependencies=[Depends(require_auth)]
)


@router.get("", response_model=TaxSummary)
async def get_tax_summary_for_user(
    period: Optional[str] = Query(None, description="Period in format YYYY-MM"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tax summary for the authenticated user's primary company.

    Automatically resolves the company_id from the user's active session.
    Calculates summary from sales and purchase documents.
    If no period is specified, returns current month summary.
    """
    # Resolve company_id from user's active session
    company_id = await get_user_primary_company_id(current_user_id, db)

    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active company found for user"
        )

    # Use repository for calculation
    repo = TaxSummaryRepository(db)
    try:
        return await repo.get_tax_summary(company_id, period)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{company_id}", response_model=TaxSummary)
async def get_tax_summary(
    company_id: UUID,
    period: Optional[str] = Query(None, description="Period in format YYYY-MM"),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tax summary for a specific company.

    (Legacy endpoint for backward compatibility)
    Calculates summary from sales and purchase documents.
    If no period is specified, returns current month summary.
    """
    # Use repository for calculation
    repo = TaxSummaryRepository(db)
    try:
        return await repo.get_tax_summary(company_id, period)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "Invalid period" in str(e) else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

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
    dependencies=[
        Depends(require_auth)
    ]
)


@router.get("", response_model=TaxSummary)
async def get_tax_summary_for_user(
    period: Optional[str] = Query(None, description="Period in format YYYY-MM"),
    company_id: Optional[UUID] = Query(None, description="Company ID to get summary for"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tax summary for the authenticated user's company.

    If company_id is provided, uses that. Otherwise, resolves from user's active session.
    Calculates summary from sales and purchase documents.
    If no period is specified, returns current month summary.
    """
    # Use provided company_id or resolve from user's active session
    resolved_company_id = company_id or await get_user_primary_company_id(current_user_id, db)

    if not resolved_company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active company found for user"
        )

    # Use repository for calculation
    repo = TaxSummaryRepository(db)
    try:
        return await repo.get_tax_summary(resolved_company_id, period)
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

"""Form29 router - Manage Form 29 (Monthly IVA declarations)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import Session
from ...dependencies import get_current_user_id, require_auth, Form29RepositoryDep
from ...schemas.tax import Form29Create, Form29Submit, Form29Update

router = APIRouter(
    prefix="/api/form29",
    tags=["form29"],
    dependencies=[Depends(require_auth)]
)


# =============================================================================
# Helper Functions
# =============================================================================

async def verify_company_access(
    company_id: UUID,
    user_id: str,
    db: AsyncSession
) -> None:
    """Verify that the user has access to the company via an active session."""
    stmt = select(Session).where(
        Session.user_id == UUID(user_id),
        Session.company_id == company_id,
        Session.is_active == True
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company"
        )


# =============================================================================
# Endpoints
# =============================================================================

@router.get("")
async def list_form29(
    repo: Form29RepositoryDep,
    company_id: str = Query(..., description="Company ID (required)"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    period_year: Optional[int] = None,
    period_month: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """
    List Form29 records for a company with optional filtering.

    Query params:
    - company_id: Company ID (required)
    - period_year: Filter by year
    - period_month: Filter by month (1-12)
    - status: Filter by status (draft, submitted)
    - skip: Pagination offset
    - limit: Number of records to return
    """
    company_uuid = UUID(company_id)

    # Verify access
    await verify_company_access(company_uuid, user_id, db)

    # Validate month if provided
    if period_month and (period_month < 1 or period_month > 12):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_month must be between 1 and 12"
        )

    # Use repository (injected via Depends)
    forms = await repo.find_by_company(
        company_id=company_uuid,
        period_year=period_year,
        period_month=period_month,
        status=status_filter,
        skip=skip,
        limit=limit
    )

    # Get total count
    total = await repo.count(filters={'company_id': company_uuid})

    return {
        "data": [
            {
                "id": str(form.id),
                "company_id": str(form.company_id),
                "period_year": form.period_year,
                "period_month": form.period_month,
                "total_sales": float(form.total_sales),
                "taxable_sales": float(form.taxable_sales),
                "exempt_sales": float(form.exempt_sales),
                "sales_tax": float(form.sales_tax),
                "total_purchases": float(form.total_purchases),
                "taxable_purchases": float(form.taxable_purchases),
                "purchases_tax": float(form.purchases_tax),
                "iva_to_pay": float(form.iva_to_pay),
                "iva_credit": float(form.iva_credit),
                "net_iva": float(form.net_iva),
                "status": form.status,
                "submission_date": form.submission_date.isoformat() if form.submission_date else None,
                "folio": form.folio,
                "created_at": form.created_at.isoformat(),
                "updated_at": form.updated_at.isoformat(),
            }
            for form in forms
        ],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total,
        }
    }


@router.get("/{form_id}")
async def get_form29(
    form_id: UUID,
    repo: Form29RepositoryDep,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get a single Form29 by ID.

    User must have access to the company that owns this form.
    """
    # Get form using repository (injected via Depends)
    form = await repo.get(form_id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form29 not found"
        )

    # Verify access
    await verify_company_access(form.company_id, user_id, db)

    return {
        "data": {
            "id": str(form.id),
            "company_id": str(form.company_id),
            "period_year": form.period_year,
            "period_month": form.period_month,
            "total_sales": float(form.total_sales),
            "taxable_sales": float(form.taxable_sales),
            "exempt_sales": float(form.exempt_sales),
            "sales_tax": float(form.sales_tax),
            "total_purchases": float(form.total_purchases),
            "taxable_purchases": float(form.taxable_purchases),
            "purchases_tax": float(form.purchases_tax),
            "iva_to_pay": float(form.iva_to_pay),
            "iva_credit": float(form.iva_credit),
            "net_iva": float(form.net_iva),
            "status": form.status,
            "submission_date": form.submission_date.isoformat() if form.submission_date else None,
            "folio": form.folio,
            "extra_data": form.extra_data,
            "created_at": form.created_at.isoformat(),
            "updated_at": form.updated_at.isoformat(),
        }
    }


@router.post("")
async def create_form29(
    data: Form29Create,
    repo: Form29RepositoryDep,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Create a new Form29.

    User must have access to the specified company.
    Only one Form29 per company per period (year + month) is allowed.
    """
    company_id = UUID(data.company_id)

    # Verify access
    await verify_company_access(company_id, user_id, db)

    # Validate month
    if data.period_month < 1 or data.period_month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_month must be between 1 and 12"
        )

    # Check if Form29 already exists for this period (using injected repo)
    exists = await repo.exists_for_period(company_id, data.period_year, data.period_month)

    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Form29 already exists for period {data.period_year}-{data.period_month:02d}"
        )

    # Create form using repository
    form = await repo.create(
        company_id=company_id,
        period_year=data.period_year,
        period_month=data.period_month,
        total_sales=data.total_sales,
        taxable_sales=data.taxable_sales,
        exempt_sales=data.exempt_sales,
        sales_tax=data.sales_tax,
        total_purchases=data.total_purchases,
        taxable_purchases=data.taxable_purchases,
        purchases_tax=data.purchases_tax,
        iva_to_pay=data.iva_to_pay,
        iva_credit=data.iva_credit,
        net_iva=data.net_iva,
        status=data.status,
        extra_data=data.extra_data or {},
    )
    await db.commit()
    await db.refresh(form)

    return {
        "data": {
            "id": str(form.id),
            "company_id": str(form.company_id),
            "period_year": form.period_year,
            "period_month": form.period_month,
            "net_iva": float(form.net_iva),
            "status": form.status,
        },
        "message": "Form29 created successfully"
    }


@router.put("/{form_id}")
async def update_form29(
    form_id: UUID,
    data: Form29Update,
    repo: Form29RepositoryDep,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update a Form29.

    User must have access to the company that owns this form.
    Note: Cannot update a Form29 that has been submitted.
    """
    # Get form using repository (injected via Depends)
    form = await repo.get(form_id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form29 not found"
        )

    # Verify access
    await verify_company_access(form.company_id, user_id, db)

    # Check if form is submitted
    if form.status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a submitted Form29"
        )

    # Update only provided fields using repository
    update_data = data.model_dump(exclude_unset=True)
    form = await repo.update(form_id, **update_data)
    await db.commit()
    await db.refresh(form)

    return {
        "data": {
            "id": str(form.id),
            "company_id": str(form.company_id),
            "period_year": form.period_year,
            "period_month": form.period_month,
            "net_iva": float(form.net_iva),
            "status": form.status,
            "updated_at": form.updated_at.isoformat(),
        },
        "message": "Form29 updated successfully"
    }


@router.delete("/{form_id}")
async def delete_form29(
    form_id: UUID,
    repo: Form29RepositoryDep,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Delete a Form29.

    User must have access to the company that owns this form.
    Note: Cannot delete a Form29 that has been submitted.
    This is a hard delete. For soft delete, update the status instead.
    """
    # Get form using repository (injected via Depends)
    form = await repo.get(form_id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form29 not found"
        )

    # Verify access
    await verify_company_access(form.company_id, user_id, db)

    # Check if form is submitted
    if form.status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a submitted Form29"
        )

    # Delete form using repository
    await repo.delete(form_id)
    await db.commit()

    return {
        "data": {
            "id": str(form_id),
        },
        "message": "Form29 deleted successfully"
    }


@router.post("/{form_id}/submit")
async def submit_form29(
    form_id: UUID,
    data: Form29Submit,
    repo: Form29RepositoryDep,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Submit a Form29 to SII.

    This changes the status to 'submitted' and records the submission date.
    User must have access to the company that owns this form.

    Note: This is a placeholder endpoint. In production, this would integrate
    with the actual SII submission service.
    """
    # Get form using repository (injected via Depends)
    form = await repo.get(form_id)

    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form29 not found"
        )

    # Verify access
    await verify_company_access(form.company_id, user_id, db)

    # Check if already submitted
    if form.status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Form29 has already been submitted"
        )

    # TODO: Implement actual SII submission logic here
    # This would involve:
    # 1. Validating the form data
    # 2. Connecting to SII API/service
    # 3. Submitting the form
    # 4. Getting back a folio/confirmation number

    # Update form status using repository
    update_data = {
        "status": "submitted",
        "submission_date": datetime.utcnow()
    }
    if data.folio:
        update_data["folio"] = data.folio

    form = await repo.update(form_id, **update_data)
    await db.commit()
    await db.refresh(form)

    return {
        "data": {
            "id": str(form.id),
            "company_id": str(form.company_id),
            "period_year": form.period_year,
            "period_month": form.period_month,
            "status": form.status,
            "submission_date": form.submission_date.isoformat(),
            "folio": form.folio,
        },
        "message": "Form29 submitted successfully"
    }

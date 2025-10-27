"""Form29 router - Manage Form 29 (Monthly IVA declarations)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import Form29, Session
from ...dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/form29",
    tags=["form29"],
    dependencies=[Depends(require_auth)]
)


# =============================================================================
# Request/Response Models
# =============================================================================

class Form29Create(BaseModel):
    """Request model for creating a Form29."""
    company_id: str  # UUID string
    period_year: int
    period_month: int
    total_sales: Decimal = Decimal("0")
    taxable_sales: Decimal = Decimal("0")
    exempt_sales: Decimal = Decimal("0")
    sales_tax: Decimal = Decimal("0")
    total_purchases: Decimal = Decimal("0")
    taxable_purchases: Decimal = Decimal("0")
    purchases_tax: Decimal = Decimal("0")
    iva_to_pay: Decimal = Decimal("0")
    iva_credit: Decimal = Decimal("0")
    net_iva: Decimal = Decimal("0")
    status: str = "draft"
    extra_data: Optional[dict] = None


class Form29Update(BaseModel):
    """Request model for updating a Form29."""
    total_sales: Optional[Decimal] = None
    taxable_sales: Optional[Decimal] = None
    exempt_sales: Optional[Decimal] = None
    sales_tax: Optional[Decimal] = None
    total_purchases: Optional[Decimal] = None
    taxable_purchases: Optional[Decimal] = None
    purchases_tax: Optional[Decimal] = None
    iva_to_pay: Optional[Decimal] = None
    iva_credit: Optional[Decimal] = None
    net_iva: Optional[Decimal] = None
    status: Optional[str] = None
    extra_data: Optional[dict] = None


class Form29Submit(BaseModel):
    """Request model for submitting a Form29 to SII."""
    folio: Optional[str] = None


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

    # Build query
    stmt = select(Form29).where(Form29.company_id == company_uuid)

    # Apply filters
    if period_year:
        stmt = stmt.where(Form29.period_year == period_year)
    if period_month:
        if period_month < 1 or period_month > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="period_month must be between 1 and 12"
            )
        stmt = stmt.where(Form29.period_month == period_month)
    if status_filter:
        stmt = stmt.where(Form29.status == status_filter)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination and ordering
    stmt = stmt.offset(skip).limit(limit).order_by(
        Form29.period_year.desc(),
        Form29.period_month.desc()
    )

    result = await db.execute(stmt)
    forms = result.scalars().all()

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
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get a single Form29 by ID.

    User must have access to the company that owns this form.
    """
    # Get form
    stmt = select(Form29).where(Form29.id == form_id)
    result = await db.execute(stmt)
    form = result.scalar_one_or_none()

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

    # Check if Form29 already exists for this period
    stmt = select(Form29).where(
        Form29.company_id == company_id,
        Form29.period_year == data.period_year,
        Form29.period_month == data.period_month
    )
    result = await db.execute(stmt)
    existing_form = result.scalar_one_or_none()

    if existing_form:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Form29 already exists for period {data.period_year}-{data.period_month:02d}"
        )

    # Create form
    form = Form29(
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

    db.add(form)
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
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update a Form29.

    User must have access to the company that owns this form.
    Note: Cannot update a Form29 that has been submitted.
    """
    # Get form
    stmt = select(Form29).where(Form29.id == form_id)
    result = await db.execute(stmt)
    form = result.scalar_one_or_none()

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

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(form, field, value)

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
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Delete a Form29.

    User must have access to the company that owns this form.
    Note: Cannot delete a Form29 that has been submitted.
    This is a hard delete. For soft delete, update the status instead.
    """
    # Get form
    stmt = select(Form29).where(Form29.id == form_id)
    result = await db.execute(stmt)
    form = result.scalar_one_or_none()

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

    # Delete form
    await db.delete(form)
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
    # Get form
    stmt = select(Form29).where(Form29.id == form_id)
    result = await db.execute(stmt)
    form = result.scalar_one_or_none()

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

    # Update form status
    form.status = "submitted"
    form.submission_date = datetime.utcnow()
    if data.folio:
        form.folio = data.folio

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

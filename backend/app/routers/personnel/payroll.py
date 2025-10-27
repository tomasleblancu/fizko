"""API endpoints for managing payroll (liquidaciones de sueldo)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...config.database import get_db
from ...db.models import Payroll, Person
from ...schemas.personnel import (
    Payroll as PayrollSchema,
    PayrollCreate,
    PayrollListResponse,
    PayrollSummary,
    PayrollUpdate,
    PayrollWithPerson,
)

router = APIRouter()


@router.post("/", response_model=PayrollSchema, status_code=status.HTTP_201_CREATED)
async def create_payroll(
    payroll_data: PayrollCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new payroll record.

    Creates a liquidación de sueldo for an employee for a specific period.
    Totals are automatically calculated by the database trigger.
    """
    # Check if person exists
    person_query = select(Person).where(Person.id == payroll_data.person_id)
    person_result = await db.execute(person_query)
    person = person_result.scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {payroll_data.person_id} not found",
        )

    # Check if payroll already exists for this period
    existing_query = select(Payroll).where(
        Payroll.person_id == payroll_data.person_id,
        Payroll.period_month == payroll_data.period_month,
        Payroll.period_year == payroll_data.period_year,
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payroll already exists for person {payroll_data.person_id} in period {payroll_data.period_month}/{payroll_data.period_year}",
        )

    # Create new payroll
    new_payroll = Payroll(**payroll_data.model_dump())

    db.add(new_payroll)
    await db.commit()
    await db.refresh(new_payroll)

    return new_payroll


@router.get("/", response_model=PayrollListResponse)
async def list_payroll(
    company_id: UUID = Query(..., description="Company ID to filter by"),
    person_id: Optional[UUID] = Query(None, description="Filter by person ID"),
    period_month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month"),
    period_year: Optional[int] = Query(None, ge=2020, description="Filter by year"),
    status: Optional[str] = Query(None, description="Filter by status (draft, approved, paid, closed)"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status (pending, paid, failed)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all payroll records for a company.

    Returns a paginated list of liquidaciones de sueldo with optional filtering.
    """
    # Build base query
    query = select(Payroll).where(Payroll.company_id == company_id)

    # Apply filters
    if person_id:
        query = query.where(Payroll.person_id == person_id)

    if period_month:
        query = query.where(Payroll.period_month == period_month)

    if period_year:
        query = query.where(Payroll.period_year == period_year)

    if status:
        query = query.where(Payroll.status == status)

    if payment_status:
        query = query.where(Payroll.payment_status == payment_status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(
        Payroll.period_year.desc(),
        Payroll.period_month.desc(),
    )

    # Execute query
    result = await db.execute(query)
    payroll_records = result.scalars().all()

    return PayrollListResponse(
        data=payroll_records,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/summary", response_model=PayrollSummary)
async def get_payroll_summary(
    company_id: UUID = Query(..., description="Company ID"),
    period_month: int = Query(..., ge=1, le=12, description="Month"),
    period_year: int = Query(..., ge=2020, description="Year"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get payroll summary for a specific period.

    Returns aggregated statistics for all payroll records in a given month/year.
    """
    # Build query for the period
    query = select(
        func.count(Payroll.id).label('total_employees'),
        func.sum(Payroll.total_income).label('total_gross_salary'),
        func.sum(Payroll.total_deductions).label('total_deductions'),
        func.sum(Payroll.net_salary).label('total_net_salary'),
    ).where(
        Payroll.company_id == company_id,
        Payroll.period_month == period_month,
        Payroll.period_year == period_year,
    )

    result = await db.execute(query)
    summary = result.first()

    return PayrollSummary(
        period_month=period_month,
        period_year=period_year,
        total_employees=summary.total_employees or 0,
        total_gross_salary=summary.total_gross_salary or 0,
        total_deductions=summary.total_deductions or 0,
        total_net_salary=summary.total_net_salary or 0,
    )


@router.get("/{payroll_id}", response_model=PayrollWithPerson)
async def get_payroll(
    payroll_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single payroll record by ID.

    Returns detailed information about a liquidación de sueldo including person information.
    """
    query = select(Payroll).options(selectinload(Payroll.person)).where(Payroll.id == payroll_id)
    result = await db.execute(query)
    payroll = result.scalar_one_or_none()

    if not payroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll with ID {payroll_id} not found",
        )

    return payroll


@router.patch("/{payroll_id}", response_model=PayrollSchema)
async def update_payroll(
    payroll_id: UUID,
    payroll_data: PayrollUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a payroll record.

    Updates an existing liquidación de sueldo. Only provided fields will be updated.
    Totals are automatically recalculated by the database trigger.
    """
    # Get existing payroll
    query = select(Payroll).where(Payroll.id == payroll_id)
    result = await db.execute(query)
    payroll = result.scalar_one_or_none()

    if not payroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll with ID {payroll_id} not found",
        )

    # Update fields
    update_data = payroll_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payroll, field, value)

    await db.commit()
    await db.refresh(payroll)

    return payroll


@router.delete("/{payroll_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payroll(
    payroll_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a payroll record.

    Permanently deletes a liquidación de sueldo.
    """
    # Get existing payroll
    query = select(Payroll).where(Payroll.id == payroll_id)
    result = await db.execute(query)
    payroll = result.scalar_one_or_none()

    if not payroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payroll with ID {payroll_id} not found",
        )

    await db.delete(payroll)
    await db.commit()

    return None


@router.post("/{payroll_id}/approve", response_model=PayrollSchema)
async def approve_payroll(
    payroll_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Approve a payroll record.

    Changes the status to 'approved' for a liquidación de sueldo.
    """
    # Get existing payroll
    query = select(Payroll).where(Payroll.id == payroll_id)
    result = await db.execute(query)
    payroll = result.scalar_one_or_none()

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
    await db.commit()
    await db.refresh(payroll)

    return payroll


@router.post("/{payroll_id}/mark-paid", response_model=PayrollSchema)
async def mark_payroll_paid(
    payroll_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a payroll record as paid.

    Changes the payment_status to 'paid' and status to 'paid' for a liquidación de sueldo.
    """
    # Get existing payroll
    query = select(Payroll).where(Payroll.id == payroll_id)
    result = await db.execute(query)
    payroll = result.scalar_one_or_none()

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
    await db.commit()
    await db.refresh(payroll)

    return payroll

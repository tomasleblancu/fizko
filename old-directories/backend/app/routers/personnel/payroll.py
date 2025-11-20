"""API endpoints for managing payroll (liquidaciones de sueldo)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...schemas.personnel import (
    Payroll as PayrollSchema,
    PayrollCreate,
    PayrollListResponse,
    PayrollSummary,
    PayrollUpdate,
    PayrollWithPerson,
)
from ...services.personnel import PayrollService

router = APIRouter()


def get_payroll_service(db: AsyncSession = Depends(get_db)) -> PayrollService:
    """
    Dependency to get PayrollService instance.

    Args:
        db: Database session from dependency injection

    Returns:
        PayrollService instance
    """
    return PayrollService(db)


@router.post("/", response_model=PayrollSchema, status_code=status.HTTP_201_CREATED)
async def create_payroll(
    payroll_data: PayrollCreate,
    service: PayrollService = Depends(get_payroll_service),
):
    """
    Create a new payroll record.

    Creates a liquidación de sueldo for an employee for a specific period.
    Totals are automatically calculated by the database trigger.
    """
    return await service.create_payroll(payroll_data)


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
    service: PayrollService = Depends(get_payroll_service),
):
    """
    List all payroll records for a company.

    Returns a paginated list of liquidaciones de sueldo with optional filtering.
    """
    payroll_records, total = await service.list_payroll(
        company_id=company_id,
        person_id=person_id,
        period_month=period_month,
        period_year=period_year,
        status=status,
        payment_status=payment_status,
        page=page,
        page_size=page_size,
    )

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
    service: PayrollService = Depends(get_payroll_service),
):
    """
    Get payroll summary for a specific period.

    Returns aggregated statistics for all payroll records in a given month/year.
    """
    summary = await service.get_payroll_summary(
        company_id=company_id,
        period_month=period_month,
        period_year=period_year,
    )

    return PayrollSummary(
        period_month=summary['period_month'],
        period_year=summary['period_year'],
        total_employees=summary['total_employees'],
        total_gross_salary=summary['total_gross_salary'],
        total_deductions=summary['total_deductions'],
        total_net_salary=summary['total_net_salary'],
    )


@router.get("/{payroll_id}", response_model=PayrollWithPerson)
async def get_payroll(
    payroll_id: UUID,
    service: PayrollService = Depends(get_payroll_service),
):
    """
    Get a single payroll record by ID.

    Returns detailed information about a liquidación de sueldo including person information.
    """
    return await service.get_payroll_by_id(payroll_id)


@router.patch("/{payroll_id}", response_model=PayrollSchema)
async def update_payroll(
    payroll_id: UUID,
    payroll_data: PayrollUpdate,
    service: PayrollService = Depends(get_payroll_service),
):
    """
    Update a payroll record.

    Updates an existing liquidación de sueldo. Only provided fields will be updated.
    Totals are automatically recalculated by the database trigger.
    """
    return await service.update_payroll(payroll_id, payroll_data)


@router.delete("/{payroll_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payroll(
    payroll_id: UUID,
    service: PayrollService = Depends(get_payroll_service),
):
    """
    Delete a payroll record.

    Permanently deletes a liquidación de sueldo.
    """
    await service.delete_payroll(payroll_id)
    return None


@router.post("/{payroll_id}/approve", response_model=PayrollSchema)
async def approve_payroll(
    payroll_id: UUID,
    service: PayrollService = Depends(get_payroll_service),
):
    """
    Approve a payroll record.

    Changes the status to 'approved' for a liquidación de sueldo.
    """
    return await service.approve_payroll(payroll_id)


@router.post("/{payroll_id}/mark-paid", response_model=PayrollSchema)
async def mark_payroll_paid(
    payroll_id: UUID,
    service: PayrollService = Depends(get_payroll_service),
):
    """
    Mark a payroll record as paid.

    Changes the payment_status to 'paid' and status to 'paid' for a liquidación de sueldo.
    """
    return await service.mark_payroll_paid(payroll_id)

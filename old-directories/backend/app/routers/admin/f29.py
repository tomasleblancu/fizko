"""
F29 form management endpoints for admin - REFACTORED VERSION

This version uses repositories instead of direct SQL queries.
"""
import logging
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...dependencies import get_current_user_id
from ...repositories import (
    CompanyRepository,
    ProfileRepository,
    SessionRepository,
    Form29SIIDownloadRepository,
    Form29Repository,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class F29DownloadInfo(BaseModel):
    """F29 download information"""
    id: str
    sii_folio: str
    sii_id_interno: Optional[str]
    period_year: int
    period_month: int
    period_display: str
    contributor_rut: str
    submission_date: Optional[datetime]
    status: str
    amount_cents: int
    pdf_storage_url: Optional[str]
    pdf_download_status: str
    pdf_download_error: Optional[str]
    pdf_downloaded_at: Optional[datetime]
    has_pdf: bool
    can_download_pdf: bool
    extra_data: Optional[dict]
    created_at: datetime
    updated_at: datetime


@router.get("/company/{company_id}/f29", response_model=List[F29DownloadInfo])
async def get_company_f29_list(
    company_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    year: Optional[int] = None,
    status_filter: Optional[str] = None
):
    """
    Get F29 forms for a company

    Returns all Form29SIIDownload records for the specified company.
    Can be filtered by year and status.

    Args:
        company_id: Company UUID
        current_user_id: Authenticated user ID
        db: Database session
        year: Optional year filter
        status_filter: Optional status filter (Vigente, Rectificado, Anulado)

    Returns:
        List of F29DownloadInfo

    Raises:
        404: Company not found
        403: User doesn't have access to this company
    """
    logger.info(f"F29 list requested for company {company_id} by user {current_user_id}")

    # Initialize repositories
    profile_repo = ProfileRepository(db)
    company_repo = CompanyRepository(db)
    session_repo = SessionRepository(db)
    f29_repo = Form29SIIDownloadRepository(db)

    # Check user role and access permissions
    user = await profile_repo.get_by_user_id(current_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    is_admin = user.rol == "admin-kaiken"

    # If not admin, check if user has access to this company
    if not is_admin:
        has_access = await session_repo.user_has_access_to_company(current_user_id, company_id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )

    # Verify company exists
    company = await company_repo.get(company_id)

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company {company_id} not found"
        )

    # Get F29 downloads using repository
    f29_downloads = await f29_repo.find_by_company(
        company_id=company_id,
        year=year,
        status_filter=status_filter
    )

    return [
        F29DownloadInfo(
            id=str(download.id),
            sii_folio=download.sii_folio,
            sii_id_interno=download.sii_id_interno,
            period_year=download.period_year,
            period_month=download.period_month,
            period_display=download.period_display,
            contributor_rut=download.contributor_rut,
            submission_date=download.submission_date,
            status=download.status,
            amount_cents=download.amount_cents,
            pdf_storage_url=download.pdf_storage_url,
            pdf_download_status=download.pdf_download_status,
            pdf_download_error=download.pdf_download_error,
            pdf_downloaded_at=download.pdf_downloaded_at,
            has_pdf=download.has_pdf,
            can_download_pdf=download.can_download_pdf,
            extra_data=download.extra_data,
            created_at=download.created_at,
            updated_at=download.updated_at
        )
        for download in f29_downloads
    ]


class Form29GeneratedInfo(BaseModel):
    """Form29 generated information"""
    id: str
    company_id: str
    company_name: str
    period_year: int
    period_month: int
    revision_number: int
    total_sales: float
    taxable_sales: float
    exempt_sales: float
    sales_tax: float
    total_purchases: float
    taxable_purchases: float
    purchases_tax: float
    iva_to_pay: float
    iva_credit: float
    net_iva: float
    previous_month_credit: float
    status: str
    validation_status: str
    submission_date: Optional[datetime]
    folio: Optional[str]
    payment_status: str
    created_at: datetime
    updated_at: datetime


@router.get("/form29/all", response_model=List[Form29GeneratedInfo])
async def get_all_form29_generated(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    year: Optional[int] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all Form29 generated records across all companies (admin only)

    Returns all Form29 records from the form29 table.
    Can be filtered by year and status.

    Args:
        current_user_id: Authenticated user ID
        db: Database session
        year: Optional year filter
        status_filter: Optional status filter (draft, saved, paid, cancelled)
        skip: Pagination offset
        limit: Number of records to return

    Returns:
        List of Form29GeneratedInfo

    Raises:
        403: User is not admin
    """
    logger.info(f"All Form29 generated list requested by user {current_user_id}")

    # Initialize repositories
    profile_repo = ProfileRepository(db)
    company_repo = CompanyRepository(db)
    f29_repo = Form29Repository(db)

    # Check user role - admin only
    user = await profile_repo.get_by_user_id(current_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    if user.rol != "admin-kaiken":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access all Form29 records"
        )

    # Get all F29 forms using repository
    filters = {}
    if year:
        filters['period_year'] = year
    if status_filter:
        filters['status'] = status_filter

    forms = await f29_repo.find_all(
        filters=filters,
        skip=skip,
        limit=limit
    )

    # Get company names
    result = []
    for form in forms:
        company = await company_repo.get(form.company_id)
        company_name = company.business_name if company else "Unknown"

        result.append(
            Form29GeneratedInfo(
                id=str(form.id),
                company_id=str(form.company_id),
                company_name=company_name,
                period_year=form.period_year,
                period_month=form.period_month,
                revision_number=form.revision_number,
                total_sales=float(form.total_sales),
                taxable_sales=float(form.taxable_sales),
                exempt_sales=float(form.exempt_sales),
                sales_tax=float(form.sales_tax),
                total_purchases=float(form.total_purchases),
                taxable_purchases=float(form.taxable_purchases),
                purchases_tax=float(form.purchases_tax),
                iva_to_pay=float(form.iva_to_pay),
                iva_credit=float(form.iva_credit),
                net_iva=float(form.net_iva),
                previous_month_credit=float(form.previous_month_credit),
                status=form.status,
                validation_status=form.validation_status,
                submission_date=form.submission_date,
                folio=form.folio,
                payment_status=form.payment_status,
                created_at=form.created_at,
                updated_at=form.updated_at
            )
        )

    return result

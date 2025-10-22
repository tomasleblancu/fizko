"""Companies router - Manage company information."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config.database import get_db
from ..db.models import Company, CompanyTaxInfo, Session
from ..dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/companies",
    tags=["companies"],
    dependencies=[Depends(require_auth)]
)


# =============================================================================
# Request/Response Models
# =============================================================================

class CompanyCreate(BaseModel):
    """Request model for creating a company."""
    rut: str
    business_name: str
    trade_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class CompanyUpdate(BaseModel):
    """Request model for updating company basic info."""
    business_name: Optional[str] = None
    trade_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    sii_password: Optional[str] = None  # SII portal password


class CompanyTaxInfoUpdate(BaseModel):
    """Request model for updating company tax info."""
    tax_regime: Optional[str] = None
    sii_activity_code: Optional[str] = None
    sii_activity_name: Optional[str] = None
    legal_representative_rut: Optional[str] = None
    legal_representative_name: Optional[str] = None
    start_of_activities_date: Optional[str] = None  # ISO date string
    accounting_start_month: Optional[int] = None
    extra_data: Optional[dict] = None


# =============================================================================
# Helper Functions
# =============================================================================

async def verify_company_access(
    company_id: UUID,
    user_id: str,
    db: AsyncSession
) -> Company:
    """
    Verify that the user has access to the company via an active session.

    Args:
        company_id: The company ID to check
        user_id: The user ID from JWT token
        db: Database session

    Returns:
        Company object if access is granted

    Raises:
        HTTPException: 403 if access denied, 404 if company not found
    """
    # Check if user has an active session with this company
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

    # Get the company with tax info
    stmt = select(Company).options(
        selectinload(Company.tax_info)
    ).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    return company


# =============================================================================
# Endpoints
# =============================================================================

@router.get("")
async def list_companies(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """
    Get all companies the authenticated user has access to via Sessions.

    Returns list of companies with basic information.
    """
    # Get all active sessions for this user
    stmt = select(Session).options(
        selectinload(Session.company).selectinload(Company.tax_info)
    ).where(
        Session.user_id == UUID(user_id),
        Session.is_active == True
    ).offset(skip).limit(limit)

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # Get total count
    count_stmt = select(Session).where(
        Session.user_id == UUID(user_id),
        Session.is_active == True
    )
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    return {
        "data": [
            {
                "id": str(s.company.id),
                "rut": s.company.rut,
                "business_name": s.company.business_name,
                "trade_name": s.company.trade_name,
                "address": s.company.address,
                "phone": s.company.phone,
                "email": s.company.email,
                "tax_regime": s.company.tax_info.tax_regime if s.company.tax_info else None,
                "sii_activity_code": s.company.tax_info.sii_activity_code if s.company.tax_info else None,
                "created_at": s.company.created_at.isoformat(),
                "session_id": str(s.id),
            }
            for s in sessions
        ],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total,
        }
    }


@router.get("/{company_id}")
async def get_company(
    company_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get detailed information about a specific company including tax info.

    User must have an active session with the company.
    """
    company = await verify_company_access(company_id, user_id, db)

    return {
        "data": {
            "id": str(company.id),
            "rut": company.rut,
            "business_name": company.business_name,
            "trade_name": company.trade_name,
            "address": company.address,
            "phone": company.phone,
            "email": company.email,
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat(),
            "tax_info": {
                "id": str(company.tax_info.id),
                "tax_regime": company.tax_info.tax_regime,
                "sii_activity_code": company.tax_info.sii_activity_code,
                "sii_activity_name": company.tax_info.sii_activity_name,
                "legal_representative_rut": company.tax_info.legal_representative_rut,
                "legal_representative_name": company.tax_info.legal_representative_name,
                "start_of_activities_date": company.tax_info.start_of_activities_date.isoformat() if company.tax_info.start_of_activities_date else None,
                "accounting_start_month": company.tax_info.accounting_start_month,
                "extra_data": company.tax_info.extra_data,
                "created_at": company.tax_info.created_at.isoformat(),
                "updated_at": company.tax_info.updated_at.isoformat(),
            } if company.tax_info else None,
        }
    }


@router.post("")
async def create_company(
    data: CompanyCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Create a new company and automatically create a session for the user.

    This endpoint creates:
    1. A new Company record
    2. A Session linking the user to the company
    """
    # Check if company with this RUT already exists
    stmt = select(Company).where(Company.rut == data.rut)
    result = await db.execute(stmt)
    existing_company = result.scalar_one_or_none()

    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with RUT {data.rut} already exists"
        )

    # Create new company
    company = Company(
        rut=data.rut,
        business_name=data.business_name,
        trade_name=data.trade_name,
        address=data.address,
        phone=data.phone,
        email=data.email,
    )

    db.add(company)
    await db.flush()  # Flush to get the company ID

    # Create session for the user
    session = Session(
        user_id=UUID(user_id),
        company_id=company.id,
        is_active=True,
    )

    db.add(session)
    await db.commit()
    await db.refresh(company)
    await db.refresh(session)

    return {
        "data": {
            "id": str(company.id),
            "rut": company.rut,
            "business_name": company.business_name,
            "session_id": str(session.id),
        },
        "message": "Company created successfully"
    }


@router.put("/{company_id}")
async def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update company basic information.

    User must have an active session with the company.
    """
    company = await verify_company_access(company_id, user_id, db)

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)

    return {
        "data": {
            "id": str(company.id),
            "rut": company.rut,
            "business_name": company.business_name,
            "trade_name": company.trade_name,
            "address": company.address,
            "phone": company.phone,
            "email": company.email,
            "updated_at": company.updated_at.isoformat(),
        },
        "message": "Company updated successfully"
    }


@router.get("/{company_id}/tax-info")
async def get_company_tax_info(
    company_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get company tax information.

    User must have an active session with the company.
    """
    company = await verify_company_access(company_id, user_id, db)

    if not company.tax_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax information not found for this company"
        )

    return {
        "data": {
            "id": str(company.tax_info.id),
            "company_id": str(company.id),
            "tax_regime": company.tax_info.tax_regime,
            "sii_activity_code": company.tax_info.sii_activity_code,
            "sii_activity_name": company.tax_info.sii_activity_name,
            "legal_representative_rut": company.tax_info.legal_representative_rut,
            "legal_representative_name": company.tax_info.legal_representative_name,
            "start_of_activities_date": company.tax_info.start_of_activities_date.isoformat() if company.tax_info.start_of_activities_date else None,
            "accounting_start_month": company.tax_info.accounting_start_month,
            "extra_data": company.tax_info.extra_data,
            "created_at": company.tax_info.created_at.isoformat(),
            "updated_at": company.tax_info.updated_at.isoformat(),
        }
    }


@router.put("/{company_id}/tax-info")
async def update_company_tax_info(
    company_id: UUID,
    data: CompanyTaxInfoUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update or create company tax information.

    User must have an active session with the company.
    """
    from datetime import date as date_type

    company = await verify_company_access(company_id, user_id, db)

    # Get or create tax info
    if not company.tax_info:
        tax_info = CompanyTaxInfo(company_id=company_id)
        db.add(tax_info)
        await db.flush()
    else:
        tax_info = company.tax_info

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)

    # Handle date conversion
    if "start_of_activities_date" in update_data and update_data["start_of_activities_date"]:
        try:
            update_data["start_of_activities_date"] = date_type.fromisoformat(
                update_data["start_of_activities_date"]
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format (YYYY-MM-DD)"
            )

    for field, value in update_data.items():
        setattr(tax_info, field, value)

    await db.commit()
    await db.refresh(tax_info)

    return {
        "data": {
            "id": str(tax_info.id),
            "company_id": str(company_id),
            "tax_regime": tax_info.tax_regime,
            "sii_activity_code": tax_info.sii_activity_code,
            "sii_activity_name": tax_info.sii_activity_name,
            "legal_representative_rut": tax_info.legal_representative_rut,
            "legal_representative_name": tax_info.legal_representative_name,
            "start_of_activities_date": tax_info.start_of_activities_date.isoformat() if tax_info.start_of_activities_date else None,
            "accounting_start_month": tax_info.accounting_start_month,
            "extra_data": tax_info.extra_data,
            "updated_at": tax_info.updated_at.isoformat(),
        },
        "message": "Tax information updated successfully"
    }

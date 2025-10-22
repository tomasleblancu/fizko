"""
Admin endpoints for company management
"""
import logging
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from ..config.database import get_db
from ..dependencies import get_current_user_id, require_auth
from ..db.models import (
    Company,
    CompanyTaxInfo,
    Session as SessionModel,
    Profile,
    PurchaseDocument,
    SalesDocument
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_auth)]
)


# Response models
class UserInfo(BaseModel):
    """User information"""
    id: str
    email: str
    full_name: Optional[str]
    name: Optional[str]
    lastname: Optional[str]
    rol: Optional[str]
    session_id: str
    is_active: bool
    last_accessed_at: Optional[datetime]
    created_at: datetime


class DocumentStats(BaseModel):
    """Document statistics"""
    total_purchase_documents: int
    total_sales_documents: int
    latest_purchase_date: Optional[datetime]
    latest_sales_date: Optional[datetime]
    total_purchase_amount: float
    total_sales_amount: float


class SyncAction(BaseModel):
    """Sync action information"""
    session_id: str
    user_email: str
    last_sync: Optional[datetime]
    total_syncs: int


class CompanySummary(BaseModel):
    """Company summary for list view"""
    id: str
    rut: str
    business_name: str
    trade_name: Optional[str]
    tax_regime: Optional[str]
    total_users: int
    total_documents: int
    created_at: datetime
    last_activity: Optional[datetime]


class CompanyDetailResponse(BaseModel):
    """Complete company information for admin view"""
    # Company info
    id: str
    rut: str
    business_name: str
    trade_name: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Tax info
    tax_regime: Optional[str]
    sii_activity_code: Optional[str]
    sii_activity_name: Optional[str]
    legal_representative_rut: Optional[str]
    legal_representative_name: Optional[str]

    # Users with access
    users: List[UserInfo]

    # Document statistics
    document_stats: DocumentStats

    # Sync actions
    sync_actions: List[SyncAction]


@router.get("/company/{company_id}", response_model=CompanyDetailResponse)
async def get_company_admin_detail(
    company_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete company information for admin view

    Includes:
    - Company basic info and tax info
    - All users with access to the company
    - Document statistics (purchase and sales)
    - Sync action history

    Args:
        company_id: Company UUID
        current_user_id: Authenticated user ID
        db: Database session

    Returns:
        CompanyDetailResponse with all company information

    Raises:
        404: Company not found
    """
    logger.info(f"Company detail requested for {company_id} by user {current_user_id}")

    # Check user role and access permissions
    user_stmt = select(Profile).where(Profile.id == current_user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    is_admin = user.rol == "admin-kaiken"

    # If not admin, check if user has access to this company
    if not is_admin:
        session_check_stmt = select(SessionModel).where(
            SessionModel.user_id == current_user_id,
            SessionModel.company_id == company_id
        )
        session_check = await db.execute(session_check_stmt)
        if not session_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this company"
            )

    # Get company with tax info
    company_stmt = select(Company).options(
        selectinload(Company.tax_info)
    ).where(Company.id == company_id)

    result = await db.execute(company_stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company {company_id} not found"
        )

    # Get users with access (through sessions)
    users_stmt = (
        select(SessionModel, Profile)
        .join(Profile, SessionModel.user_id == Profile.id)
        .where(SessionModel.company_id == company_id)
        .order_by(desc(SessionModel.last_accessed_at))
    )

    users_result = await db.execute(users_stmt)
    users_data = users_result.all()

    users = [
        UserInfo(
            id=str(profile.id),
            email=profile.email,
            full_name=profile.full_name,
            name=profile.name,
            lastname=profile.lastname,
            rol=profile.rol,
            session_id=str(session.id),
            is_active=session.is_active,
            last_accessed_at=session.last_accessed_at,
            created_at=session.created_at
        )
        for session, profile in users_data
    ]

    # Get document statistics
    # Purchase documents
    purchase_stats_stmt = select(
        func.count(PurchaseDocument.id).label('count'),
        func.max(PurchaseDocument.created_at).label('latest'),
        func.sum(PurchaseDocument.total_amount).label('total')
    ).where(PurchaseDocument.company_id == company_id)

    purchase_stats = (await db.execute(purchase_stats_stmt)).one()

    # Sales documents
    sales_stats_stmt = select(
        func.count(SalesDocument.id).label('count'),
        func.max(SalesDocument.created_at).label('latest'),
        func.sum(SalesDocument.total_amount).label('total')
    ).where(SalesDocument.company_id == company_id)

    sales_stats = (await db.execute(sales_stats_stmt)).one()

    document_stats = DocumentStats(
        total_purchase_documents=purchase_stats.count or 0,
        total_sales_documents=sales_stats.count or 0,
        latest_purchase_date=purchase_stats.latest,
        latest_sales_date=sales_stats.latest,
        total_purchase_amount=float(purchase_stats.total or 0),
        total_sales_amount=float(sales_stats.total or 0)
    )

    # Get sync actions (from sessions with last_accessed_at)
    # TODO: When we implement sync job tracking, use that instead
    sync_actions = [
        SyncAction(
            session_id=str(session.id),
            user_email=profile.email,
            last_sync=session.last_accessed_at,
            total_syncs=1 if session.last_accessed_at else 0  # Placeholder
        )
        for session, profile in users_data
        if session.last_accessed_at
    ]

    # Build response
    return CompanyDetailResponse(
        id=str(company.id),
        rut=company.rut,
        business_name=company.business_name,
        trade_name=company.trade_name,
        address=company.address,
        phone=company.phone,
        email=company.email,
        created_at=company.created_at,
        updated_at=company.updated_at,
        tax_regime=company.tax_info.tax_regime if company.tax_info else None,
        sii_activity_code=company.tax_info.sii_activity_code if company.tax_info else None,
        sii_activity_name=company.tax_info.sii_activity_name if company.tax_info else None,
        legal_representative_rut=company.tax_info.legal_representative_rut if company.tax_info else None,
        legal_representative_name=company.tax_info.legal_representative_name if company.tax_info else None,
        users=users,
        document_stats=document_stats,
        sync_actions=sync_actions
    )


@router.get("/companies", response_model=List[CompanySummary])
async def list_all_companies(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List companies accessible to the current user

    - If user has rol="admin-kaiken": returns ALL companies
    - Otherwise: returns only companies where user has an active session

    Returns a list of companies with:
    - Basic company info
    - Number of users with access
    - Total number of documents
    - Last activity timestamp

    Args:
        current_user_id: Authenticated user ID
        db: Database session

    Returns:
        List of CompanySummary objects
    """
    logger.info(f"Companies list requested by user {current_user_id}")

    # Get current user's profile to check role
    user_stmt = select(Profile).where(Profile.id == current_user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    is_admin = user.rol == "admin-kaiken"

    # Build companies query based on role
    if is_admin:
        # Admin can see all companies
        logger.info(f"User {current_user_id} is admin-kaiken, showing all companies")
        companies_stmt = select(Company).options(
            selectinload(Company.tax_info)
        ).order_by(desc(Company.created_at))
    else:
        # Regular user can only see companies they have sessions for
        logger.info(f"User {current_user_id} is regular user, showing only accessible companies")
        companies_stmt = (
            select(Company)
            .join(SessionModel, SessionModel.company_id == Company.id)
            .options(selectinload(Company.tax_info))
            .where(SessionModel.user_id == current_user_id)
            .order_by(desc(Company.created_at))
        )

    result = await db.execute(companies_stmt)
    companies = result.scalars().all()

    summaries = []
    for company in companies:
        # Count users with access
        users_count_stmt = select(func.count(SessionModel.id)).where(
            SessionModel.company_id == company.id
        )
        users_count = (await db.execute(users_count_stmt)).scalar() or 0

        # Count total documents
        purchase_count_stmt = select(func.count(PurchaseDocument.id)).where(
            PurchaseDocument.company_id == company.id
        )
        purchase_count = (await db.execute(purchase_count_stmt)).scalar() or 0

        sales_count_stmt = select(func.count(SalesDocument.id)).where(
            SalesDocument.company_id == company.id
        )
        sales_count = (await db.execute(sales_count_stmt)).scalar() or 0

        total_documents = purchase_count + sales_count

        # Get last activity (most recent session access)
        last_activity_stmt = select(
            func.max(SessionModel.last_accessed_at)
        ).where(SessionModel.company_id == company.id)
        last_activity = (await db.execute(last_activity_stmt)).scalar()

        summaries.append(CompanySummary(
            id=str(company.id),
            rut=company.rut,
            business_name=company.business_name,
            trade_name=company.trade_name,
            tax_regime=company.tax_info.tax_regime if company.tax_info else None,
            total_users=users_count,
            total_documents=total_documents,
            created_at=company.created_at,
            last_activity=last_activity
        ))

    return summaries

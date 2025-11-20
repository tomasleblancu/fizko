"""Sessions router - Manage user-company sessions."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...config.database import get_db
from ...db.models import Company, Session
from ...dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/sessions",
    tags=["sessions"],
    dependencies=[Depends(require_auth)]
)


# =============================================================================
# Request/Response Models
# =============================================================================

class SessionCreate(BaseModel):
    """Request model for creating a session."""
    company_id: str  # UUID string
    cookies: Optional[dict] = None
    resources: Optional[dict] = None


class SessionUpdate(BaseModel):
    """Request model for updating a session."""
    is_active: Optional[bool] = None
    cookies: Optional[dict] = None
    resources: Optional[dict] = None


class SessionCookiesUpdate(BaseModel):
    """Request model for updating session cookies."""
    cookies: dict


class SIICredentials(BaseModel):
    """Request model for saving SII credentials during onboarding."""
    rut: str
    password: str


# =============================================================================
# Endpoints
# =============================================================================

@router.get("")
async def list_sessions(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
) -> dict[str, Any]:
    """
    List all sessions for the authenticated user.

    Query params:
    - is_active: Filter by session status (true/false)
    - skip: Pagination offset
    - limit: Number of records to return
    """
    # Build query
    stmt = select(Session).options(
        selectinload(Session.company)
    ).where(Session.user_id == UUID(user_id))

    # Apply filters
    if is_active is not None:
        stmt = stmt.where(Session.is_active == is_active)

    # Apply pagination
    stmt = stmt.offset(skip).limit(limit).order_by(Session.last_accessed_at.desc().nullsfirst())

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # Get total count
    count_stmt = select(Session).where(Session.user_id == UUID(user_id))
    if is_active is not None:
        count_stmt = count_stmt.where(Session.is_active == is_active)
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    return {
        "data": [
            {
                "id": str(s.id),
                "user_id": str(s.user_id),
                "company_id": str(s.company_id),
                "company": {
                    "id": str(s.company.id),
                    "rut": s.company.rut,
                    "business_name": s.company.business_name,
                    "trade_name": s.company.trade_name,
                } if s.company else None,
                "is_active": s.is_active,
                "has_cookies": bool(s.cookies),
                "has_resources": bool(s.resources),
                "last_accessed_at": s.last_accessed_at.isoformat() if s.last_accessed_at else None,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sessions
        ],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total,
        }
    }


@router.get("/{session_id}")
async def get_session(
    session_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get detailed information about a specific session.

    User can only access their own sessions.
    """
    stmt = select(Session).options(
        selectinload(Session.company)
    ).where(
        Session.id == session_id,
        Session.user_id == UUID(user_id)
    )

    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {
        "data": {
            "id": str(session.id),
            "user_id": str(session.user_id),
            "company_id": str(session.company_id),
            "company": {
                "id": str(session.company.id),
                "rut": session.company.rut,
                "business_name": session.company.business_name,
                "trade_name": session.company.trade_name,
                "address": session.company.address,
                "phone": session.company.phone,
                "email": session.company.email,
            } if session.company else None,
            "is_active": session.is_active,
            "cookies": session.cookies,
            "resources": session.resources,
            "last_accessed_at": session.last_accessed_at.isoformat() if session.last_accessed_at else None,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
    }


@router.post("")
async def create_session(
    data: SessionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Create a new session to link user to an existing company.

    This is used when a user needs access to a company that already exists
    (e.g., invited by another user, or accessing a pre-created company).
    """
    company_id = UUID(data.company_id)

    # Verify company exists
    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Check if session already exists
    stmt = select(Session).where(
        Session.user_id == UUID(user_id),
        Session.company_id == company_id
    )
    result = await db.execute(stmt)
    existing_session = result.scalar_one_or_none()

    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already exists for this user and company"
        )

    # Create new session
    session = Session(
        user_id=UUID(user_id),
        company_id=company_id,
        is_active=True,
        cookies=data.cookies or {},
        resources=data.resources or {},
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return {
        "data": {
            "id": str(session.id),
            "user_id": str(session.user_id),
            "company_id": str(session.company_id),
            "is_active": session.is_active,
            "created_at": session.created_at.isoformat(),
        },
        "message": "Session created successfully"
    }


@router.put("/{session_id}")
async def update_session(
    session_id: UUID,
    data: SessionUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update session information (status, cookies, resources).

    User can only update their own sessions.
    """
    # Get session
    stmt = select(Session).where(
        Session.id == session_id,
        Session.user_id == UUID(user_id)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)

    # Update last_accessed_at
    session.last_accessed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    return {
        "data": {
            "id": str(session.id),
            "is_active": session.is_active,
            "has_cookies": bool(session.cookies),
            "has_resources": bool(session.resources),
            "last_accessed_at": session.last_accessed_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        },
        "message": "Session updated successfully"
    }


@router.delete("/{session_id}")
async def deactivate_session(
    session_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Deactivate a session (soft delete).

    User can only deactivate their own sessions.
    """
    # Get session
    stmt = select(Session).where(
        Session.id == session_id,
        Session.user_id == UUID(user_id)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Deactivate session
    session.is_active = False

    await db.commit()

    return {
        "data": {
            "id": str(session.id),
            "is_active": False,
        },
        "message": "Session deactivated successfully"
    }


@router.get("/{session_id}/cookies")
async def get_session_cookies(
    session_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get cookies stored in a session.

    User can only access their own sessions.
    """
    stmt = select(Session).where(
        Session.id == session_id,
        Session.user_id == UUID(user_id)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {
        "data": {
            "session_id": str(session.id),
            "cookies": session.cookies or {},
        }
    }


@router.put("/{session_id}/cookies")
async def update_session_cookies(
    session_id: UUID,
    data: SessionCookiesUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update cookies stored in a session.

    This replaces all existing cookies with the new ones provided.
    User can only update their own sessions.
    """
    # Get session
    stmt = select(Session).where(
        Session.id == session_id,
        Session.user_id == UUID(user_id)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Update cookies
    session.cookies = data.cookies
    session.last_accessed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    return {
        "data": {
            "session_id": str(session.id),
            "cookies": session.cookies,
            "updated_at": session.updated_at.isoformat(),
        },
        "message": "Session cookies updated successfully"
    }


@router.post("/onboarding/sii-credentials")
async def save_sii_credentials(
    data: SIICredentials,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    DEPRECATED: Use /api/sii/auth/login instead.

    This endpoint is kept for backward compatibility but should not be used.
    The new endpoint /api/sii/auth/login provides better SII integration
    and real-time data extraction.

    Save SII credentials during onboarding.
    Creates a MOCK active session immediately to allow user to pass onboarding,
    then processes credentials in background to fetch real company data.

    The mock company will be updated with real SII data once processed.
    """
    # NOTE: Profile creation now handled by database trigger (011_add_profile_trigger.sql)
    # If profile doesn't exist, it means the trigger hasn't been applied yet
    user_uuid = UUID(user_id)

    # Check if user already has a session
    stmt = select(Session).where(
        Session.user_id == user_uuid
    ).order_by(Session.created_at.desc())
    result = await db.execute(stmt)
    existing_session = result.scalar_one_or_none()

    # Prepare credentials to store
    credentials = {
        "sii_rut": data.rut,
        "sii_password": data.password,
        "onboarding_completed": False,
        "is_mock": True,  # Mark as mock until real data is fetched
    }

    if existing_session:
        # Update existing session with new credentials and activate it
        existing_session.cookies = credentials
        existing_session.is_active = True  # Activate immediately
        existing_session.last_accessed_at = datetime.utcnow()

        # IMPORTANT: Also save password to Company model for SII integration
        company_stmt = select(Company).where(Company.id == existing_session.company_id)
        company_result = await db.execute(company_stmt)
        company = company_result.scalar_one_or_none()
        if company:
            company.sii_password = data.password

        await db.commit()
        await db.refresh(existing_session)

        return {
            "data": {
                "session_id": str(existing_session.id),
                "is_active": existing_session.is_active,
                "has_credentials": True,
            },
            "message": "Sesión creada. Obteniendo información de la empresa..."
        }
    else:
        # Create a mock company for new users
        mock_company = Company(
            rut=data.rut,
            business_name=f"Empresa (RUT: {data.rut})",
            trade_name="Cargando...",
        )
        mock_company.sii_password = data.password  # Store SII password for authentication (will be encrypted)
        db.add(mock_company)
        await db.flush()  # Get the company ID

        # Create active session with mock company
        new_session = Session(
            user_id=user_uuid,
            company_id=mock_company.id,
            is_active=True,  # Activate immediately
            cookies=credentials,
            resources={
                "is_mock": True,
                "pending_sii_sync": True,
            },
            last_accessed_at=datetime.utcnow(),
        )
        db.add(new_session)

        await db.commit()
        await db.refresh(new_session)

        # TODO: Launch background task to process SII credentials
        # asyncio.create_task(process_sii_onboarding(user_id, data.rut, data.password, db))

        return {
            "data": {
                "session_id": str(new_session.id),
                "company_id": str(mock_company.id),
                "is_active": new_session.is_active,
                "has_credentials": True,
            },
            "message": "Sesión creada. Obteniendo información de la empresa..."
        }

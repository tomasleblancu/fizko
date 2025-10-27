"""Profile router - Manage user profile information."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import Profile
from ...dependencies import get_current_user_id, require_auth

router = APIRouter(
    prefix="/api/profile",
    tags=["profile"],
    dependencies=[Depends(require_auth)]
)


# =============================================================================
# Request/Response Models
# =============================================================================

class ProfileUpdate(BaseModel):
    """Request model for updating user profile."""
    name: Optional[str] = None
    lastname: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ProfileResponse(BaseModel):
    """Response model for user profile."""
    id: str
    email: str
    name: Optional[str] = None
    lastname: Optional[str] = None
    phone: Optional[str] = None
    phone_verified: bool = False
    phone_verified_at: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    avatar_url: Optional[str] = None
    rol: Optional[str] = None
    created_at: str
    updated_at: str


# =============================================================================
# Endpoints
# =============================================================================

@router.get("")
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get the authenticated user's profile information.
    """
    stmt = select(Profile).where(Profile.id == UUID(user_id))
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return {
        "data": {
            "id": str(profile.id),
            "email": profile.email,
            "name": profile.name,
            "lastname": profile.lastname,
            "phone": profile.phone,
            "phone_verified": profile.phone_verified,
            "phone_verified_at": profile.phone_verified_at.isoformat() if profile.phone_verified_at else None,
            "full_name": profile.full_name,
            "company_name": profile.company_name,
            "avatar_url": profile.avatar_url,
            "rol": profile.rol,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
        }
    }


@router.patch("")
async def update_profile(
    data: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update the authenticated user's profile information.

    Only provided fields will be updated (partial update).
    """
    stmt = select(Profile).where(Profile.id == UUID(user_id))
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)

    # If phone number is being updated, reset verification status
    if "phone" in update_data and update_data["phone"] != profile.phone:
        profile.phone_verified = False
        profile.phone_verified_at = None

    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    return {
        "data": {
            "id": str(profile.id),
            "email": profile.email,
            "name": profile.name,
            "lastname": profile.lastname,
            "phone": profile.phone,
            "phone_verified": profile.phone_verified,
            "phone_verified_at": profile.phone_verified_at.isoformat() if profile.phone_verified_at else None,
            "full_name": profile.full_name,
            "company_name": profile.company_name,
            "avatar_url": profile.avatar_url,
            "rol": profile.rol,
            "updated_at": profile.updated_at.isoformat(),
        },
        "message": "Profile updated successfully"
    }


@router.post("/verify-phone/request")
async def request_phone_verification(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Request phone number verification.
    Sends a verification code to the user's phone number.

    TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
    """
    stmt = select(Profile).where(Profile.id == UUID(user_id))
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    if not profile.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No phone number registered"
        )

    if profile.phone_verified:
        return {
            "message": "Phone number already verified",
            "already_verified": True
        }

    # TODO: Generate verification code and send SMS
    # For now, just return success
    # verification_code = generate_random_code(6)
    # send_sms(profile.phone, f"Your verification code is: {verification_code}")
    # store_verification_code(user_id, verification_code)

    return {
        "message": "Verification code sent successfully (feature not implemented yet)",
        "phone": profile.phone,
        "note": "SMS integration pending - implement with Twilio or similar service"
    }


@router.post("/verify-phone/confirm")
async def confirm_phone_verification(
    code: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Confirm phone number verification with the code sent via SMS.

    TODO: Integrate with verification code storage and validation
    """
    from datetime import datetime as dt

    stmt = select(Profile).where(Profile.id == UUID(user_id))
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    if profile.phone_verified:
        return {
            "message": "Phone number already verified",
            "already_verified": True
        }

    # TODO: Validate verification code
    # stored_code = get_verification_code(user_id)
    # if code != stored_code:
    #     raise HTTPException(status_code=400, detail="Invalid verification code")

    # For now, accept any 6-digit code as valid
    if not code or len(code) != 6 or not code.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code format (expected 6 digits)"
        )

    # Mark phone as verified
    profile.phone_verified = True
    profile.phone_verified_at = dt.now()

    await db.commit()
    await db.refresh(profile)

    return {
        "data": {
            "phone_verified": profile.phone_verified,
            "phone_verified_at": profile.phone_verified_at.isoformat(),
        },
        "message": "Phone number verified successfully"
    }

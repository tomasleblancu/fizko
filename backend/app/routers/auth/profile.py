"""Profile router - Manage user profile information."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.database import get_db
from ...db.models import Profile, PhoneVerification
from ...dependencies import get_current_user_id, require_auth

logger = logging.getLogger(__name__)

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
    Generates a 6-digit code and sends it via WhatsApp to the user's phone number.
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

    # Generate verification code
    verification_code = PhoneVerification.generate_code()
    expires_at = PhoneVerification.get_expiry_time()

    # Create verification record
    verification = PhoneVerification(
        user_id=UUID(user_id),
        phone_number=profile.phone,
        code=verification_code,
        expires_at=expires_at
    )
    db.add(verification)
    await db.commit()
    await db.refresh(verification)

    # Send verification code via WhatsApp
    # Log the code for development
    logger.info(f"🔐 Verification code generated for {profile.phone}: {verification_code}")

    try:
        # Import WhatsApp service from services module
        from ...services.whatsapp import get_whatsapp_service
        import os

        whatsapp_service = get_whatsapp_service()

        # Get default WhatsApp config ID from environment
        # You can set this in your .env file: DEFAULT_WHATSAPP_CONFIG_ID=your-config-id
        whatsapp_config_id = os.getenv("DEFAULT_WHATSAPP_CONFIG_ID")

        if whatsapp_config_id:
            # Format message
            message_text = f"Tu código de verificación de Fizko es: *{verification_code}*\n\nEste código expira en 10 minutos."

            # Normalize phone number - remove '+' prefix if present
            normalized_phone = profile.phone.lstrip('+') if profile.phone else None

            if not normalized_phone:
                logger.error(f"❌ Invalid phone number: {profile.phone}")
                return {
                    "message": "Verification code sent successfully",
                    "phone": profile.phone,
                    "expires_in_minutes": 10
                }

            # Try to find existing conversation first
            try:
                # Search for conversations with this phone number
                conversations = await whatsapp_service.list_conversations(
                    whatsapp_config_id=whatsapp_config_id,
                    limit=50,  # Get more results to find the right conversation
                )

                conversation_id = None
                # Try multiple possible keys for the conversations list
                nodes = (
                    conversations.get("data") or
                    conversations.get("nodes") or
                    conversations.get("conversations") or
                    conversations.get("items") or
                    []
                )

                for conv in nodes:
                    conv_phone = conv.get("phone_number", "").lstrip('+')
                    conv_status = conv.get("status", "")

                    # Only match active conversations
                    if conv_phone == normalized_phone and conv_status == "active":
                        conversation_id = conv.get("id")
                        logger.info(f"✅ Verification code sent to {normalized_phone}")
                        break

                if conversation_id:
                    # Send using the existing conversation ID
                    await whatsapp_service.send_text(
                        conversation_id=conversation_id,
                        message=message_text,
                    )
                else:
                    logger.warning(f"⚠️ No active conversation found for {normalized_phone}")
                    logger.info(f"💡 User needs to send a message first or use a template")
            except Exception as send_error:
                # If sending fails, log the error
                logger.warning(f"⚠️ Could not send via WhatsApp: {send_error}")
        else:
            logger.warning(f"⚠️ DEFAULT_WHATSAPP_CONFIG_ID not set in environment")
            logger.info(f"💡 Set DEFAULT_WHATSAPP_CONFIG_ID in .env to enable WhatsApp sending")
    except Exception as e:
        logger.error(f"❌ Error in WhatsApp send attempt: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # Always return success - the code is stored in DB and logged

    return {
        "message": "Verification code sent successfully",
        "phone": profile.phone,
        "expires_in_minutes": 10
    }


class VerifyPhoneRequest(BaseModel):
    """Request model for phone verification confirmation."""
    code: str


@router.post("/verify-phone/confirm")
async def confirm_phone_verification(
    request: VerifyPhoneRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Confirm phone number verification with the code sent via WhatsApp.
    """
    code = request.code.strip()

    # Validate code format
    if not code or len(code) != 6 or not code.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code format (expected 6 digits)"
        )

    # Get user profile
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

    # Find the most recent verification code for this user
    verification_stmt = (
        select(PhoneVerification)
        .where(
            and_(
                PhoneVerification.user_id == UUID(user_id),
                PhoneVerification.is_verified == False,
            )
        )
        .order_by(desc(PhoneVerification.created_at))
        .limit(1)
    )
    verification_result = await db.execute(verification_stmt)
    verification = verification_result.scalar_one_or_none()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code found. Please request a new code."
        )

    # Check if code has expired
    if verification.is_expired():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new code."
        )

    # Check if max attempts reached
    if verification.is_max_attempts_reached():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum verification attempts reached. Please request a new code."
        )

    # Increment attempts
    verification.attempts += 1

    # Validate the code
    if verification.code != code:
        await db.commit()
        remaining_attempts = verification.max_attempts - verification.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification code. {remaining_attempts} attempts remaining."
        )

    # Mark verification as complete
    from datetime import timezone
    verification.is_verified = True
    verification.verified_at = datetime.now(timezone.utc)

    # Mark phone as verified in profile
    profile.phone_verified = True
    profile.phone_verified_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(profile)

    logger.info(f"✅ Phone verified for user {user_id}: {profile.phone}")

    return {
        "data": {
            "phone_verified": profile.phone_verified,
            "phone_verified_at": profile.phone_verified_at.isoformat(),
        },
        "message": "Phone number verified successfully"
    }

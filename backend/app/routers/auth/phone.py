"""Phone authentication endpoints using WhatsApp OTP."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.supabase import get_supabase_client
from app.services.auth import (
    PhoneAuthService,
    CodeExpiredError,
    CodeNotFoundError,
    InvalidCodeError,
    MaxAttemptsExceededError,
)
from .schemas import (
    RequestCodeRequest,
    RequestCodeResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
    VerifyCodeErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_phone_auth_service() -> PhoneAuthService:
    """Dependency to get PhoneAuthService instance."""
    supabase = get_supabase_client()
    return PhoneAuthService(supabase.client)


@router.post(
    "/phone/request-code",
    response_model=RequestCodeResponse,
    status_code=status.HTTP_200_OK,
)
async def request_verification_code(
    request: RequestCodeRequest,
    service: PhoneAuthService = Depends(get_phone_auth_service),
):
    """
    Request verification code to be sent via WhatsApp.

    This endpoint generates a 6-digit code and sends it to the specified
    phone number via WhatsApp. The code is valid for 5 minutes.

    **Rate Limiting**: Max 3 requests per hour per phone number.

    **Requirements**:
    - Phone number must have an active WhatsApp conversation
    - If no active conversation exists, user must initiate one first

    Args:
        request: Phone number in E.164 format (+56912345678)
        service: Phone auth service dependency

    Returns:
        Success response with expiry time and retry delay

    Raises:
        400: Invalid phone number or rate limit exceeded
        500: Failed to send code via WhatsApp
    """
    phone_number = request.phone_number
    logger.info(f"📱 Verification code requested for {phone_number}")

    try:
        result = await service.request_verification_code(phone_number)

        logger.info(f"✅ Verification code sent to {phone_number}")

        return RequestCodeResponse(
            success=result["success"],
            message="Código enviado por WhatsApp",
            expires_at=result["expires_at"],
            retry_after=result["retry_after"],
        )

    except ValueError as e:
        # Rate limit or validation error
        logger.warning(f"⚠️  Request code failed for {phone_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"❌ Unexpected error requesting code: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar código de verificación. Por favor intenta nuevamente.",
        )


@router.post(
    "/phone/verify-code",
    response_model=VerifyCodeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": VerifyCodeErrorResponse},
    },
)
async def verify_code(
    request: VerifyCodeRequest,
    service: PhoneAuthService = Depends(get_phone_auth_service),
):
    """
    Verify code and authenticate user.

    This endpoint verifies the 6-digit code sent via WhatsApp and returns
    a JWT access token if the code is valid.

    **Flow**:
    1. Verify code hasn't expired (5 minutes)
    2. Check attempts < 3
    3. Validate code (timing-safe comparison)
    4. Create or get user from database
    5. Generate JWT access token
    6. Return token + user profile

    **If user doesn't exist**: A new user is created automatically.

    Args:
        request: Phone number and 6-digit code
        service: Phone auth service dependency

    Returns:
        JWT access token, refresh token, and user profile

    Raises:
        400: Code expired, invalid, or max attempts exceeded
        404: No code found for phone number
        500: Server error
    """
    phone_number = request.phone_number
    code = request.code

    logger.info(f"🔐 Code verification attempt for {phone_number}")

    try:
        result = await service.verify_code(phone_number, code)

        logger.info(f"✅ User authenticated: {result['user']['id']} ({phone_number})")

        return VerifyCodeResponse(**result)

    except CodeNotFoundError as e:
        logger.warning(f"⚠️  No code found for {phone_number}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except CodeExpiredError as e:
        logger.warning(f"⏰ Code expired for {phone_number}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except InvalidCodeError as e:
        # Extract attempts remaining from error message
        logger.warning(f"❌ Invalid code for {phone_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except MaxAttemptsExceededError as e:
        logger.warning(f"🚫 Max attempts exceeded for {phone_number}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"❌ Unexpected error verifying code: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al verificar código. Por favor intenta nuevamente.",
        )

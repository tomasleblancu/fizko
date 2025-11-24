"""Pydantic schemas for authentication endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RequestCodeRequest(BaseModel):
    """Request to send verification code to phone number."""

    phone_number: str = Field(
        ...,
        description="Phone number in E.164 format",
        examples=["+56912345678"],
        min_length=8,
        max_length=20,
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate and normalize phone number to E.164 format."""
        # Remove whitespace
        v = v.strip()

        # Add + prefix if missing
        if not v.startswith("+"):
            # Assume Chile (+56) if no country code
            if v.startswith("56"):
                v = f"+{v}"
            elif v.startswith("9"):  # Mobile numbers in Chile start with 9
                v = f"+56{v}"
            else:
                raise ValueError("Phone number must include country code (e.g., +56912345678)")

        # Basic validation
        if not v[1:].isdigit():
            raise ValueError("Phone number must contain only digits after + prefix")

        if len(v) < 9 or len(v) > 20:
            raise ValueError("Invalid phone number length")

        return v


class RequestCodeResponse(BaseModel):
    """Response after requesting verification code."""

    success: bool
    message: str = "Código enviado por WhatsApp"
    expires_at: datetime
    retry_after: int = Field(
        default=60,
        description="Seconds to wait before requesting another code",
    )


class VerifyCodeRequest(BaseModel):
    """Request to verify code and authenticate user."""

    phone_number: str = Field(
        ...,
        description="Phone number in E.164 format",
        examples=["+56912345678"],
    )
    code: str = Field(
        ...,
        description="Six-digit verification code",
        min_length=6,
        max_length=6,
        pattern="^[0-9]{6}$",
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Normalize phone number."""
        v = v.strip()
        if not v.startswith("+"):
            if v.startswith("56"):
                v = f"+{v}"
            elif v.startswith("9"):
                v = f"+56{v}"
            else:
                raise ValueError("Phone number must include country code")
        return v


class UserProfile(BaseModel):
    """User profile information."""

    id: str
    phone: str
    email: Optional[str] = None
    created_at: datetime


class VerifyCodeResponse(BaseModel):
    """Response after successful code verification."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    user: UserProfile


class VerifyCodeErrorResponse(BaseModel):
    """Error response for code verification."""

    error: str = Field(
        ...,
        description="Error code: invalid_code, code_expired, max_attempts_exceeded",
    )
    message: str
    attempts_remaining: Optional[int] = None

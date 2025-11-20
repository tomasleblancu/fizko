"""Phone verification model."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
import secrets

from sqlalchemy import Text, text, Integer
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PhoneVerification(Base):
    """Phone verification codes for user phone number verification.

    Stores verification codes sent via WhatsApp to verify user phone numbers.
    Codes expire after 10 minutes and can only be used once.
    """

    __tablename__ = "phone_verifications"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    phone_number: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, server_default=text("3"), nullable=False)
    is_verified: Mapped[bool] = mapped_column(
        server_default=text("false"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    @staticmethod
    def generate_code() -> str:
        """Generate a random 6-digit verification code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

    @staticmethod
    def get_expiry_time() -> datetime:
        """Get expiration time for verification code (10 minutes from now)."""
        from datetime import timezone
        return datetime.now(timezone.utc) + timedelta(minutes=10)

    def is_expired(self) -> bool:
        """Check if the verification code has expired."""
        from datetime import timezone
        return datetime.now(timezone.utc) > self.expires_at

    def is_max_attempts_reached(self) -> bool:
        """Check if maximum verification attempts have been reached."""
        return self.attempts >= self.max_attempts

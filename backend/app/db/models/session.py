"""Session model for user-company linking."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, Index, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .user import Profile


class Session(Base):
    """Links users to companies and stores session-specific data.

    Many-to-many relationship between Profile and Company. Each session represents
    a user's access to a specific company, storing cookies and resources needed
    for operations like SII integration.
    """

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id")
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id")
    )

    # Session status
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    # Session data storage
    cookies: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )
    resources: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )

    # Timestamps
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        # Unique constraint: one session per user-company pair
        UniqueConstraint("user_id", "company_id", name="sessions_user_company_unique"),
        # Indexes for efficient queries
        Index("ix_sessions_user_company", "user_id", "company_id"),
        Index("ix_sessions_company_active", "company_id", "is_active"),
    )

    # Relationships
    user: Mapped["Profile"] = relationship("Profile", back_populates="sessions")
    company: Mapped["Company"] = relationship("Company", back_populates="sessions")

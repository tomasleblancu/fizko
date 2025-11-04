"""User profile model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .chat import Conversation, Message
    from .session import Session


class Profile(Base):
    """User profiles extending auth.users with additional information.

    Represents individual users in the system. Each user can access multiple
    companies through Session records.
    """

    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    full_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone_verified: Mapped[bool] = mapped_column(
        server_default=text("false"), nullable=False
    )
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    company_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    name: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, server_default=text("''::text")
    )
    lastname: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, server_default=text("''::text")
    )
    rol: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, server_default=text("''::text")
    )

    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )

    # Brain (Memory) relationship
    brain_memories: Mapped[list["UserBrain"]] = relationship(
        "UserBrain", back_populates="user", cascade="all, delete-orphan"
    )

"""Chat and messaging models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import Profile


class Conversation(Base):
    """Chat conversations between users and AI assistant."""

    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id"))
    chatkit_session_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(
        Text, server_default=text("'Nueva conversación'::text")
    )
    status: Mapped[str] = mapped_column(Text, server_default=text("'active'::text"))
    meta_data: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint(
            "status = ANY (ARRAY['active'::text, 'archived'::text, 'completed'::text])",
            name="conversations_status_check",
        ),
    )

    # Relationships
    user: Mapped["Profile"] = relationship("Profile", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    """Individual messages within chat conversations."""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("conversations.id")
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("profiles.id"))
    role: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    message_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint(
            "role = ANY (ARRAY['user'::text, 'assistant'::text, 'system'::text])",
            name="messages_role_check",
        ),
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    user: Mapped["Profile"] = relationship("Profile", back_populates="messages")


class ChatKitAttachment(Base):
    """ChatKit attachment metadata stored in the database.

    Note: This stores only metadata. The actual file is stored in Supabase Storage
    via the two-phase upload process handled by AttachmentStore.
    """

    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    thread_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    upload_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )

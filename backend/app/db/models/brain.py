"""Brain models for storing Mem0 memory references.

These models track memories stored in Mem0, allowing for:
1. Update existing memories instead of creating duplicates
2. Query and manage memories from the database
3. Track memory metadata and slugs for organized retrieval
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class UserBrain(Base):
    """
    User-specific memories stored in Mem0.

    Tracks personal preferences, history, and information specific to each user.
    Each memory is identified by a slug to enable updates instead of duplicates.

    Examples of user memories:
    - "user_preferred_tax_regime" - User's preference for tax regime
    - "user_role" - User's role in the company (owner, accountant, etc.)
    - "user_joined_date" - When user joined the company
    - "user_preferences" - General user preferences
    """

    __tablename__ = "user_brain"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Mem0 reference
    memory_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Mem0 memory ID returned from API"
    )

    # Memory identification
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Descriptive slug to identify the memory (e.g., 'user_tax_regime_preference')"
    )

    # Memory content (cached for quick access)
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The actual memory content stored in Mem0"
    )

    # Metadata (renamed to avoid SQLAlchemy reserved word)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata stored with the memory"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="brain_memories"
    )

    # Indexes for efficient queries
    __table_args__ = (
        Index("ix_user_brain_user_slug", "user_id", "slug", unique=True),
        Index("ix_user_brain_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<UserBrain(id={self.id}, user_id={self.user_id}, slug='{self.slug}')>"


class CompanyBrain(Base):
    """
    Company-wide memories stored in Mem0.

    Tracks shared knowledge and information across the company that all users can access.
    Each memory is identified by a slug to enable updates instead of duplicates.

    Examples of company memories:
    - "company_tax_regime" - Company's tax regime
    - "company_activity" - Company's economic activity
    - "company_start_date" - When company started operations
    - "company_has_employees" - Whether company has formal employees
    - "company_import_export" - Company's import/export status
    """

    __tablename__ = "company_brain"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )

    # Foreign keys
    company_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Mem0 reference
    memory_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Mem0 memory ID returned from API"
    )

    # Memory identification
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Descriptive slug to identify the memory (e.g., 'company_tax_regime')"
    )

    # Memory content (cached for quick access)
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The actual memory content stored in Mem0"
    )

    # Metadata (renamed to avoid SQLAlchemy reserved word)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata stored with the memory"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="brain_memories"
    )

    # Indexes for efficient queries
    __table_args__ = (
        Index("ix_company_brain_company_slug", "company_id", "slug", unique=True),
        Index("ix_company_brain_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CompanyBrain(id={self.id}, company_id={self.company_id}, slug='{self.slug}')>"

"""Contact model for providers and clients."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .documents import PurchaseDocument, SalesDocument


class Contact(Base):
    """Business contacts (providers, clients, or both).

    Stores contact information for business entities that the company
    does business with. A contact can be a provider (supplier), a client,
    or both.
    """

    __tablename__ = "contacts"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE")
    )

    # Contact identification
    rut: Mapped[str] = mapped_column(Text)  # Chilean tax ID
    business_name: Mapped[str] = mapped_column(Text)
    trade_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contact type: 'provider', 'client', or 'both'
    contact_type: Mapped[str] = mapped_column(Text)

    # Contact information
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional flexible data
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        # RUT must be unique within a company
        UniqueConstraint("company_id", "rut", name="contacts_company_rut_unique"),
        # Contact type must be one of: provider, client, both
        CheckConstraint(
            "contact_type = ANY (ARRAY['provider'::text, 'client'::text, 'both'::text])",
            name="contacts_contact_type_check",
        ),
        # Indexes for efficient queries
        Index("idx_contacts_company_id", "company_id"),
        Index("idx_contacts_company_type", "company_id", "contact_type"),
        Index("idx_contacts_rut", "rut"),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="contacts")
    purchase_documents: Mapped[list["PurchaseDocument"]] = relationship(
        "PurchaseDocument", back_populates="contact"
    )
    sales_documents: Mapped[list["SalesDocument"]] = relationship(
        "SalesDocument", back_populates="contact"
    )

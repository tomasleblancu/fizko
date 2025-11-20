"""Honorarios receipts models for professional services."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .contact import Contact


class HonorariosReceipt(Base):
    """Honorarios receipts (boletas de honorarios).

    Represents professional services fee receipts, both received (paid to service providers)
    and issued (received for professional services rendered).

    In Chile, "boletas de honorarios" are used to document payments for professional
    services and are subject to a 10% withholding tax (retención).
    """

    __tablename__ = "honorarios_receipts"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE")
    )

    # Receipt type
    receipt_type: Mapped[str] = mapped_column(
        Text
    )  # 'received' (paid to provider) or 'issued' (received for service)

    # Document identification
    folio: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    issue_date: Mapped[date] = mapped_column(Date)
    emission_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Issuer information (service provider)
    issuer_rut: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issuer_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Recipient information (service receiver)
    recipient_rut: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recipient_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Financial information
    gross_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), server_default=text("0")
    )  # Monto bruto (honorarios brutos)
    issuer_retention: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), server_default=text("0")
    )  # Retención emisor
    recipient_retention: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), server_default=text("0")
    )  # Retención receptor (typically 10%)
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), server_default=text("0")
    )  # Monto líquido (net after retentions)

    # Status
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending'::text")
    )  # pending, approved, rejected, cancelled, vigente, anulada

    # Additional data
    is_professional_society: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )  # Sociedad profesional
    is_manual: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )  # Ingresada manualmente
    emission_user: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contact reference (optional)
    contact_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )

    # SII integration
    sii_track_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
        CheckConstraint(
            "receipt_type IN ('received', 'issued')",
            name="honorarios_receipts_receipt_type_check",
        ),
        CheckConstraint(
            "status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text, "
            "'cancelled'::text, 'vigente'::text, 'anulada'::text])",
            name="honorarios_receipts_status_check",
        ),
        CheckConstraint(
            "gross_amount >= 0", name="honorarios_receipts_gross_amount_check"
        ),
        CheckConstraint("net_amount >= 0", name="honorarios_receipts_net_amount_check"),
        # Indexes for efficient queries
        Index("ix_honorarios_receipts_company_id", "company_id"),
        Index("ix_honorarios_receipts_company_type", "company_id", "receipt_type"),
        Index("ix_honorarios_receipts_company_date", "company_id", "issue_date"),
        Index("ix_honorarios_receipts_issuer_rut", "issuer_rut"),
        Index("ix_honorarios_receipts_recipient_rut", "recipient_rut"),
        Index("ix_honorarios_receipts_contact_id", "contact_id"),
        Index("ix_honorarios_receipts_status", "status"),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="honorarios_receipts")
    contact: Mapped[Optional["Contact"]] = relationship(
        "Contact", back_populates="honorarios_receipts"
    )

    @property
    def total_retention(self) -> Decimal:
        """Calculate total retention amount."""
        return self.issuer_retention + self.recipient_retention

    @property
    def retention_percentage(self) -> Optional[Decimal]:
        """Calculate retention percentage (typically 10% for honorarios)."""
        if self.gross_amount > 0:
            return (self.total_retention / self.gross_amount) * 100
        return None

    def __repr__(self) -> str:
        return (
            f"<HonorariosReceipt(id={self.id}, folio={self.folio}, "
            f"type={self.receipt_type}, gross={self.gross_amount}, "
            f"net={self.net_amount})>"
        )

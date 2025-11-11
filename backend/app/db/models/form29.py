"""Form 29 model for monthly IVA declarations."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import DATE, JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .form29_sii_download import Form29SIIDownload


class Form29(Base):
    """Form 29 - Monthly IVA (VAT) declaration.

    Represents the Chilean F29 tax form for monthly VAT reporting. This form
    calculates the net IVA to pay or carry forward as credit based on sales
    and purchases for a given period.

    Draft Lifecycle:
    1. draft -> User creates and edits the form
    2. validated -> System validates calculations
    3. confirmed -> User confirms for submission
    4. submitted -> Form submitted to SII
    5. paid -> Payment confirmed
    6. cancelled -> Superseded by a newer revision
    """

    __tablename__ = "form29"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id")
    )

    # Period
    period_year: Mapped[int] = mapped_column(Integer)
    period_month: Mapped[int] = mapped_column(Integer)

    # Revision tracking (for multiple drafts of same period)
    revision_number: Mapped[int] = mapped_column(Integer, server_default=text("1"))

    # Sales summary
    total_sales: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    taxable_sales: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    exempt_sales: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    sales_tax: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # Purchases summary
    total_purchases: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    taxable_purchases: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    purchases_tax: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # IVA calculation
    iva_to_pay: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    iva_credit: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    net_iva: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # Previous month credit (remanente de crédito fiscal mes anterior)
    # This is the credit carried forward from the previous month's F29
    previous_month_credit: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # User tracking
    # Note: Foreign keys to auth.users exist in DB but not in SQLAlchemy model
    # because auth schema is managed separately by Supabase
    created_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    confirmed_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    # Validation tracking
    validation_status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending'::text")
    )  # pending, valid, invalid, warning
    validation_errors: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, server_default=text("'[]'::jsonb")
    )

    # Confirmation tracking
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    confirmation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'draft'::text")
    )  # draft, validated, confirmed, submitted, paid, cancelled
    submission_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    folio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Payment tracking
    payment_status: Mapped[str] = mapped_column(
        Text, server_default=text("'unpaid'::text")
    )  # unpaid, pending, paid, partially_paid, overdue
    payment_date: Mapped[Optional[date]] = mapped_column(DATE, nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_amount_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Link to SII download (when form is submitted and downloaded)
    sii_download_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("form29_sii_downloads.id"), nullable=True
    )

    # Additional flexible data
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )
    form_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in database
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
        # Unique constraint: one Form29 per company per period per revision
        UniqueConstraint(
            "company_id", "period_year", "period_month", "revision_number",
            name="form29_company_period_revision_unique"
        ),
        # Check constraints
        CheckConstraint(
            "period_month >= 1 AND period_month <= 12",
            name="form29_period_month_check",
        ),
        CheckConstraint(
            "status = ANY (ARRAY['draft'::text, 'validated'::text, 'confirmed'::text, 'submitted'::text, 'paid'::text, 'cancelled'::text])",
            name="form29_status_check",
        ),
        CheckConstraint(
            "validation_status = ANY (ARRAY['pending'::text, 'valid'::text, 'invalid'::text, 'warning'::text])",
            name="form29_validation_status_check",
        ),
        CheckConstraint(
            "payment_status = ANY (ARRAY['unpaid'::text, 'pending'::text, 'paid'::text, 'partially_paid'::text, 'overdue'::text])",
            name="form29_payment_status_check",
        ),
        # Indexes for efficient queries
        Index("ix_form29_company_period", "company_id", "period_year", "period_month"),
        Index("ix_form29_active_drafts", "company_id", "period_year", "period_month", postgresql_where=text("status = 'draft'")),
        Index("ix_form29_ready_for_submission", "company_id", "status", postgresql_where=text("status IN ('validated', 'confirmed')")),
        Index("ix_form29_payment_status", "company_id", "payment_status", postgresql_where=text("payment_status IN ('unpaid', 'pending', 'overdue')")),
        Index("ix_form29_created_by", "created_by_user_id", "created_at"),
        Index("ix_form29_sii_link", "sii_download_id", postgresql_where=text("sii_download_id IS NOT NULL")),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="form29_records")

    # New relationship: this Form29 points to SII download
    sii_download_link: Mapped[Optional["Form29SIIDownload"]] = relationship(
        "Form29SIIDownload",
        foreign_keys=[sii_download_id],
        back_populates="linked_form29",
        uselist=False
    )

    # Legacy relationship: SII download points to this Form29
    sii_download_legacy: Mapped[Optional["Form29SIIDownload"]] = relationship(
        "Form29SIIDownload",
        foreign_keys="Form29SIIDownload.form29_id",
        back_populates="form29",
        uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<Form29("
            f"id={self.id}, "
            f"period={self.period_year}-{self.period_month:02d}, "
            f"revision={self.revision_number}, "
            f"status={self.status}, "
            f"net_iva={self.net_iva}"
            f")>"
        )

    # Helper properties
    @property
    def is_draft(self) -> bool:
        """Check if form is still a draft."""
        return self.status == "draft"

    @property
    def is_validated(self) -> bool:
        """Check if form has been validated."""
        return self.validation_status == "valid"

    @property
    def is_confirmed(self) -> bool:
        """Check if form has been confirmed by user."""
        return self.status in ("confirmed", "submitted", "paid")

    @property
    def is_submitted(self) -> bool:
        """Check if form has been submitted to SII."""
        return self.status in ("submitted", "paid")

    @property
    def is_paid(self) -> bool:
        """Check if payment has been completed."""
        return self.payment_status == "paid"

    @property
    def is_cancelled(self) -> bool:
        """Check if form has been cancelled."""
        return self.status == "cancelled"

    @property
    def can_be_edited(self) -> bool:
        """Check if form can still be edited."""
        return self.status in ("draft", "validated")

    @property
    def can_be_confirmed(self) -> bool:
        """Check if form is ready to be confirmed."""
        return self.status == "validated" and self.validation_status == "valid"

    @property
    def can_be_submitted(self) -> bool:
        """Check if form is ready to be submitted to SII."""
        return self.status == "confirmed"

    @property
    def has_validation_errors(self) -> bool:
        """Check if form has validation errors."""
        return (
            self.validation_status == "invalid"
            and self.validation_errors is not None
            and len(self.validation_errors) > 0
        )

    @property
    def is_linked_to_sii(self) -> bool:
        """Check if form is linked to an SII download."""
        return self.sii_download_id is not None

    @property
    def period_display(self) -> str:
        """Get period in display format (YYYY-MM)."""
        return f"{self.period_year}-{self.period_month:02d}"

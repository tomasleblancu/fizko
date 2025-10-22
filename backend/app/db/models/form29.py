"""Form 29 model for monthly IVA declarations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company


class Form29(Base):
    """Form 29 - Monthly IVA (VAT) declaration.

    Represents the Chilean F29 tax form for monthly VAT reporting. This form
    calculates the net IVA to pay or carry forward as credit based on sales
    and purchases for a given period.
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

    # Status
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'draft'::text")
    )  # draft, submitted
    submission_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    folio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
        # Unique constraint: one Form29 per company per period
        UniqueConstraint(
            "company_id", "period_year", "period_month",
            name="form29_company_period_unique"
        ),
        CheckConstraint(
            "period_month >= 1 AND period_month <= 12",
            name="form29_period_month_check",
        ),
        CheckConstraint(
            "status = ANY (ARRAY['draft'::text, 'submitted'::text])",
            name="form29_status_check",
        ),
        # Index for efficient period queries
        Index("ix_form29_company_period", "company_id", "period_year", "period_month"),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="form29_records")

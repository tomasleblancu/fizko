"""Form 29 SII downloads model - tracks F29 forms downloaded from SII."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, Date, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .form29 import Form29


class Form29SIIDownload(Base):
    """Form 29 SII Download - Tracks F29 forms downloaded from SII portal.

    This table stores F29 forms as they appear in the SII portal,
    separate from locally calculated F29 forms. This separation allows:
    - Tracking what forms exist in the SII
    - Managing PDF downloads independently
    - Reconciling SII data with local calculations
    - Maintaining audit trail of SII submissions
    """

    __tablename__ = "form29_sii_downloads"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id")
    )

    # Optional link to local F29 (for reconciliation)
    form29_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("form29.id"), nullable=True
    )

    # SII data (as returned from API)
    sii_folio: Mapped[str] = mapped_column(Text)  # Unique folio from SII
    sii_id_interno: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Internal SII ID (required for PDF download, but not always available)

    # Period
    period_year: Mapped[int] = mapped_column(Integer)
    period_month: Mapped[int] = mapped_column(Integer)
    period_display: Mapped[str] = mapped_column(Text)  # "YYYY-MM" format from SII

    # Form information
    contributor_rut: Mapped[str] = mapped_column(Text)
    submission_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(Text)  # Vigente, Rectificado, Anulado
    amount_cents: Mapped[int] = mapped_column(
        Integer, server_default=text("0")
    )  # Amount in pesos (no decimals)

    # PDF download tracking
    pdf_storage_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # URL to PDF in storage
    pdf_download_status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending'::text")
    )  # pending, downloaded, error
    pdf_download_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

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
        # Unique constraint: one download record per company per folio
        UniqueConstraint(
            "company_id", "sii_folio",
            name="form29_sii_downloads_company_folio_unique"
        ),
        # Check constraints
        CheckConstraint(
            "period_month >= 1 AND period_month <= 12",
            name="form29_sii_downloads_period_month_check",
        ),
        CheckConstraint(
            "status = ANY (ARRAY['Vigente'::text, 'Rectificado'::text, 'Anulado'::text])",
            name="form29_sii_downloads_status_check",
        ),
        CheckConstraint(
            "pdf_download_status = ANY (ARRAY['pending'::text, 'downloaded'::text, 'error'::text])",
            name="form29_sii_downloads_pdf_status_check",
        ),
        # Indexes
        Index(
            "ix_form29_sii_downloads_company_period",
            "company_id", "period_year", "period_month"
        ),
        Index("ix_form29_sii_downloads_folio", "sii_folio"),
        Index("ix_form29_sii_downloads_status", "company_id", "status"),
    )

    # Relationships
    company: Mapped["Company"] = relationship(
        "Company", back_populates="form29_sii_downloads"
    )

    # Legacy relationship: form29_id points to local Form29 for reconciliation
    form29: Mapped[Optional["Form29"]] = relationship(
        "Form29",
        foreign_keys=[form29_id],
        back_populates="sii_download_legacy",
        uselist=False
    )

    # New relationship: Form29 points back to this SII download via sii_download_id
    linked_form29: Mapped[Optional["Form29"]] = relationship(
        "Form29",
        foreign_keys="Form29.sii_download_id",
        back_populates="sii_download_link",
        uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<Form29SIIDownload("
            f"id={self.id}, "
            f"folio={self.sii_folio}, "
            f"period={self.period_display}, "
            f"status={self.status}"
            f")>"
        )

    @property
    def has_pdf(self) -> bool:
        """Check if PDF has been downloaded successfully."""
        return self.pdf_download_status == "downloaded" and self.pdf_storage_url is not None

    @property
    def can_download_pdf(self) -> bool:
        """Check if PDF can be downloaded (has internal SII ID)."""
        return self.sii_id_interno is not None

    @property
    def is_linked_to_local_form(self) -> bool:
        """Check if this download is linked to a local F29 form."""
        return self.form29_id is not None

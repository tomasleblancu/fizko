"""Expense model - Manual expense tracking for non-DTE documents."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint, Date, ForeignKey, Index, Integer,
    Numeric, Text, text, Boolean
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .contact import Contact
    from .user import User


class ExpenseCategory(str, Enum):
    """Expense categories for classification."""
    TRANSPORT = "transport"
    PARKING = "parking"
    MEALS = "meals"
    OFFICE_SUPPLIES = "office_supplies"
    UTILITIES = "utilities"
    REPRESENTATION = "representation"
    TRAVEL = "travel"
    PROFESSIONAL_SERVICES = "professional_services"
    MAINTENANCE = "maintenance"
    OTHER = "other"


class ExpenseStatus(str, Enum):
    """Expense approval workflow statuses."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_INFO = "requires_info"


class Expense(Base):
    """
    Manual expense tracking for non-electronic documents.

    This model is specifically designed for expenses that don't have
    a DTE (Documento Tributario Electrónico) from the SII:
    - Physical receipts (boletas físicas)
    - Taxi/transport receipts without folio
    - Parking tickets
    - Tips and minor expenses
    - Restaurant bills
    - Office supplies from small vendors
    - Any expense without electronic tax document

    Workflow:
    1. User creates expense (status: draft)
    2. Uploads receipt photo/PDF (optional)
    3. Submits for approval (status: pending_approval)
    4. Accountant reviews and approves/rejects
    5. Approved expenses are included in tax calculations
    """

    __tablename__ = "expenses"

    # ========================================================================
    # IDENTIFICATION
    # ========================================================================
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE")
    )

    created_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL")
    )

    # ========================================================================
    # EXPENSE CATEGORIZATION
    # ========================================================================
    expense_category: Mapped[str] = mapped_column(Text)
    # Categories: transport, parking, meals, office_supplies, utilities,
    # representation, travel, professional_services, maintenance, other

    expense_subcategory: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    # Subcategories for detailed tracking (free-form text)

    # ========================================================================
    # EXPENSE DETAILS
    # ========================================================================
    expense_date: Mapped[date] = mapped_column(Date)
    # Date when expense occurred

    description: Mapped[str] = mapped_column(Text)
    # User-friendly description

    vendor_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Name of vendor/provider

    vendor_rut: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # RUT if available

    receipt_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Receipt/ticket number if available

    # ========================================================================
    # FINANCIAL INFORMATION
    # ========================================================================
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # Total amount paid

    has_tax: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    # Does this expense include IVA (19%)?

    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), server_default=text("0")
    )
    # Calculated: total_amount / 1.19 if has_tax, else 0

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), server_default=text("0")
    )
    # Calculated: total_amount - net_amount if has_tax, else 0

    currency: Mapped[str] = mapped_column(
        Text, server_default=text("'CLP'::text")
    )
    # Currency code (CLP, USD, EUR)

    # ========================================================================
    # BUSINESS CONTEXT
    # ========================================================================
    is_business_expense: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true")
    )
    # Is this a legitimate business expense?

    is_reimbursable: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )
    # Should this be reimbursed to the user?

    reimbursed: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )
    # Has this expense been reimbursed?

    reimbursement_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    # Date when expense was reimbursed

    # ========================================================================
    # OPTIONAL ASSOCIATIONS
    # ========================================================================
    contact_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True
    )
    # Link to contact if expense is related to a client/supplier

    project_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Project or cost center code for accounting

    # ========================================================================
    # APPROVAL WORKFLOW
    # ========================================================================
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'draft'::text")
    )
    # Workflow states: draft, pending_approval, approved, rejected, requires_info

    approved_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True
    )

    approved_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    # Why was this expense rejected?

    # ========================================================================
    # DOCUMENT ATTACHMENTS
    # ========================================================================
    receipt_file_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    # URL to uploaded receipt photo/PDF

    receipt_file_name: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    # Original filename

    receipt_file_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    # File size in bytes

    receipt_mime_type: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    # MIME type: image/jpeg, image/png, application/pdf

    # ========================================================================
    # OCR / EXTRACTION DATA (Future)
    # ========================================================================
    ocr_extracted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )
    # Was data extracted via OCR?

    ocr_confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    # OCR confidence score (0-100)

    ocr_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )
    # Raw OCR extraction data for reference

    # ========================================================================
    # NOTES AND METADATA
    # ========================================================================
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Additional notes from user or accountant

    tags: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, server_default=text("'[]'::jsonb")
    )
    # Tags for organization: ["urgent", "recurring", "client-related"]

    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in database
        JSONB, nullable=True, server_default=text("'{}'::jsonb")
    )
    # Flexible metadata field

    # ========================================================================
    # TIMESTAMPS
    # ========================================================================
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("now()")
    )

    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    # When user submitted for approval

    # ========================================================================
    # CONSTRAINTS
    # ========================================================================
    __table_args__ = (
        # Valid expense categories
        CheckConstraint(
            "expense_category = ANY (ARRAY["
            "'transport'::text, 'parking'::text, 'meals'::text, "
            "'office_supplies'::text, 'utilities'::text, "
            "'representation'::text, 'travel'::text, "
            "'professional_services'::text, 'maintenance'::text, "
            "'other'::text])",
            name="expenses_category_check",
        ),
        # Valid statuses
        CheckConstraint(
            "status = ANY (ARRAY["
            "'draft'::text, 'pending_approval'::text, 'approved'::text, "
            "'rejected'::text, 'requires_info'::text])",
            name="expenses_status_check",
        ),
        # Valid currencies
        CheckConstraint(
            "currency = ANY (ARRAY['CLP'::text, 'USD'::text, 'EUR'::text])",
            name="expenses_currency_check",
        ),
        # Amount must be positive
        CheckConstraint(
            "total_amount > 0",
            name="expenses_total_amount_positive",
        ),
        # OCR confidence must be between 0 and 100
        CheckConstraint(
            "ocr_confidence IS NULL OR (ocr_confidence >= 0 AND ocr_confidence <= 100)",
            name="expenses_ocr_confidence_range",
        ),
        # Indexes for efficient queries
        Index("ix_expenses_company_id", "company_id"),
        Index("ix_expenses_created_by", "created_by_user_id"),
        Index("ix_expenses_expense_date", "expense_date"),
        Index("ix_expenses_status", "status"),
        Index("ix_expenses_category", "expense_category"),
        Index("ix_expenses_company_date", "company_id", "expense_date"),
        Index("ix_expenses_company_status", "company_id", "status"),
    )

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    company: Mapped["Company"] = relationship(
        "Company", back_populates="expenses"
    )

    created_by: Mapped["Profile"] = relationship(
        "Profile",
        foreign_keys=[created_by_user_id],
        back_populates="expenses_created"
    )

    approved_by: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        foreign_keys=[approved_by_user_id],
        back_populates="expenses_approved"
    )

    contact: Mapped[Optional["Contact"]] = relationship(
        "Contact", back_populates="expenses"
    )

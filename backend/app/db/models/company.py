"""Company and company tax info models."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Text, event, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from ...utils.rut import normalize_rut
from ...utils.encryption import encrypt_password, decrypt_password

if TYPE_CHECKING:
    from .calendar import CalendarEvent, CompanyEvent
    from .contact import Contact
    from .documents import PurchaseDocument, SalesDocument
    from .expenses import Expense
    from .form29 import Form29
    from .form29_sii_download import Form29SIIDownload
    from .personnel import Payroll, Person
    from .session import Session
    from .honorarios import HonorariosReceipt
    from .subscriptions import Subscription


class Company(Base):
    """Basic company information.

    Stores fundamental company data. Tax-specific information is stored in
    CompanyTaxInfo. Users access companies through Session records.
    """

    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Company identification
    rut: Mapped[str] = mapped_column(Text, unique=True)  # Chilean tax ID
    business_name: Mapped[str] = mapped_column(Text)
    trade_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # SII credentials (encrypted with Fernet using SUPABASE_JWT_SECRET)
    _sii_password_encrypted: Mapped[Optional[str]] = mapped_column(
        "sii_password", Text, nullable=True
    )

    # Contact information
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    # Relationships
    tax_info: Mapped[Optional["CompanyTaxInfo"]] = relationship(
        "CompanyTaxInfo", back_populates="company", uselist=False, cascade="all, delete-orphan"
    )
    settings: Mapped[Optional["CompanySettings"]] = relationship(
        "CompanySettings", back_populates="company", uselist=False, cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="company", cascade="all, delete-orphan"
    )
    purchase_documents: Mapped[list["PurchaseDocument"]] = relationship(
        "PurchaseDocument", back_populates="company", cascade="all, delete-orphan"
    )
    sales_documents: Mapped[list["SalesDocument"]] = relationship(
        "SalesDocument", back_populates="company", cascade="all, delete-orphan"
    )
    form29_records: Mapped[list["Form29"]] = relationship(
        "Form29", back_populates="company", cascade="all, delete-orphan"
    )
    form29_sii_downloads: Mapped[list["Form29SIIDownload"]] = relationship(
        "Form29SIIDownload", back_populates="company", cascade="all, delete-orphan"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="company", cascade="all, delete-orphan"
    )
    company_events: Mapped[list["CompanyEvent"]] = relationship(
        "CompanyEvent", back_populates="company", cascade="all, delete-orphan"
    )
    calendar_events: Mapped[list["CalendarEvent"]] = relationship(
        "CalendarEvent", back_populates="company"
    )

    # Personnel relationships
    people: Mapped[list["Person"]] = relationship(
        "Person", back_populates="company", cascade="all, delete-orphan"
    )
    payroll_records: Mapped[list["Payroll"]] = relationship(
        "Payroll", back_populates="company", cascade="all, delete-orphan"
    )

    # Brain (Memory) relationship
    brain_memories: Mapped[list["CompanyBrain"]] = relationship(
        "CompanyBrain", back_populates="company", cascade="all, delete-orphan"
    )

    # Honorarios relationships
    honorarios_receipts: Mapped[list["HonorariosReceipt"]] = relationship(
        "HonorariosReceipt", back_populates="company", cascade="all, delete-orphan"
    )

    # Expenses relationship
    expenses: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="company", cascade="all, delete-orphan"
    )

    # Feedback relationship
    feedback: Mapped[list["Feedback"]] = relationship(
        "Feedback", back_populates="company", cascade="all, delete-orphan"
    )

    # Subscription relationship (1:1)
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Helper methods for subscription access
    def has_active_subscription(self) -> bool:
        """Check if company has an active subscription."""
        return (
            self.subscription is not None and
            self.subscription.status in ['trialing', 'active']
        )

    def can_use_feature(self, feature_key: str) -> bool:
        """
        Check if subscription allows a specific feature.

        Args:
            feature_key: Feature to check (e.g., "has_whatsapp")

        Returns:
            bool: True if feature is available, False otherwise
        """
        if not self.subscription:
            return False
        return self.subscription.plan.features.get(feature_key, False)

    @hybrid_property
    def sii_password(self) -> Optional[str]:
        """
        Get the decrypted SII password.

        Returns:
            Decrypted password string, or None if not set
        """
        if self._sii_password_encrypted:
            return decrypt_password(self._sii_password_encrypted)
        return None

    @sii_password.setter
    def sii_password(self, value: Optional[str]) -> None:
        """
        Set the SII password (will be encrypted before storage).

        Args:
            value: Plaintext password to encrypt and store
        """
        if value:
            self._sii_password_encrypted = encrypt_password(value)
        else:
            self._sii_password_encrypted = None


class CompanyTaxInfo(Base):
    """Tax-specific information for companies.

    One-to-one relationship with Company. Stores all tax-related configuration
    and legal information required for Chilean tax operations.
    """

    __tablename__ = "company_tax_info"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id"), unique=True
    )

    # Tax configuration
    tax_regime: Mapped[str] = mapped_column(
        Text, server_default=text("'regimen_general'::text")
    )  # regimen_general, regimen_simplificado, pro_pyme, 14_ter
    sii_activity_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sii_activity_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Legal representative
    legal_representative_rut: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    legal_representative_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Business dates
    start_of_activities_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    accounting_start_month: Mapped[int] = mapped_column(
        Integer, server_default=text("1")
    )  # Fiscal year start month (1-12)

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
            "tax_regime = ANY (ARRAY['regimen_general'::text, 'regimen_simplificado'::text, "
            "'pro_pyme'::text, '14_ter'::text])",
            name="company_tax_info_tax_regime_check",
        ),
        CheckConstraint(
            "accounting_start_month >= 1 AND accounting_start_month <= 12",
            name="company_tax_info_accounting_start_month_check",
        ),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="tax_info")


class CompanySettings(Base):
    """General company business settings and configuration.

    Stores business operation settings that help customize the platform
    experience and provide relevant features to the company.
    """

    __tablename__ = "company_settings"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id"), unique=True
    )

    # Business operations settings
    has_formal_employees: Mapped[Optional[bool]] = mapped_column(nullable=True)
    has_imports: Mapped[Optional[bool]] = mapped_column(nullable=True)
    has_exports: Mapped[Optional[bool]] = mapped_column(nullable=True)
    has_lease_contracts: Mapped[Optional[bool]] = mapped_column(nullable=True)

    # Setup tracking
    is_initial_setup_complete: Mapped[bool] = mapped_column(default=False)
    initial_setup_completed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="settings")


# Event listeners for RUT normalization
@event.listens_for(Company, 'before_insert')
@event.listens_for(Company, 'before_update')
def normalize_company_rut(mapper, connection, target):
    """
    Normalize RUT before insert or update.

    This ensures all RUTs are stored in a consistent format:
    - No hyphens, dots, or spaces
    - Lowercase verification digit
    - Example: "77794858k" instead of "77.794.858-K"
    """
    if target.rut:
        target.rut = normalize_rut(target.rut)

"""Personnel and payroll management models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from ...utils.rut import normalize_rut

if TYPE_CHECKING:
    from .company import Company


class Person(Base):
    """Employee information.

    Stores basic employee data including personal info, contract details,
    and salary information for a company.
    """

    __tablename__ = "people"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE")
    )

    # Personal Information
    rut: Mapped[str] = mapped_column(String(20))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Position and Contract
    position_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contract_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Salary Information
    base_salary: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # AFP (Pension)
    afp_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    afp_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, server_default=text("10.49"))

    # Health Insurance
    health_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    health_plan: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    health_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    health_fixed_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    # Bank Information
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_account_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Employment Status
    status: Mapped[str] = mapped_column(String(20), server_default=text("'active'"))
    termination_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    termination_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional Data
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
            "status IN ('active', 'inactive', 'terminated')",
            name="people_status_check",
        ),
        CheckConstraint(
            "contract_type IS NULL OR contract_type IN ('indefinido', 'plazo_fijo', 'honorarios', 'por_obra', 'part_time')",
            name="people_contract_type_check",
        ),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="people")
    payroll_records: Mapped[list["Payroll"]] = relationship(
        "Payroll", back_populates="person", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get employee's full name."""
        return f"{self.first_name} {self.last_name}"


class Payroll(Base):
    """Payroll calculation record (Liquidación de Sueldo).

    Stores the complete payroll calculation for an employee for a specific
    period, including all income items (haberes) and deductions (descuentos).
    """

    __tablename__ = "payroll"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE")
    )
    person_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people.id", ondelete="CASCADE")
    )

    # Period Information
    period_month: Mapped[int] = mapped_column(Integer)
    period_year: Mapped[int] = mapped_column(Integer)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    worked_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default=text("30"))

    # Base Salary
    base_salary: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # HABERES IMPONIBLES (Taxable Income)
    # JSONB format: [{"name": "Gratificación", "amount": 209396}, ...]
    taxable_income_items: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, server_default=text("'[]'::jsonb")
    )
    total_taxable_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # HABERES NO IMPONIBLES (Non-taxable Income)
    # JSONB format: [{"name": "Colación", "amount": 300000}, ...]
    non_taxable_income_items: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, server_default=text("'[]'::jsonb")
    )
    total_non_taxable_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # TOTAL HABERES
    total_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # DESCUENTOS LEGALES (Legal Deductions)
    afp_deduction: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    health_deduction: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    unemployment_insurance: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    income_tax: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    total_legal_deductions: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # OTROS DESCUENTOS (Other Deductions)
    # JSONB format: [{"name": "Préstamo", "amount": 50000}, ...]
    other_deductions_items: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, server_default=text("'[]'::jsonb")
    )
    total_other_deductions: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # TOTAL DESCUENTOS
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # BASES IMPONIBLES (Taxable Bases)
    pension_base: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    unemployment_base: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    taxable_base: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # NET SALARY (LÍQUIDO A RECIBIR)
    net_salary: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))

    # Payment Information
    payment_method: Mapped[str] = mapped_column(String(50), server_default=text("'bank_transfer'"))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"))

    # Documents
    payslip_document_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), server_default=text("'draft'"))

    # Additional Data
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
            "payment_method IN ('bank_transfer', 'cash', 'check')",
            name="payroll_payment_method_check",
        ),
        CheckConstraint(
            "payment_status IN ('pending', 'paid', 'failed')",
            name="payroll_payment_status_check",
        ),
        CheckConstraint(
            "status IN ('draft', 'approved', 'paid', 'closed')",
            name="payroll_status_check",
        ),
        CheckConstraint(
            "period_month >= 1 AND period_month <= 12",
            name="payroll_month_check",
        ),
        CheckConstraint(
            "period_year >= 2020 AND period_year <= 2100",
            name="payroll_year_check",
        ),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="payroll_records")
    person: Mapped["Person"] = relationship("Person", back_populates="payroll_records")

    @property
    def period_name(self) -> str:
        """Get formatted period name (e.g., 'Agosto 2025')."""
        months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        return f"{months[self.period_month - 1]} {self.period_year}"


# Event listeners for RUT normalization
@event.listens_for(Person, 'before_insert')
@event.listens_for(Person, 'before_update')
def normalize_person_rut(mapper, connection, target):
    """Normalize person RUT before insert or update."""
    if target.rut:
        target.rut = normalize_rut(target.rut)

"""Pydantic schemas for personnel and payroll management."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# PERSON (Employee) SCHEMAS
# ============================================================================

class PersonBase(BaseModel):
    """Base person schema with common fields."""
    rut: str = Field(..., description="Chilean RUT (will be normalized)")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    birth_date: Optional[date] = None

    # Position and Contract
    position_title: Optional[str] = Field(None, max_length=100)
    contract_type: Optional[str] = Field(None, description="indefinido, plazo_fijo, honorarios, por_obra, part_time")
    hire_date: Optional[date] = None

    # Salary Information
    base_salary: Decimal = Field(default=Decimal("0"), ge=0)

    # AFP (Pension)
    afp_provider: Optional[str] = Field(None, max_length=100, description="AFP name (e.g., Provida, Habitat)")
    afp_percentage: Optional[Decimal] = Field(default=Decimal("10.49"), ge=0, le=100, description="AFP percentage (typically 10-13%)")

    # Health Insurance
    health_provider: Optional[str] = Field(None, max_length=100, description="Fonasa or Isapre name")
    health_plan: Optional[str] = Field(None, max_length=100)
    health_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="For Isapre percentage")
    health_fixed_amount: Optional[Decimal] = Field(None, ge=0, description="For Isapre UF amount")

    # Bank Information
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_type: Optional[str] = Field(None, description="cuenta corriente, cuenta vista, cuenta ahorro")
    bank_account_number: Optional[str] = Field(None, max_length=50)

    # Additional
    notes: Optional[str] = None
    photo_url: Optional[str] = None

    @field_validator('contract_type')
    @classmethod
    def validate_contract_type(cls, v):
        if v and v not in ['indefinido', 'plazo_fijo', 'honorarios', 'por_obra', 'part_time']:
            raise ValueError('Invalid contract type')
        return v


class PersonCreate(PersonBase):
    """Schema for creating a new person."""
    company_id: UUID


class PersonUpdate(BaseModel):
    """Schema for updating a person (all fields optional)."""
    rut: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    birth_date: Optional[date] = None
    position_title: Optional[str] = Field(None, max_length=100)
    contract_type: Optional[str] = None
    hire_date: Optional[date] = None
    base_salary: Optional[Decimal] = Field(None, ge=0)
    afp_provider: Optional[str] = Field(None, max_length=100)
    afp_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    health_provider: Optional[str] = Field(None, max_length=100)
    health_plan: Optional[str] = Field(None, max_length=100)
    health_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    health_fixed_amount: Optional[Decimal] = Field(None, ge=0)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_type: Optional[str] = None
    bank_account_number: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, description="active, inactive, terminated")
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None
    notes: Optional[str] = None
    photo_url: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v and v not in ['active', 'inactive', 'terminated']:
            raise ValueError('Invalid status')
        return v


class Person(PersonBase):
    """Schema for reading a person (returned from API)."""
    id: UUID
    company_id: UUID
    status: str
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PAYROLL SCHEMAS
# ============================================================================

class PayrollItemSchema(BaseModel):
    """Schema for individual payroll item (haber or descuento)."""
    name: str = Field(..., description="Item name (e.g., 'Gratificación', 'Bono Producción')")
    amount: Decimal = Field(..., ge=0, description="Amount in CLP")


class PayrollBase(BaseModel):
    """Base payroll schema."""
    period_month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    period_year: int = Field(..., ge=2020, le=2100, description="Year")
    payment_date: Optional[date] = None
    worked_days: Decimal = Field(default=Decimal("30"), ge=0, le=31)

    # Base Salary
    base_salary: Decimal = Field(default=Decimal("0"), ge=0)

    # HABERES IMPONIBLES (Taxable Income)
    taxable_income_items: list[PayrollItemSchema] = Field(default_factory=list, description="Items like Gratificación, Bono")

    # HABERES NO IMPONIBLES (Non-taxable Income)
    non_taxable_income_items: list[PayrollItemSchema] = Field(default_factory=list, description="Items like Colación, Movilización")

    # DESCUENTOS LEGALES (Legal Deductions)
    afp_deduction: Decimal = Field(default=Decimal("0"), ge=0, description="AFP deduction")
    health_deduction: Decimal = Field(default=Decimal("0"), ge=0, description="Health insurance deduction")
    unemployment_insurance: Decimal = Field(default=Decimal("0"), ge=0, description="Unemployment insurance")
    income_tax: Decimal = Field(default=Decimal("0"), ge=0, description="Income tax (Impuesto Único)")

    # OTROS DESCUENTOS (Other Deductions)
    other_deductions_items: list[PayrollItemSchema] = Field(default_factory=list, description="Items like loans, advances")

    # BASES IMPONIBLES (for reference)
    pension_base: Decimal = Field(default=Decimal("0"), ge=0, description="Base for pension/health calculations")
    unemployment_base: Decimal = Field(default=Decimal("0"), ge=0, description="Base for unemployment insurance")
    taxable_base: Decimal = Field(default=Decimal("0"), ge=0, description="Base for income tax")

    # Payment Information
    payment_method: str = Field(default="bank_transfer", description="bank_transfer, cash, check")
    payment_reference: Optional[str] = Field(None, max_length=100)

    # Documents
    payslip_document_url: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v):
        if v not in ['bank_transfer', 'cash', 'check']:
            raise ValueError('Invalid payment method')
        return v


class PayrollCreate(PayrollBase):
    """Schema for creating a new payroll record."""
    company_id: UUID
    person_id: UUID


class PayrollUpdate(BaseModel):
    """Schema for updating a payroll record (all fields optional)."""
    payment_date: Optional[date] = None
    worked_days: Optional[Decimal] = Field(None, ge=0, le=31)
    base_salary: Optional[Decimal] = Field(None, ge=0)
    taxable_income_items: Optional[list[PayrollItemSchema]] = None
    non_taxable_income_items: Optional[list[PayrollItemSchema]] = None
    afp_deduction: Optional[Decimal] = Field(None, ge=0)
    health_deduction: Optional[Decimal] = Field(None, ge=0)
    unemployment_insurance: Optional[Decimal] = Field(None, ge=0)
    income_tax: Optional[Decimal] = Field(None, ge=0)
    other_deductions_items: Optional[list[PayrollItemSchema]] = None
    pension_base: Optional[Decimal] = Field(None, ge=0)
    unemployment_base: Optional[Decimal] = Field(None, ge=0)
    taxable_base: Optional[Decimal] = Field(None, ge=0)
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = Field(None, max_length=100)
    payment_status: Optional[str] = Field(None, description="pending, paid, failed")
    payslip_document_url: Optional[str] = None
    status: Optional[str] = Field(None, description="draft, approved, paid, closed")
    notes: Optional[str] = None

    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v):
        if v and v not in ['bank_transfer', 'cash', 'check']:
            raise ValueError('Invalid payment method')
        return v

    @field_validator('payment_status')
    @classmethod
    def validate_payment_status(cls, v):
        if v and v not in ['pending', 'paid', 'failed']:
            raise ValueError('Invalid payment status')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v and v not in ['draft', 'approved', 'paid', 'closed']:
            raise ValueError('Invalid status')
        return v


class Payroll(PayrollBase):
    """Schema for reading a payroll record (returned from API)."""
    id: UUID
    company_id: UUID
    person_id: UUID

    # Calculated totals (auto-calculated by DB trigger)
    total_taxable_income: Decimal
    total_non_taxable_income: Decimal
    total_income: Decimal
    total_legal_deductions: Decimal
    total_other_deductions: Decimal
    total_deductions: Decimal
    net_salary: Decimal

    # Status
    payment_status: str
    status: str

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayrollWithPerson(Payroll):
    """Payroll record with person information included."""
    person: Person


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class PersonListResponse(BaseModel):
    """Response schema for listing people."""
    data: list[Person]
    total: int
    page: int = 1
    page_size: int = 50


class PayrollListResponse(BaseModel):
    """Response schema for listing payroll records."""
    data: list[Payroll]
    total: int
    page: int = 1
    page_size: int = 50


class PayrollSummary(BaseModel):
    """Summary schema for payroll statistics."""
    period_month: int
    period_year: int
    total_employees: int
    total_gross_salary: Decimal
    total_deductions: Decimal
    total_net_salary: Decimal

"""Pydantic schemas for expense management."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# CREATE SCHEMA
# ============================================================================
class ExpenseCreate(BaseModel):
    """Schema for creating a new expense."""

    company_id: str = Field(..., description="Company UUID")

    expense_category: str = Field(
        ...,
        description="Category: transport, parking, meals, office_supplies, etc."
    )

    expense_subcategory: Optional[str] = Field(
        None, description="Subcategory for detailed tracking"
    )

    expense_date: str = Field(..., description="Date of expense (YYYY-MM-DD)")

    description: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Description of expense"
    )

    vendor_name: Optional[str] = Field(None, description="Vendor name")

    vendor_rut: Optional[str] = Field(None, description="Vendor RUT")

    receipt_number: Optional[str] = Field(None, description="Receipt number")

    total_amount: Decimal = Field(..., gt=0, description="Total amount")

    has_tax: bool = Field(
        default=True,
        description="Does amount include IVA (19%)?"
    )

    currency: str = Field(default="CLP", description="Currency code")

    is_business_expense: bool = Field(
        default=True,
        description="Is this a business expense?"
    )

    is_reimbursable: bool = Field(
        default=False,
        description="Should be reimbursed to user?"
    )

    contact_id: Optional[str] = Field(
        None, description="Related contact UUID"
    )

    project_code: Optional[str] = Field(
        None, description="Project or cost center code"
    )

    notes: Optional[str] = Field(None, description="Additional notes")

    tags: Optional[list[str]] = Field(
        default=[], description="Tags for organization"
    )

    metadata: Optional[dict] = Field(
        default={}, description="Additional metadata"
    )

    @field_validator("expense_category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid_categories = [
            "transport", "parking", "meals", "office_supplies",
            "utilities", "representation", "travel",
            "professional_services", "maintenance", "other"
        ]
        if v not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        valid_currencies = ["CLP", "USD", "EUR"]
        if v not in valid_currencies:
            raise ValueError(f"Invalid currency. Must be one of: {valid_currencies}")
        return v


# ============================================================================
# UPDATE SCHEMA
# ============================================================================
class ExpenseUpdate(BaseModel):
    """Schema for updating an expense (all fields optional)."""

    expense_category: Optional[str] = None
    expense_subcategory: Optional[str] = None
    expense_date: Optional[str] = None
    description: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_rut: Optional[str] = None
    receipt_number: Optional[str] = None
    total_amount: Optional[Decimal] = None
    has_tax: Optional[bool] = None
    currency: Optional[str] = None
    is_business_expense: Optional[bool] = None
    is_reimbursable: Optional[bool] = None
    contact_id: Optional[str] = None
    project_code: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict] = None


# ============================================================================
# APPROVAL SCHEMAS
# ============================================================================
class ExpenseApproval(BaseModel):
    """Schema for approving/rejecting an expense."""

    status: str = Field(..., description="approved or rejected")
    rejection_reason: Optional[str] = Field(
        None, description="Reason if rejected"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["approved", "rejected"]:
            raise ValueError("Status must be 'approved' or 'rejected'")
        return v


class ExpenseSubmit(BaseModel):
    """Schema for submitting expense for approval."""
    pass  # No additional fields needed


class ExpenseReimbursement(BaseModel):
    """Schema for marking expense as reimbursed."""

    reimbursed: bool = Field(..., description="Mark as reimbursed")
    reimbursement_date: Optional[str] = Field(
        None, description="Date of reimbursement (YYYY-MM-DD)"
    )


# ============================================================================
# RESPONSE SCHEMA
# ============================================================================
class Expense(BaseModel):
    """Schema for reading an expense."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    created_by_user_id: UUID

    expense_category: str
    expense_subcategory: Optional[str]
    expense_date: date
    description: str
    vendor_name: Optional[str]
    vendor_rut: Optional[str]
    receipt_number: Optional[str]

    total_amount: Decimal
    has_tax: bool
    net_amount: Decimal
    tax_amount: Decimal
    currency: str

    is_business_expense: bool
    is_reimbursable: bool
    reimbursed: bool
    reimbursement_date: Optional[date]

    contact_id: Optional[UUID]
    project_code: Optional[str]

    status: str
    approved_by_user_id: Optional[UUID]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]

    receipt_file_url: Optional[str]
    receipt_file_name: Optional[str]
    receipt_file_size: Optional[int]
    receipt_mime_type: Optional[str]

    ocr_extracted: bool
    ocr_confidence: Optional[Decimal]

    notes: Optional[str]
    tags: list[str]
    metadata: dict

    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]


# ============================================================================
# LIST RESPONSE
# ============================================================================
class ExpenseListResponse(BaseModel):
    """Response schema for listing expenses."""

    data: list[Expense]
    total: int
    page: int = 1
    page_size: int = 50

    # Summary statistics
    total_amount_sum: Optional[Decimal] = None
    approved_amount_sum: Optional[Decimal] = None
    pending_amount_sum: Optional[Decimal] = None


# ============================================================================
# SUMMARY SCHEMA
# ============================================================================
class ExpenseSummary(BaseModel):
    """Summary statistics for expenses."""

    period_start: date
    period_end: date

    total_expenses: int
    total_amount: Decimal
    total_tax: Decimal

    by_category: dict[str, dict]
    by_status: dict[str, dict]

    pending_approval_count: int
    pending_approval_amount: Decimal

    approved_count: int
    approved_amount: Decimal

    reimbursable_count: int
    reimbursable_amount: Decimal
    reimbursed_amount: Decimal

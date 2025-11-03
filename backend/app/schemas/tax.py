"""Pydantic schemas for tax document management."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# TAX DOCUMENT SCHEMAS (General)
# ============================================================================

class TaxDocument(BaseModel):
    """Tax document response model (unified view of purchase/sales documents)."""
    id: str
    company_id: str
    document_type: str
    document_number: str
    issue_date: str
    amount: float
    tax_amount: Optional[float] = None
    status: str
    description: Optional[str] = None
    created_at: str


# ============================================================================
# PURCHASE DOCUMENT SCHEMAS
# ============================================================================

class PurchaseDocumentCreate(BaseModel):
    """Schema for creating a purchase document."""
    company_id: str = Field(..., description="Company UUID string")
    document_type: str = Field(..., description="factura_compra, nota_credito_compra, nota_debito_compra")
    folio: Optional[int] = Field(None, description="Document folio number")
    issue_date: str = Field(..., description="ISO date string")
    sender_rut: Optional[str] = Field(None, description="Sender RUT")
    sender_name: Optional[str] = Field(None, description="Sender name")
    net_amount: Decimal = Field(..., description="Net amount (without tax)")
    tax_amount: Decimal = Field(default=Decimal("0"), description="Tax amount")
    exempt_amount: Decimal = Field(default=Decimal("0"), description="Exempt amount")
    total_amount: Decimal = Field(..., description="Total amount")
    status: str = Field(default="pending", description="Document status")
    dte_xml: Optional[str] = Field(None, description="DTE XML content")
    sii_track_id: Optional[str] = Field(None, description="SII tracking ID")
    file_url: Optional[str] = Field(None, description="Document file URL")
    extra_data: Optional[dict] = Field(None, description="Additional data")


class PurchaseDocumentUpdate(BaseModel):
    """Schema for updating a purchase document (all fields optional)."""
    document_type: Optional[str] = Field(None, description="Document type")
    folio: Optional[int] = Field(None, description="Document folio")
    issue_date: Optional[str] = Field(None, description="ISO date string")
    sender_rut: Optional[str] = Field(None, description="Sender RUT")
    sender_name: Optional[str] = Field(None, description="Sender name")
    net_amount: Optional[Decimal] = Field(None, description="Net amount")
    tax_amount: Optional[Decimal] = Field(None, description="Tax amount")
    exempt_amount: Optional[Decimal] = Field(None, description="Exempt amount")
    total_amount: Optional[Decimal] = Field(None, description="Total amount")
    status: Optional[str] = Field(None, description="Document status")
    dte_xml: Optional[str] = Field(None, description="DTE XML content")
    sii_track_id: Optional[str] = Field(None, description="SII tracking ID")
    file_url: Optional[str] = Field(None, description="Document file URL")
    extra_data: Optional[dict] = Field(None, description="Additional data")


class PurchaseDocument(BaseModel):
    """Schema for reading a purchase document."""
    id: UUID
    company_id: UUID
    document_type: str
    folio: Optional[int] = None
    issue_date: date
    sender_rut: Optional[str] = None
    sender_name: Optional[str] = None
    net_amount: Decimal
    tax_amount: Decimal
    exempt_amount: Decimal
    total_amount: Decimal
    status: str
    dte_xml: Optional[str] = None
    sii_track_id: Optional[str] = None
    file_url: Optional[str] = None
    extra_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SALES DOCUMENT SCHEMAS
# ============================================================================

class SalesDocumentCreate(BaseModel):
    """Schema for creating a sales document."""
    company_id: str = Field(..., description="Company UUID string")
    document_type: str = Field(..., description="factura_venta, boleta, nota_credito_venta, nota_debito_venta, factura_exenta")
    folio: Optional[int] = Field(None, description="Document folio number")
    issue_date: str = Field(..., description="ISO date string")
    recipient_rut: Optional[str] = Field(None, description="Recipient RUT")
    recipient_name: Optional[str] = Field(None, description="Recipient name")
    net_amount: Decimal = Field(..., description="Net amount (without tax)")
    tax_amount: Decimal = Field(default=Decimal("0"), description="Tax amount")
    exempt_amount: Decimal = Field(default=Decimal("0"), description="Exempt amount")
    total_amount: Decimal = Field(..., description="Total amount")
    status: str = Field(default="pending", description="Document status")
    dte_xml: Optional[str] = Field(None, description="DTE XML content")
    sii_track_id: Optional[str] = Field(None, description="SII tracking ID")
    file_url: Optional[str] = Field(None, description="Document file URL")
    extra_data: Optional[dict] = Field(None, description="Additional data")


class SalesDocumentUpdate(BaseModel):
    """Schema for updating a sales document (all fields optional)."""
    document_type: Optional[str] = Field(None, description="Document type")
    folio: Optional[int] = Field(None, description="Document folio")
    issue_date: Optional[str] = Field(None, description="ISO date string")
    recipient_rut: Optional[str] = Field(None, description="Recipient RUT")
    recipient_name: Optional[str] = Field(None, description="Recipient name")
    net_amount: Optional[Decimal] = Field(None, description="Net amount")
    tax_amount: Optional[Decimal] = Field(None, description="Tax amount")
    exempt_amount: Optional[Decimal] = Field(None, description="Exempt amount")
    total_amount: Optional[Decimal] = Field(None, description="Total amount")
    status: Optional[str] = Field(None, description="Document status")
    dte_xml: Optional[str] = Field(None, description="DTE XML content")
    sii_track_id: Optional[str] = Field(None, description="SII tracking ID")
    file_url: Optional[str] = Field(None, description="Document file URL")
    extra_data: Optional[dict] = Field(None, description="Additional data")


class SalesDocument(BaseModel):
    """Schema for reading a sales document."""
    id: UUID
    company_id: UUID
    document_type: str
    folio: Optional[int] = None
    issue_date: date
    recipient_rut: Optional[str] = None
    recipient_name: Optional[str] = None
    net_amount: Decimal
    tax_amount: Decimal
    exempt_amount: Decimal
    total_amount: Decimal
    status: str
    dte_xml: Optional[str] = None
    sii_track_id: Optional[str] = None
    file_url: Optional[str] = None
    extra_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# FORM 29 SCHEMAS (Monthly IVA Declaration)
# ============================================================================

class Form29Create(BaseModel):
    """Schema for creating a Form 29."""
    company_id: str = Field(..., description="Company UUID string")
    period_year: int = Field(..., ge=2000, le=2100, description="Year")
    period_month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    total_sales: Decimal = Field(default=Decimal("0"), description="Total sales")
    taxable_sales: Decimal = Field(default=Decimal("0"), description="Taxable sales")
    exempt_sales: Decimal = Field(default=Decimal("0"), description="Exempt sales")
    sales_tax: Decimal = Field(default=Decimal("0"), description="Sales tax (IVA)")
    total_purchases: Decimal = Field(default=Decimal("0"), description="Total purchases")
    taxable_purchases: Decimal = Field(default=Decimal("0"), description="Taxable purchases")
    purchases_tax: Decimal = Field(default=Decimal("0"), description="Purchases tax credit")
    iva_to_pay: Decimal = Field(default=Decimal("0"), description="IVA to pay")
    iva_credit: Decimal = Field(default=Decimal("0"), description="IVA credit")
    net_iva: Decimal = Field(default=Decimal("0"), description="Net IVA (to pay or credit)")
    status: str = Field(default="draft", description="Form status (draft, submitted, paid)")
    extra_data: Optional[dict] = Field(None, description="Additional data")


class Form29Update(BaseModel):
    """Schema for updating a Form 29 (all fields optional)."""
    total_sales: Optional[Decimal] = Field(None, description="Total sales")
    taxable_sales: Optional[Decimal] = Field(None, description="Taxable sales")
    exempt_sales: Optional[Decimal] = Field(None, description="Exempt sales")
    sales_tax: Optional[Decimal] = Field(None, description="Sales tax")
    total_purchases: Optional[Decimal] = Field(None, description="Total purchases")
    taxable_purchases: Optional[Decimal] = Field(None, description="Taxable purchases")
    purchases_tax: Optional[Decimal] = Field(None, description="Purchases tax credit")
    iva_to_pay: Optional[Decimal] = Field(None, description="IVA to pay")
    iva_credit: Optional[Decimal] = Field(None, description="IVA credit")
    net_iva: Optional[Decimal] = Field(None, description="Net IVA")
    status: Optional[str] = Field(None, description="Form status")
    extra_data: Optional[dict] = Field(None, description="Additional data")


class Form29Submit(BaseModel):
    """Schema for submitting a Form 29 to SII."""
    folio: Optional[str] = Field(None, description="SII folio number")


class Form29(BaseModel):
    """Schema for reading a Form 29."""
    id: UUID
    company_id: UUID
    period_year: int
    period_month: int
    total_sales: Decimal
    taxable_sales: Decimal
    exempt_sales: Decimal
    sales_tax: Decimal
    total_purchases: Decimal
    taxable_purchases: Decimal
    purchases_tax: Decimal
    iva_to_pay: Decimal
    iva_credit: Decimal
    net_iva: Decimal
    status: str
    extra_data: Optional[dict] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TAX SUMMARY SCHEMAS
# ============================================================================

class TaxSummary(BaseModel):
    """Schema for tax summary information."""
    id: str = Field(..., description="Summary ID (company-year-month)")
    company_id: str = Field(..., description="Company UUID string")
    period_start: str = Field(..., description="Period start date (ISO format)")
    period_end: str = Field(..., description="Period end date (ISO format)")
    total_revenue: float = Field(..., description="Total revenue (sales)")
    total_expenses: float = Field(..., description="Total expenses (purchases)")
    iva_collected: float = Field(..., description="IVA collected from sales")
    iva_paid: float = Field(..., description="IVA paid on purchases")
    net_iva: float = Field(..., description="Net IVA position")
    income_tax: float = Field(..., description="Income tax amount")
    previous_month_credit: Optional[float] = Field(None, description="Credit from previous month")
    ppm: Optional[float] = Field(None, description="PPM (Pago Provisional Mensual) - monthly provisional payment")
    retencion: Optional[float] = Field(None, description="Retención (honorarios) - withholding from invoices")
    impuesto_trabajadores: Optional[float] = Field(None, description="Impuesto trabajadores - employee tax withholding")
    monthly_tax: float = Field(..., description="Monthly tax to pay")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Update timestamp")


class TaxSummaryResponse(BaseModel):
    """Response schema for tax summary."""
    current_period: TaxSummary
    previous_period: Optional[TaxSummary] = None
    year_to_date: Optional[dict] = None


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class PurchaseDocumentListResponse(BaseModel):
    """Response schema for listing purchase documents."""
    data: list[PurchaseDocument]
    total: int
    page: int = 1
    page_size: int = 50


class SalesDocumentListResponse(BaseModel):
    """Response schema for listing sales documents."""
    data: list[SalesDocument]
    total: int
    page: int = 1
    page_size: int = 50


class Form29ListResponse(BaseModel):
    """Response schema for listing Form 29 records."""
    data: list[Form29]
    total: int
    page: int = 1
    page_size: int = 50

"""Tax document models for purchases and sales."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, Numeric, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .contact import Contact


class PurchaseDocument(Base):
    """Purchase documents (documentos de compra - facturas recibidas).

    Represents all incoming tax documents that the company receives from suppliers.
    Includes invoices, credit notes, and debit notes received.
    """

    __tablename__ = "purchase_documents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id")
    )

    # Document identification
    document_type: Mapped[str] = mapped_column(Text)  # factura_compra, factura_exenta_compra, nota_credito_compra, nota_debito_compra, liquidacion_factura
    folio: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    issue_date: Mapped[date] = mapped_column(Date)

    # Sender information (supplier)
    sender_rut: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sender_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contact reference (optional)
    contact_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )

    # Financial information
    net_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    exempt_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))

    # Status
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending'::text")
    )  # pending, approved, rejected, cancelled

    # Accounting state (SII registro contable)
    accounting_state: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # PENDIENTE, REGISTRO - tracks SII estadoContab field
    accounting_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )  # Date when accounting_state changed from PENDIENTE to REGISTRO

    # SII integration
    dte_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sii_track_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Storage
    file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
            "document_type = ANY (ARRAY['factura_compra'::text, 'factura_exenta_compra'::text, "
            "'nota_credito_compra'::text, 'nota_debito_compra'::text, 'liquidacion_factura'::text])",
            name="purchase_documents_document_type_check",
        ),
        CheckConstraint(
            "status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text, "
            "'cancelled'::text])",
            name="purchase_documents_status_check",
        ),
        CheckConstraint("total_amount >= 0", name="purchase_documents_total_amount_check"),
        # Indexes for efficient queries
        Index("ix_purchase_documents_company_type", "company_id", "document_type"),
        Index("ix_purchase_documents_company_date", "company_id", "issue_date"),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="purchase_documents")
    contact: Mapped[Optional["Contact"]] = relationship(
        "Contact", back_populates="purchase_documents"
    )


class SalesDocument(Base):
    """Sales documents (documentos de venta - facturas emitidas).

    Represents all outgoing tax documents that the company issues to clients.
    Includes invoices, receipts, exempt invoices, credit notes, and debit notes issued.
    """

    __tablename__ = "sales_documents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id")
    )

    # Document identification
    document_type: Mapped[str] = mapped_column(
        Text
    )  # factura_venta, boleta, boleta_exenta, nota_credito_venta, nota_debito_venta, factura_exenta, comprobante_pago, liquidacion_factura
    folio: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    issue_date: Mapped[date] = mapped_column(Date)

    # Recipient information (client)
    recipient_rut: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recipient_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contact reference (optional)
    contact_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )

    # Financial information
    net_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    exempt_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), server_default=text("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))

    # Status
    status: Mapped[str] = mapped_column(
        Text, server_default=text("'pending'::text")
    )  # pending, approved, rejected, cancelled

    # SII integration
    dte_xml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sii_track_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Storage
    file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
            "document_type = ANY (ARRAY['factura_venta'::text, 'boleta'::text, 'boleta_exenta'::text, "
            "'nota_credito_venta'::text, 'nota_debito_venta'::text, 'factura_exenta'::text, "
            "'comprobante_pago'::text, 'liquidacion_factura'::text])",
            name="sales_documents_document_type_check",
        ),
        CheckConstraint(
            "status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text, "
            "'cancelled'::text])",
            name="sales_documents_status_check",
        ),
        CheckConstraint("total_amount >= 0", name="sales_documents_total_amount_check"),
        # Indexes for efficient queries
        Index("ix_sales_documents_company_type", "company_id", "document_type"),
        Index("ix_sales_documents_company_date", "company_id", "issue_date"),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="sales_documents")
    contact: Mapped[Optional["Contact"]] = relationship(
        "Contact", back_populates="sales_documents"
    )

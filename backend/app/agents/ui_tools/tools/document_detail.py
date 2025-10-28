"""UI Tool for Document Detail component."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.models import Company, Contact, SalesDocument, PurchaseDocument
from ...tools.widgets.widgets import create_document_detail_widget, document_detail_widget_copy_text
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class DocumentDetailTool(BaseUITool):
    """
    UI Tool for Document Detail component.

    When a user clicks on a specific document (invoice, bill, etc.),
    this tool pre-loads:
    - Full document details (amounts, dates, status)
    - Contact information (issuer/receiver)
    - Related documents (credit notes, debit notes)
    - Payment status and history

    Requires additional_data with:
    - entity_id: Document UUID
    - entity_type: "sales_document" or "purchase_document"

    This allows the agent to provide detailed document analysis
    without needing to query the database.
    """

    @property
    def component_name(self) -> str:
        return "document_detail"

    @property
    def description(self) -> str:
        return "Loads detailed information when user clicks on a specific document"

    @property
    def domain(self) -> str:
        return "documents"

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process document detail interaction and load relevant data."""

        if not context.db:
            return UIToolResult(
                success=False,
                context_text="",
                error="Database session not available",
            )

        if not context.company_id:
            return UIToolResult(
                success=False,
                context_text="",
                error="Company ID not available in context",
            )

        if not context.additional_data or "entity_id" not in context.additional_data:
            return UIToolResult(
                success=False,
                context_text="",
                error="Document ID (entity_id) not provided in additional_data",
            )

        try:
            entity_id = context.additional_data["entity_id"]
            entity_type = context.additional_data.get("entity_type", "sales_document")

            # Get company info
            company_data = await self._get_company_info(context.db, context.company_id)
            if not company_data:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se encontró información de la empresa",
                )

            # Get document details based on type
            if entity_type == "sales_document":
                document_data = await self._get_sales_document_details(
                    context.db, entity_id, context.company_id
                )
            elif entity_type == "purchase_document":
                document_data = await self._get_purchase_document_details(
                    context.db, entity_id, context.company_id
                )
            else:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error=f"Tipo de documento no soportado: {entity_type}",
                )

            if not document_data:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se encontró el documento solicitado",
                )

            # Combine data
            full_data = {
                **company_data,
                "document": document_data,
                "document_type": entity_type,
            }

            # Format context text
            context_text = self._format_document_context(full_data)

            # Create widget to stream immediately
            widget = None
            widget_copy_text = None

            # Get document type name and contact info for widget
            doc = document_data
            is_sales = entity_type == "sales_document"
            doc_type_names = {
                # Sales documents
                "factura_venta": "Factura de Venta",
                "factura_exenta": "Factura Exenta de Venta",
                "boleta": "Boleta",
                "boleta_exenta": "Boleta Exenta",
                "nota_credito_venta": "Nota de Crédito (Venta)",
                "nota_debito_venta": "Nota de Débito (Venta)",
                "comprobante_pago": "Comprobante de Pago",
                "liquidacion_factura": "Liquidación Factura",
                # Purchase documents
                "factura_compra": "Factura de Compra",
                "factura_exenta_compra": "Factura Exenta de Compra",
                "nota_credito_compra": "Nota de Crédito (Compra)",
                "nota_debito_compra": "Nota de Débito (Compra)",
            }
            doc_type_name = doc_type_names.get(doc["document_type"], doc["document_type"].replace("_", " ").title())
            contact_label = "Cliente" if is_sales else "Proveedor"

            # Get contact info
            contact_name = None
            contact_rut = None
            if doc.get("contact"):
                contact_name = doc["contact"].get("business_name")
                contact_rut = doc["contact"].get("rut")
            elif is_sales:
                contact_name = doc.get("recipient_name")
                contact_rut = doc.get("recipient_rut")
            else:
                contact_name = doc.get("sender_name")
                contact_rut = doc.get("sender_rut")

            widget = create_document_detail_widget(
                document_type_name=doc_type_name,
                folio=doc["folio"],
                issue_date=doc["issue_date"],
                status=doc.get("status", "N/A"),
                net_amount=doc["net_amount"],
                tax_amount=doc["tax_amount"],
                total_amount=doc["total_amount"],
                contact_name=contact_name,
                contact_rut=contact_rut,
                contact_label=contact_label,
                sii_track_id=doc.get("sii_track_id"),
                is_sales=is_sales,
            )

            widget_copy_text = document_detail_widget_copy_text(
                document_type_name=doc_type_name,
                folio=doc["folio"],
                issue_date=doc["issue_date"],
                status=doc.get("status", "N/A"),
                net_amount=doc["net_amount"],
                tax_amount=doc["tax_amount"],
                total_amount=doc["total_amount"],
                contact_name=contact_name,
                contact_rut=contact_rut,
                contact_label=contact_label,
                sii_track_id=doc.get("sii_track_id"),
            )

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=full_data,
                metadata={
                    "document_id": entity_id,
                    "document_type": entity_type,
                    "total_amount": document_data["total_amount"],
                },
                widget=widget,
                widget_copy_text=widget_copy_text,
            )

        except Exception as e:
            self.logger.error(f"Error processing document detail: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar detalles del documento: {str(e)}",
            )

    async def _get_company_info(
        self,
        db: AsyncSession,
        company_id: str,
    ) -> dict[str, Any] | None:
        """Fetch company basic info."""
        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return None

        stmt = select(Company).where(Company.id == company_uuid)
        result = await db.execute(stmt)
        company = result.scalar_one_or_none()

        if not company:
            return None

        return {
            "rut": company.rut,
            "business_name": company.business_name,
        }

    async def _get_sales_document_details(
        self,
        db: AsyncSession,
        document_id: str,
        company_id: str,
    ) -> dict[str, Any] | None:
        """Get detailed information about a sales document."""

        document_uuid = self._safe_get_uuid(document_id)
        company_uuid = self._safe_get_uuid(company_id)
        if not document_uuid or not company_uuid:
            return None

        # Get document with contact info
        stmt = (
            select(SalesDocument, Contact)
            .outerjoin(Contact, SalesDocument.contact_id == Contact.id)
            .where(
                SalesDocument.id == document_uuid,
                SalesDocument.company_id == company_uuid,
            )
        )

        result = await db.execute(stmt)
        row = result.first()

        if not row:
            return None

        document, contact = row

        return {
            "id": str(document.id),
            "folio": document.folio,
            "document_type": document.document_type,
            "issue_date": document.issue_date.isoformat() if document.issue_date else None,
            "net_amount": float(document.net_amount) if document.net_amount else 0.0,
            "tax_amount": float(document.tax_amount) if document.tax_amount else 0.0,
            "total_amount": float(document.total_amount) if document.total_amount else 0.0,
            "status": document.status,
            "sii_track_id": document.sii_track_id,
            "recipient_rut": document.recipient_rut,
            "recipient_name": document.recipient_name,
            "contact": {
                "rut": contact.rut if contact else None,
                "business_name": contact.business_name if contact else None,
            } if contact else None,
        }

    async def _get_purchase_document_details(
        self,
        db: AsyncSession,
        document_id: str,
        company_id: str,
    ) -> dict[str, Any] | None:
        """Get detailed information about a purchase document."""

        document_uuid = self._safe_get_uuid(document_id)
        company_uuid = self._safe_get_uuid(company_id)
        if not document_uuid or not company_uuid:
            return None

        # Get document with contact info
        stmt = (
            select(PurchaseDocument, Contact)
            .outerjoin(Contact, PurchaseDocument.contact_id == Contact.id)
            .where(
                PurchaseDocument.id == document_uuid,
                PurchaseDocument.company_id == company_uuid,
            )
        )

        result = await db.execute(stmt)
        row = result.first()

        if not row:
            return None

        document, contact = row

        return {
            "id": str(document.id),
            "folio": document.folio,
            "document_type": document.document_type,
            "issue_date": document.issue_date.isoformat() if document.issue_date else None,
            "net_amount": float(document.net_amount) if document.net_amount else 0.0,
            "tax_amount": float(document.tax_amount) if document.tax_amount else 0.0,
            "total_amount": float(document.total_amount) if document.total_amount else 0.0,
            "status": document.status,
            "sii_track_id": document.sii_track_id,
            "sender_rut": document.sender_rut,
            "sender_name": document.sender_name,
            "contact": {
                "rut": contact.rut if contact else None,
                "business_name": contact.business_name if contact else None,
            } if contact else None,
        }

    def _format_document_context(self, data: dict[str, Any]) -> str:
        """Format document data into human-readable context for agent."""

        doc = data["document"]
        doc_type = data["document_type"]
        is_sales = doc_type == "sales_document"

        # Map document type strings to Spanish names
        doc_type_names = {
            # Sales documents
            "factura_venta": "Factura de Venta",
            "factura_exenta": "Factura Exenta de Venta",
            "boleta": "Boleta",
            "boleta_exenta": "Boleta Exenta",
            "nota_credito_venta": "Nota de Crédito (Venta)",
            "nota_debito_venta": "Nota de Débito (Venta)",
            "comprobante_pago": "Comprobante de Pago",
            "liquidacion_factura": "Liquidación Factura",
            # Purchase documents
            "factura_compra": "Factura de Compra",
            "factura_exenta_compra": "Factura Exenta de Compra",
            "nota_credito_compra": "Nota de Crédito (Compra)",
            "nota_debito_compra": "Nota de Débito (Compra)",
        }

        doc_type_name = doc_type_names.get(doc["document_type"], doc["document_type"].replace("_", " ").title())

        lines = [
            "## 📄 CONTEXTO: Detalle de Documento",
            "",
            f"**{data['business_name']}** (RUT: {data['rut']})",
            "",
            "### 📋 Información del Documento",
            f"- **Tipo:** {doc_type_name}",
            f"- **Folio:** {doc['folio']}",
            f"- **Fecha Emisión:** {doc['issue_date']}",
            f"- **Estado:** {doc.get('status', 'N/A')}",
        ]

        # Add SII track ID if available
        if doc.get("sii_track_id"):
            lines.append(f"- **Track ID SII:** {doc['sii_track_id']}")

        lines.extend([
            "",
            "### 💰 Montos",
            f"- **Neto:** ${doc['net_amount']:,.0f}",
            f"- **IVA:** ${doc['tax_amount']:,.0f}",
            f"- **Total:** ${doc['total_amount']:,.0f}",
            "",
        ])

        # Contact information (from contact or recipient/sender fields)
        contact_label = "Cliente" if is_sales else "Proveedor"

        if doc.get("contact"):
            # Use contact relationship
            contact = doc["contact"]
            lines.extend([
                f"### 👤 {contact_label}",
                f"- **Razón Social:** {contact['business_name']}",
                f"- **RUT:** {contact['rut']}",
                "",
            ])
        elif is_sales and (doc.get("recipient_name") or doc.get("recipient_rut")):
            # Use recipient fields for sales documents
            lines.extend([
                f"### 👤 {contact_label}",
                f"- **Razón Social:** {doc.get('recipient_name', 'N/A')}",
                f"- **RUT:** {doc.get('recipient_rut', 'N/A')}",
                "",
            ])
        elif not is_sales and (doc.get("sender_name") or doc.get("sender_rut")):
            # Use sender fields for purchase documents
            lines.extend([
                f"### 👤 {contact_label}",
                f"- **Razón Social:** {doc.get('sender_name', 'N/A')}",
                f"- **RUT:** {doc.get('sender_rut', 'N/A')}",
                "",
            ])

        # Contact info for widget
        contact_name = None
        contact_rut = None
        if doc.get("contact"):
            contact_name = doc["contact"].get("business_name")
            contact_rut = doc["contact"].get("rut")
        elif is_sales:
            contact_name = doc.get("recipient_name")
            contact_rut = doc.get("recipient_rut")
        else:
            contact_name = doc.get("sender_name")
            contact_rut = doc.get("sender_rut")

        lines.extend([
            "",
            "---",
            "",
            "💡 **INSTRUCCIONES PARA EL AGENTE:**",
            "- Ya se mostró el widget con los detalles del documento arriba",
            "- Responde en máximo 2 líneas con un resumen breve del documento",
            "- NO repitas la información que ya está en el widget",
            "- Termina preguntando si necesita más información sobre el documento",
            "- **NO llames a herramientas adicionales**",
            "",
        ])

        return "\n".join(lines)

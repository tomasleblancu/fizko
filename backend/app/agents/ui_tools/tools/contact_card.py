"""UI Tool for Contact Card component."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.models import Contact, PurchaseDocument, SalesDocument
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class ContactCardTool(BaseUITool):
    """
    UI Tool for Contact Card component.

    When a user clicks or interacts with a contact card in the frontend,
    this tool pre-loads:
    - Contact basic information
    - Recent transaction summary (sales/purchases)
    - Total amounts transacted
    - Contact type (provider, client, both)

    This gives the agent immediate context about the contact without
    needing to call additional tools.
    """

    @property
    def component_name(self) -> str:
        return "contact_card"

    @property
    def description(self) -> str:
        return "Loads contact information and transaction history when user views a contact card"

    @property
    def domain(self) -> str:
        return "contacts"

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process contact card interaction and load relevant data."""

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

        try:
            # Extract contact RUT from message if present
            # Common patterns: "RUT: 12345678-9" or just "12345678-9"
            contact_rut = self._extract_rut_from_message(context.user_message)

            # If no RUT in message, try to get from additional_data
            if not contact_rut:
                contact_rut = context.additional_data.get("contact_rut")

            # Get contact data
            contact_data = await self._get_contact_data(
                context.db,
                context.company_id,
                contact_rut,
            )

            if not contact_data:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error=f"No se encontró el contacto con RUT {contact_rut}" if contact_rut else "No se especificó un RUT de contacto",
                )

            # Format context text for agent
            context_text = self._format_contact_context(contact_data)

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=contact_data,
                metadata={
                    "contact_rut": contact_data.get("rut"),
                    "contact_type": contact_data.get("contact_type"),
                    "has_transactions": contact_data.get("total_transactions", 0) > 0,
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing contact card: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar información del contacto: {str(e)}",
            )

    async def _get_contact_data(
        self,
        db: AsyncSession,
        company_id: str,
        contact_rut: str | None = None,
    ) -> dict[str, Any] | None:
        """Fetch contact data from database."""

        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return None

        # Build query
        query = select(Contact).where(Contact.company_id == company_uuid)

        if contact_rut:
            query = query.where(Contact.rut == contact_rut)
        else:
            # If no RUT specified, just return None
            # (could optionally return most recent contact)
            return None

        result = await db.execute(query)
        contact = result.scalar_one_or_none()

        if not contact:
            return None

        # Get transaction summary
        sales_summary = await self._get_sales_summary(db, contact.id)
        purchase_summary = await self._get_purchase_summary(db, contact.id)

        return {
            "id": str(contact.id),
            "rut": contact.rut,
            "business_name": contact.business_name,
            "trade_name": contact.trade_name,
            "contact_type": contact.contact_type,
            "address": contact.address,
            "phone": contact.phone,
            "email": contact.email,
            "sales_summary": sales_summary,
            "purchase_summary": purchase_summary,
            "total_transactions": sales_summary["count"] + purchase_summary["count"],
            "total_amount": sales_summary["total"] + purchase_summary["total"],
        }

    async def _get_sales_summary(self, db: AsyncSession, contact_id) -> dict[str, Any]:
        """Get summary of sales documents for this contact."""
        stmt = select(
            func.count(SalesDocument.id).label("count"),
            func.coalesce(func.sum(SalesDocument.monto_total), 0).label("total"),
        ).where(SalesDocument.contact_id == contact_id)

        result = await db.execute(stmt)
        row = result.first()

        return {
            "count": row.count if row else 0,
            "total": float(row.total) if row else 0.0,
        }

    async def _get_purchase_summary(self, db: AsyncSession, contact_id) -> dict[str, Any]:
        """Get summary of purchase documents for this contact."""
        stmt = select(
            func.count(PurchaseDocument.id).label("count"),
            func.coalesce(func.sum(PurchaseDocument.monto_total), 0).label("total"),
        ).where(PurchaseDocument.contact_id == contact_id)

        result = await db.execute(stmt)
        row = result.first()

        return {
            "count": row.count if row else 0,
            "total": float(row.total) if row else 0.0,
        }

    def _extract_rut_from_message(self, message: str) -> str | None:
        """Extract RUT from user message using common patterns."""
        import re

        # Pattern 1: "RUT: 12345678-9"
        match = re.search(r"RUT:?\s*([0-9]{7,8}-[0-9Kk])", message, re.IGNORECASE)
        if match:
            return match.group(1)

        # Pattern 2: Just the RUT "12345678-9"
        match = re.search(r"\b([0-9]{7,8}-[0-9Kk])\b", message)
        if match:
            return match.group(1)

        # Pattern 3: RUT without hyphen "123456789"
        match = re.search(r"\b([0-9]{8,9})\b", message)
        if match:
            rut = match.group(1)
            # Format: insert hyphen before last digit
            return f"{rut[:-1]}-{rut[-1]}"

        return None

    def _format_contact_context(self, contact_data: dict[str, Any]) -> str:
        """Format contact data into human-readable context for agent."""

        contact_type_es = {
            "provider": "Proveedor",
            "client": "Cliente",
            "both": "Proveedor y Cliente",
        }.get(contact_data["contact_type"], contact_data["contact_type"])

        lines = [
            "## 📇 CONTEXTO: Información de Contacto",
            "",
            f"**{contact_data['business_name']}**",
            f"RUT: {contact_data['rut']}",
            f"Tipo: {contact_type_es}",
        ]

        if contact_data.get("trade_name"):
            lines.append(f"Nombre de fantasía: {contact_data['trade_name']}")

        # Contact info
        contact_info = []
        if contact_data.get("email"):
            contact_info.append(f"Email: {contact_data['email']}")
        if contact_data.get("phone"):
            contact_info.append(f"Teléfono: {contact_data['phone']}")
        if contact_data.get("address"):
            contact_info.append(f"Dirección: {contact_data['address']}")

        if contact_info:
            lines.append("")
            lines.extend(contact_info)

        # Transaction summary
        lines.append("")
        lines.append("### 📊 Resumen de Transacciones")

        sales = contact_data["sales_summary"]
        purchases = contact_data["purchase_summary"]

        if sales["count"] > 0:
            lines.append(
                f"- **Ventas**: {sales['count']} documentos, "
                f"Total: ${sales['total']:,.0f}"
            )

        if purchases["count"] > 0:
            lines.append(
                f"- **Compras**: {purchases['count']} documentos, "
                f"Total: ${purchases['total']:,.0f}"
            )

        if contact_data["total_transactions"] == 0:
            lines.append("- Sin transacciones registradas")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("💡 **INSTRUCCIONES PARA EL AGENTE:**")
        lines.append("- Responde de forma **breve y directa** con la información clave del contacto")
        lines.append("- **NO llames a herramientas adicionales** - toda la información necesaria ya está arriba")
        lines.append("- Termina tu respuesta preguntando al usuario qué le gustaría saber sobre este contacto")
        lines.append("")

        return "\n".join(lines)

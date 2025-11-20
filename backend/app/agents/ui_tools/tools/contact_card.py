"""UI Tool for Contact Card component - Supabase Version."""

from __future__ import annotations

import logging
from typing import Any

from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class ContactCardTool(BaseUITool):
    """
    UI Tool for Contact Card component - Supabase Version.

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

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario ve una tarjeta de contacto."""
        return """
## 💡 INSTRUCCIONES: Tarjeta de Contacto

El usuario está viendo la ficha de un contacto específico.

**Tu objetivo:**
- Responde preguntas sobre ESTE contacto (historial, transacciones, datos)
- Usa la información de resumen que ya está cargada arriba (total de transacciones y montos)
- Si el usuario quiere VER los documentos específicos, usa la herramienta `get_documents(rut="XX-X")` con el RUT del contacto
- Sé breve y directo (máximo 3-4 líneas para el resumen inicial)

**Formato de respuesta:**
- Inicia con un resumen clave del contacto basado en el contexto cargado
- Si piden ver documentos, usa la herramienta get_documents con el RUT
- Termina preguntando qué le gustaría saber o hacer con este contacto

**Evita:**
- Temas generales no relacionados con este contacto
- Respuestas largas o explicaciones innecesarias en el saludo inicial
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process contact card interaction and load relevant data."""

        if not context.supabase:
            return UIToolResult(
                success=False,
                context_text="",
                error="Supabase client not available",
            )

        if not context.company_id:
            return UIToolResult(
                success=False,
                context_text="",
                error="Company ID not available in context",
            )

        try:
            # Priority 1: Get RUT from entity_id (frontend UI component click)
            contact_rut = context.additional_data.get("entity_id") if context.additional_data else None

            # Priority 2: Extract contact RUT from message if present
            # Common patterns: "RUT: 12345678-9" or just "12345678-9"
            if not contact_rut:
                contact_rut = self._extract_rut_from_message(context.user_message)

            # Priority 3: Fallback to contact_rut in additional_data
            if not contact_rut:
                contact_rut = context.additional_data.get("contact_rut") if context.additional_data else None

            # Get contact data
            contact_data = await self._get_contact_data(
                context.supabase,
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
        supabase,
        company_id: str,
        contact_rut: str | None = None,
    ) -> dict[str, Any] | None:
        """Fetch contact data from Supabase using repository pattern."""

        if not contact_rut:
            return None

        # Get contact by RUT using contacts repository
        contact = await supabase.contacts.get_by_rut(company_id, contact_rut)

        if not contact:
            return None

        contact_id = contact.get("id")

        # Get transaction summaries using contacts repository
        sales_summary = await supabase.contacts.get_sales_summary(contact_id)
        purchase_summary = await supabase.contacts.get_purchase_summary(contact_id)

        # Handle None responses from repository
        if sales_summary is None:
            sales_summary = {"total_amount": 0, "document_count": 0}
        if purchase_summary is None:
            purchase_summary = {"total_amount": 0, "document_count": 0}

        return {
            "id": contact_id,
            "rut": contact.get("rut"),
            "business_name": contact.get("business_name"),
            "trade_name": contact.get("trade_name"),
            "contact_type": contact.get("contact_type"),
            "address": contact.get("address"),
            "phone": contact.get("phone"),
            "email": contact.get("email"),
            "sales_summary": {
                "count": sales_summary.get("document_count", 0),
                "total": sales_summary.get("total_amount", 0),
            },
            "purchase_summary": {
                "count": purchase_summary.get("document_count", 0),
                "total": purchase_summary.get("total_amount", 0),
            },
            "total_transactions": (
                sales_summary.get("document_count", 0) +
                purchase_summary.get("document_count", 0)
            ),
            "total_amount": (
                sales_summary.get("total_amount", 0) +
                purchase_summary.get("total_amount", 0)
            ),
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

        return "\n".join(lines)

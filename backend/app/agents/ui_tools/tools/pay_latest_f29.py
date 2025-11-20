"""UI Tool for Pay Latest F29 action - Supabase version."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ...tools.widgets.builders import create_f29_payment_flow_widget, f29_payment_flow_widget_copy_text
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class PayLatestF29Tool(BaseUITool):
    """
    UI Tool for Pay Latest F29 action - Supabase version.

    When a user clicks the "Pay F29" button or action in the frontend,
    this tool shows a step-by-step widget guide to pay on SII.
    """

    @property
    def component_name(self) -> str:
        return "pay_latest_f29"

    @property
    def description(self) -> str:
        return "Shows step-by-step payment guide for F29"

    @property
    def domain(self) -> str:
        return "tax"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario quiere pagar el F29."""
        return """
## 💡 INSTRUCCIONES: Pagar F29

El usuario quiere pagar su F29.

**Tu objetivo:**
- Confirmar el F29 que se va a pagar (período y monto)
- Ya se mostró el widget con el paso a paso arriba
- Sé breve y directo (máximo 2-3 líneas)
- Ofrece ayuda adicional si la necesita

**Formato de respuesta:**
1. Confirma el F29: "Perfecto, aquí está la guía para pagar tu F29 de [PERÍODO]."
2. Ofrece ayuda: "¿Necesitas ayuda con algún paso?"

**Evita:**
- Explicar cada paso manualmente (ya está en el widget)
- Respuestas largas
- **NO llames a herramientas adicionales**
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process pay F29 action and show payment flow guide."""

        if not context.company_id:
            return UIToolResult(
                success=False,
                context_text="",
                error="Company ID not available in context",
            )

        try:
            # Parse period from entity_id or default to previous month
            period = self._parse_period_from_entity_id(
                context.additional_data.get("entity_id") if context.additional_data else None
            )

            if period:
                self.logger.info(f"Parsed period from entity_id: {period['year']}-{period['month']:02d}")
            else:
                # Default to previous month
                now = datetime.now()
                period = {
                    "year": now.year if now.month > 1 else now.year - 1,
                    "month": now.month - 1 if now.month > 1 else 12
                }
                self.logger.info(f"Using default period (previous month): {period['year']}-{period['month']:02d}")

            # Format context text for agent
            context_text = self._format_payment_context(period)

            # Create payment flow widget
            period_display = f"{period['year']}-{period['month']:02d}"
            widget = create_f29_payment_flow_widget(
                title=f"Paso a paso: pagar F29 {period_display}",
                url="https://zeusr.sii.cl/AUT2000/InicioAutenticacion/IngresoRutClave.html?https://www4.sii.cl/propuestaf29ui/#/default",
            )

            widget_copy_text = f29_payment_flow_widget_copy_text(
                title=f"Paso a paso: pagar F29 {period_display}",
                url="https://zeusr.sii.cl/AUT2000/InicioAutenticacion/IngresoRutClave.html?https://www4.sii.cl/propuestaf29ui/#/default",
            )

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data={"period": period_display},
                metadata={
                    "period": period_display,
                    "year": period["year"],
                    "month": period["month"],
                },
                widget=widget,
                widget_copy_text=widget_copy_text,
            )

        except Exception as e:
            self.logger.error(f"Error processing pay F29: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al preparar guía de pago F29: {str(e)}",
            )

    def _format_payment_context(self, period: dict[str, int]) -> str:
        """Format F29 payment context for agent."""

        # Format month name in Spanish
        month_names = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        period_display = f"{month_names[period['month'] - 1]} {period['year']}"

        lines = [
            "## 💳 CONTEXTO: Pagar F29",
            "",
            f"**Período**: {period_display}",
            "",
            "---",
            "",
            "💡 **INSTRUCCIONES:**",
            "- Ya se mostró el widget con el paso a paso de pago arriba",
            "- Confirma el F29 a pagar (período)",
            "- Responde en máximo 2-3 líneas",
            "- Ofrece ayuda adicional si la necesita",
            "- **NO llames a herramientas adicionales**",
        ]

        return "\n".join(lines)

    def _parse_period_from_entity_id(self, entity_id: str | None) -> dict[str, int] | None:
        """
        Parse period from entity_id (format: "YYYY-MM" or ISO datetime).

        Args:
            entity_id: Period string in format "YYYY-MM" or ISO datetime (e.g., "2025-10-01T00:00:00") or None

        Returns:
            Dict with year and month keys, or None if parsing fails
        """
        if not entity_id:
            return None

        try:
            # Handle ISO datetime format (e.g., "2025-10-01T00:00:00")
            if "T" in entity_id:
                # Extract just the date part before 'T'
                date_part = entity_id.split("T")[0]
                parts = date_part.split("-")
                if len(parts) >= 2:
                    year = int(parts[0])
                    month = int(parts[1])
                    return {"year": year, "month": month}
            # Handle simple "YYYY-MM" format
            else:
                parts = entity_id.split("-")
                if len(parts) == 2:
                    year = int(parts[0])
                    month = int(parts[1])
                    return {"year": year, "month": month}
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Failed to parse period from entity_id '{entity_id}': {e}")
            return None

        return None

"""UI Tool for Tax Summary Expenses component - Supabase version."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class TaxSummaryExpensesTool(BaseUITool):
    """
    UI Tool for Tax Summary Expenses component - Supabase version.

    When a user clicks on the expenses (gastos) amount,
    this tool provides context about expenses for the period.
    """

    @property
    def component_name(self) -> str:
        return "tax_summary_expenses"

    @property
    def description(self) -> str:
        return "Loads expense details and provider breakdown when user clicks on gastos"

    @property
    def domain(self) -> str:
        return "financials"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario ve el resumen de gastos."""
        return """
## 💡 INSTRUCCIONES: Resumen de Gastos

El usuario está viendo el desglose de sus gastos/compras del período.

**Tu objetivo:**
- Responde de forma **breve y directa** con insights sobre los gastos
- **NO llames herramientas adicionales** - toda la información ya está cargada
- Si no hay documentos, informa brevemente y sugiere próximos pasos

**Formato de respuesta:**
- 2-3 líneas con el resumen clave (total, principales proveedores, tendencias)
- Termina preguntando qué le gustaría saber sobre estos gastos

**Evita:**
- Buscar documentos adicionales
- Explicaciones largas sobre contabilidad
- Repetir números que ya están visibles
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process expenses summary interaction and load relevant data."""

        if not context.company_id:
            return UIToolResult(
                success=False,
                context_text="",
                error="Company ID not available in context",
            )

        try:
            # Get period from entity_id (format: "YYYY-MM") or default to current month
            period = self._parse_period_from_entity_id(
                context.additional_data.get("entity_id") if context.additional_data else None
            )

            # Format period for Supabase query
            period_str = f"{period['year']}-{period['month']:02d}"

            # Get expense data using TaxSummaryService
            from app.services.tax_summary_service import TaxSummaryService

            service = TaxSummaryService(context.supabase)
            expense_data = await service.get_expense_summary(context.company_id, period_str)

            # Format month name
            month_names = [
                "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]
            month_name = month_names[period["month"] - 1]
            period_display = f"{month_name.title()} {period['year']}"

            # Format context text
            context_text = f"""
## 📉 CONTEXTO: Análisis de Gastos

**Período:** {period_display}
**Total de gastos:** ${int(expense_data['total_expenses']):,}
**Gastos netos (sin IVA):** ${int(expense_data['net_expenses']):,}
**Documentos:** {expense_data['document_count']}

### 💡 INSTRUCCIONES:
- El usuario está viendo el resumen de gastos/compras del período
- Responde de forma breve y directa con insights sobre los gastos
- Si no hay documentos, informa brevemente y sugiere próximos pasos
- NO busques documentos adicionales
"""

            return UIToolResult(
                success=True,
                context_text=context_text,
                metadata={
                    "period": period_str,
                    "total_expenses": expense_data['total_expenses'],
                    "net_expenses": expense_data['net_expenses'],
                    "document_count": expense_data['document_count'],
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing expenses summary: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar resumen de gastos: {str(e)}",
            )

    def _parse_period_from_entity_id(self, entity_id: str | None) -> dict[str, int]:
        """Parse period from entity_id (format: "YYYY-MM" or ISO datetime)."""
        now = datetime.now()
        year = now.year
        month = now.month

        if entity_id:
            try:
                if "T" in entity_id:
                    date_part = entity_id.split("T")[0]
                    parts = date_part.split("-")
                    if len(parts) >= 2:
                        year = int(parts[0])
                        month = int(parts[1])
                else:
                    parts = entity_id.split("-")
                    if len(parts) == 2:
                        year = int(parts[0])
                        month = int(parts[1])
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse period from entity_id '{entity_id}': {e}")

        return {"year": year, "month": month}

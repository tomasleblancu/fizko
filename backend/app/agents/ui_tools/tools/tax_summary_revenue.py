"""UI Tool for Tax Summary Revenue component - Supabase version."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class TaxSummaryRevenueTool(BaseUITool):
    """
    UI Tool for Tax Summary Revenue component - Supabase version.

    When a user clicks on the revenue (ingresos) amount,
    this tool provides context about revenue for the period.
    """

    @property
    def component_name(self) -> str:
        return "tax_summary_revenue"

    @property
    def description(self) -> str:
        return "Loads revenue details and client breakdown when user clicks on ingresos"

    @property
    def domain(self) -> str:
        return "financials"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario ve el resumen de ingresos."""
        return """
## 💡 INSTRUCCIONES: Resumen de Ingresos

El usuario está viendo el desglose de sus ingresos/ventas del período.

**Tu objetivo:**
- Responde de forma **breve y directa** con insights sobre los ingresos
- **NO llames herramientas adicionales** - toda la información ya está cargada
- Si no hay documentos, informa brevemente y sugiere próximos pasos

**Formato de respuesta:**
- 2-3 líneas con el resumen clave (total, principales clientes, tendencias)
- Termina preguntando qué le gustaría saber sobre estos ingresos

**Evita:**
- Buscar documentos adicionales
- Explicaciones largas sobre contabilidad
- Repetir números que ya están visibles
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process revenue summary interaction and load relevant data."""

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

            # Get revenue data using TaxSummaryService
            from app.services.tax_summary_service import TaxSummaryService

            service = TaxSummaryService(context.supabase)
            revenue_data = await service.get_revenue_summary(context.company_id, period_str)

            # Format month name
            month_names = [
                "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]
            month_name = month_names[period["month"] - 1]
            period_display = f"{month_name.title()} {period['year']}"

            # Format context text
            context_text = f"""
## 📈 CONTEXTO: Análisis de Ingresos

**Período:** {period_display}
**Total de ingresos:** ${int(revenue_data['total_revenue']):,}
**Ingresos netos (sin IVA):** ${int(revenue_data['net_revenue']):,}
**Documentos:** {revenue_data['document_count']}

### 💡 INSTRUCCIONES:
- El usuario está viendo el resumen de ingresos/ventas del período
- Responde de forma breve y directa con insights sobre los ingresos
- Si no hay documentos, informa brevemente y sugiere próximos pasos
- NO busques documentos adicionales
"""

            return UIToolResult(
                success=True,
                context_text=context_text,
                metadata={
                    "period": period_str,
                    "total_revenue": revenue_data['total_revenue'],
                    "net_revenue": revenue_data['net_revenue'],
                    "document_count": revenue_data['document_count'],
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing revenue summary: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar resumen de ingresos: {str(e)}",
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

"""UI Tool for Tax Period Card component - Supabase version."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ...tools.widgets.builders import create_tax_calculation_widget, tax_calculation_widget_copy_text
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class TaxPeriodCardTool(BaseUITool):
    """
    UI Tool for Tax Period Card component - Supabase version.

    When a user clicks on a tax period (month) card,
    this tool provides a comprehensive overview of the period including:
    - IVA calculation (débito, crédito, balance)
    - PPM and Retención
    - Previous month credit (remanente)
    - Monthly tax total
    - Document counts (sales, purchases)
    """

    @property
    def component_name(self) -> str:
        return "tax_period_card"

    @property
    def description(self) -> str:
        return "Loads comprehensive tax period overview when user clicks on period card"

    @property
    def domain(self) -> str:
        return "tax_compliance"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario ve el resumen del período tributario."""
        return """
## 💡 INSTRUCCIONES: Resumen del Período Tributario

El usuario está viendo el resumen completo de un período tributario (mes).

**Contexto:**
- Ya se mostró un widget interactivo con el desglose del cálculo de impuestos
- Toda la información de ventas, compras, IVA, PPM y retenciones ya está cargada

**Tu objetivo:**
- Explica BREVEMENTE (máximo 2-3 líneas) el estado del período
- **NO repitas** los números que ya están en el widget
- **NO llames herramientas adicionales** - toda la info está arriba
- Si hay algo notable (crédito a favor, impuesto alto, etc.), menciónalo

**Formato de respuesta:**
- 1-2 líneas con insight clave sobre el período
- Pregunta si necesita más detalles o ayuda con obligaciones tributarias

**Evita:**
- Repetir el desglose completo del cálculo
- Explicaciones largas de conceptos que ya están en el widget
- Llamar herramientas de búsqueda de documentos
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process tax period card interaction and load relevant data from Supabase."""

        if not context.company_id:
            return UIToolResult(
                success=False,
                context_text="",
                error="Company ID not available in context",
            )

        try:
            # Get period from entity_id (format: ISO datetime like "2025-10-01T03:00:00.000Z")
            period = self._parse_period_from_entity_id(
                context.additional_data.get("entity_id") if context.additional_data else None
            )

            # Format period for Supabase query (YYYY-MM format)
            period_str = f"{period['year']}-{period['month']:02d}"

            # Get comprehensive tax data using TaxSummaryService
            from app.services.tax_summary_service import TaxSummaryService

            service = TaxSummaryService(context.supabase)
            iva_data = await service.get_iva_summary(context.company_id, period_str)
            revenue_data = await service.get_revenue_summary(context.company_id, period_str)
            expense_data = await service.get_expense_summary(context.company_id, period_str)

            # Format month name
            month_names = [
                "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]
            month_name = month_names[period["month"] - 1]
            period_display = f"{month_name.title()} {period['year']}"

            # Calculate monthly tax: IVA balance - previous month credit + PPM + Retención
            monthly_tax = (
                iva_data["balance"]
                - (iva_data.get("previous_month_credit", 0.0) or 0.0)
                + (iva_data.get("ppm", 0.0) or 0.0)
                + (iva_data.get("retencion", 0.0) or 0.0)
            )

            # Format context text with comprehensive period info
            context_text = f"""
## 📅 CONTEXTO: Período Tributario {period_display}

**Resumen del período:**
- Impuesto mensual total: ${int(monthly_tax):,}
- Documentos de venta: {iva_data['sales_count']}
- Documentos de compra: {iva_data['purchases_count']}

**IVA:**
- Débito fiscal (ventas): ${int(iva_data['debito_fiscal']):,}
- Crédito fiscal (compras): ${int(iva_data['credito_fiscal']):,}
- Balance IVA: ${int(iva_data['balance']):,}

**Otros impuestos:**
- Crédito mes anterior: ${int(iva_data.get('previous_month_credit', 0.0) or 0.0):,}
- PPM: ${int(iva_data.get('ppm', 0.0) or 0.0):,}
- Retención: ${int(iva_data.get('retencion', 0.0) or 0.0):,}

**Ingresos y gastos:**
- Ingresos totales: ${int(revenue_data.get('total_revenue', 0.0)):,}
- Gastos totales: ${int(expense_data.get('total_expenses', 0.0)):,}

### 💡 INSTRUCCIONES:
- Ya se mostró el widget con el desglose completo arriba
- Explica brevemente el estado del período (máximo 2-3 líneas)
- NO repitas los números que ya están en el widget
- Pregunta si necesita más información o ayuda con obligaciones
"""

            # Create widget if there's data
            widget = None
            widget_copy_text = None
            if iva_data["sales_count"] > 0 or iva_data["purchases_count"] > 0:
                widget = create_tax_calculation_widget(
                    iva_collected=iva_data["debito_fiscal"],
                    iva_paid=iva_data["credito_fiscal"],
                    previous_month_credit=iva_data.get("previous_month_credit", 0.0),
                    monthly_tax=monthly_tax,
                    period=period_display,
                    ppm=iva_data.get("ppm", 0.0),
                    retencion=iva_data.get("retencion", 0.0),
                    impuesto_trabajadores=0.0,  # TODO: Get from payroll system when available
                )

                widget_copy_text = tax_calculation_widget_copy_text(
                    iva_collected=iva_data["debito_fiscal"],
                    iva_paid=iva_data["credito_fiscal"],
                    previous_month_credit=iva_data.get("previous_month_credit", 0.0),
                    monthly_tax=monthly_tax,
                    period=period_display,
                    ppm=iva_data.get("ppm", 0.0),
                    retencion=iva_data.get("retencion", 0.0),
                    impuesto_trabajadores=0.0,
                )

            return UIToolResult(
                success=True,
                context_text=context_text,
                metadata={
                    "period": period_str,
                    "monthly_tax": monthly_tax,
                    "has_documents": iva_data["sales_count"] > 0 or iva_data["purchases_count"] > 0,
                    "sales_count": iva_data["sales_count"],
                    "purchases_count": iva_data["purchases_count"],
                    "total_revenue": revenue_data.get("total_revenue", 0.0),
                    "total_expenses": expense_data.get("total_expenses", 0.0),
                },
                widget=widget,
                widget_copy_text=widget_copy_text,
            )

        except Exception as e:
            self.logger.error(f"Error processing tax period card: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar resumen del período: {str(e)}",
            )

    def _parse_period_from_entity_id(self, entity_id: str | None) -> dict[str, int]:
        """Parse period from entity_id (format: ISO datetime like "2025-10-01T03:00:00.000Z")."""
        now = datetime.now()
        year = now.year
        month = now.month

        if entity_id:
            try:
                # Parse ISO datetime format
                if "T" in entity_id:
                    date_part = entity_id.split("T")[0]
                    parts = date_part.split("-")
                    if len(parts) >= 2:
                        year = int(parts[0])
                        month = int(parts[1])
                else:
                    # Fallback for "YYYY-MM" format
                    parts = entity_id.split("-")
                    if len(parts) == 2:
                        year = int(parts[0])
                        month = int(parts[1])
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse period from entity_id '{entity_id}': {e}. Using current month.")

        return {"year": year, "month": month}

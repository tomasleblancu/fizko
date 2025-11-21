"""UI Tool for Tax Summary IVA component - Supabase version."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ...tools.widgets.builders import create_tax_calculation_widget, tax_calculation_widget_copy_text
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class TaxSummaryIVATool(BaseUITool):
    """
    UI Tool for Tax Summary IVA component - Supabase version.

    When a user clicks on the IVA amount in the tax summary card,
    this tool provides context about IVA calculation for the period.
    """

    @property
    def component_name(self) -> str:
        return "tax_summary_iva"

    @property
    def description(self) -> str:
        return "Loads IVA calculation details when user clicks on IVA amount"

    @property
    def domain(self) -> str:
        return "tax_compliance"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario ve el cálculo de IVA."""
        return """
## 💡 INSTRUCCIONES: Cálculo de Impuesto Mensual

El usuario está viendo el desglose del cálculo de impuesto mensual (IVA).

**Contexto:**
- Ya se mostró un widget interactivo con el desglose completo del cálculo
- Toda la información de ventas, compras, y otros impuestos ya está cargada

**Detalles técnicos del cálculo:**
- **IVA Cobrado**: IVA de ventas (facturas, boletas) menos IVA de notas de crédito
- **IVA Pagado**: IVA de compras (facturas) menos IVA de notas de crédito de compra
- **IVA Crédito Mes Anterior**: Crédito a favor del mes anterior (del F29 previo)
- **IVA Fuera de plazo**: IVA de documentos antiguos que no se puede recuperar (tanto de facturas como NC)
- **PPM (Pago Provisional Mensual)**: 0.125% del ingreso neto (ventas sin IVA, después de restar NC). IMPORTANTE: Los documentos con "IVA Fuera de plazo" NO se consideran en la base del PPM (se excluyen del cálculo)
- **Retención**: Retención de honorarios recibidos (boletas de honorarios pagadas)

**Tu objetivo:**
- Explica BREVEMENTE (máximo 2 líneas) el resultado del cálculo
- **NO repitas** los números que ya están en el widget
- **NO llames herramientas adicionales** - toda la info está arriba
- Si hay crédito a favor o impuesto a pagar, explica qué significa

**Formato de respuesta:**
- 1-2 líneas con insight clave (ej: "Tienes un impuesto a pagar de $X porque...")
- Pregunta si necesita más detalles o tiene dudas sobre el cálculo

**Evita:**
- Repetir el desglose completo del cálculo
- Explicaciones largas de conceptos que ya están en el widget
- Llamar herramientas de búsqueda de documentos
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process IVA summary interaction and load relevant data from Supabase."""

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

            # Format period for Supabase query (YYYY-MM format)
            period_str = f"{period['year']}-{period['month']:02d}"

            # Get IVA data using TaxSummaryService (not repository)
            from app.services.tax_summary_service import TaxSummaryService

            service = TaxSummaryService(context.supabase)
            iva_data = await service.get_iva_summary(context.company_id, period_str)

            # Format month name
            month_names = [
                "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]
            month_name = month_names[period["month"] - 1]
            period_display = f"{month_name.title()} {period['year']}"

            # Calculate IVA balance with previous month credit
            # Balance from service is: debito_fiscal - credito_fiscal
            # We need to subtract previous month credit to get IVA a pagar
            iva_balance = (
                iva_data["balance"]
                - (iva_data.get("previous_month_credit", 0.0) or 0.0)
            )
            iva_a_pagar = max(0.0, iva_balance)

            # Calculate monthly tax: IVA a pagar + overdue IVA + PPM + Retención + Impuesto Trabajadores
            monthly_tax = (
                iva_a_pagar
                + (iva_data.get("overdue_iva_credit", 0.0) or 0.0)
                + (iva_data.get("ppm", 0.0) or 0.0)
                + (iva_data.get("retencion", 0.0) or 0.0)
                + 0.0  # impuesto_trabajadores - will be added when payroll is integrated
            )

            # Format context text
            context_text = f"""
## 💰 CONTEXTO: Cálculo de Impuesto Mensual

**Período:** {period_display}
**Impuesto mensual:** ${int(monthly_tax):,}

**Desglose:**
- IVA débito fiscal (ventas): ${int(iva_data['debito_fiscal']):,}
- IVA crédito fiscal (compras): ${int(iva_data['credito_fiscal']):,}
- Balance: ${int(iva_data['balance']):,}

### 💡 INSTRUCCIONES:
- Ya se mostró el widget con el desglose completo arriba
- Explica brevemente el resultado (máximo 2 líneas)
- NO repitas los números que ya están en el widget
- Pregunta si necesita más detalles sobre el cálculo
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
                    overdue_iva_credit=iva_data.get("overdue_iva_credit", 0.0),
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
                    overdue_iva_credit=iva_data.get("overdue_iva_credit", 0.0),
                )

            return UIToolResult(
                success=True,
                context_text=context_text,
                metadata={
                    "period": period_str,
                    "monthly_tax": monthly_tax,
                    "has_documents": iva_data["sales_count"] > 0 or iva_data["purchases_count"] > 0,
                },
                widget=widget,
                widget_copy_text=widget_copy_text,
            )

        except Exception as e:
            self.logger.error(f"Error processing IVA summary: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar resumen de IVA: {str(e)}",
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
                logger.warning(f"Failed to parse period from entity_id '{entity_id}': {e}. Using current month.")

        return {"year": year, "month": month}

"""UI Tool for Pay Latest F29 action."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.tax import TaxSummaryRepository
from ...tools.widgets.builders import create_f29_payment_flow_widget, f29_payment_flow_widget_copy_text
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class PayLatestF29Tool(BaseUITool):
    """
    UI Tool for Pay Latest F29 action.

    When a user clicks the "Pay F29" button or action in the frontend,
    this tool:
    - Calculates the F29 for the requested period using TaxSummaryRepository
    - Shows a step-by-step widget guide to pay on SII
    - Triggers Celery task to save/update Form29 draft in background
    - Provides context about the calculated F29 values

    This gives the agent immediate context about the F29 to pay
    and displays a helpful payment flow guide with accurate amounts.
    """

    @property
    def component_name(self) -> str:
        return "pay_latest_f29"

    @property
    def description(self) -> str:
        return "Calculates F29 values and shows step-by-step payment guide"

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
1. Confirma el F29: "Perfecto, aquí está la guía para pagar tu F29 de [PERÍODO] por [MONTO]."
2. Ofrece ayuda: "¿Necesitas ayuda con algún paso?"

**Evita:**
- Explicar cada paso manualmente (ya está en el widget)
- Respuestas largas
- **NO llames a herramientas adicionales**
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process pay F29 action, calculate values, and show payment flow guide."""

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

            # Calculate F29 values using TaxSummaryRepository
            f29_data = await self._calculate_f29_values(
                context.db,
                context.company_id,
                period["year"],
                period["month"],
            )

            if not f29_data:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error=f"No se pudo calcular el F29 del período {period['year']}-{period['month']:02d}",
                )

            # Trigger Celery task to save Form29 draft (fire-and-forget)
            self._trigger_f29_draft_generation(
                context.company_id,
                period["year"],
                period["month"],
            )

            # Format context text for agent
            context_text = self._format_payment_context(f29_data, period)

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
                structured_data=f29_data,
                metadata={
                    "period": period_display,
                    "monthly_tax": f29_data.get("monthly_tax"),
                    "calculated": True,
                },
                widget=widget,
                widget_copy_text=widget_copy_text,
            )

        except Exception as e:
            self.logger.error(f"Error processing pay F29: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al calcular información del F29: {str(e)}",
            )

    async def _calculate_f29_values(
        self,
        db: AsyncSession,
        company_id: str,
        year: int,
        month: int,
    ) -> dict[str, Any] | None:
        """
        Calculate F29 values for a period using TaxSummaryRepository.

        This uses the same logic as /api/tax-summary endpoint.
        """
        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return None

        try:
            # Format period as YYYY-MM
            period = f"{year}-{month:02d}"

            # Use TaxSummaryRepository to calculate values
            repo = TaxSummaryRepository(db)
            summary = await repo.get_tax_summary(company_uuid, period)

            # Format month name in Spanish
            month_names = [
                "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]
            period_display = f"{month_names[month - 1]} {year}"

            # Calculate IVA to pay (positive net_iva, or 0 if negative)
            iva_to_pay = max(0.0, summary.net_iva)

            return {
                "period": period,
                "period_display": period_display,
                "period_year": year,
                "period_month": month,
                "total_revenue": summary.total_revenue,
                "total_expenses": summary.total_expenses,
                "iva_collected": summary.iva_collected,
                "iva_paid": summary.iva_paid,
                "net_iva": summary.net_iva,
                "iva_to_pay": iva_to_pay,
                "previous_month_credit": summary.previous_month_credit or 0.0,
                "ppm": summary.ppm or 0.0,
                "retencion": summary.retencion or 0.0,
                "impuesto_trabajadores": summary.impuesto_trabajadores or 0.0,
                "monthly_tax": summary.monthly_tax,
                "monthly_tax_formatted": f"${int(summary.monthly_tax):,}",
            }

        except Exception as e:
            self.logger.error(f"Error calculating F29 values: {e}", exc_info=True)
            return None

    def _trigger_f29_draft_generation(
        self,
        company_id: str,
        year: int,
        month: int,
    ) -> None:
        """
        Trigger Celery task to generate/update Form29 draft in background.

        This is fire-and-forget - we don't wait for the result.
        """
        try:
            from app.infrastructure.celery.tasks.forms.form29 import generate_f29_draft_for_company

            # Dispatch Celery task (async)
            generate_f29_draft_for_company.delay(
                company_id=company_id,
                period_year=year,
                period_month=month,
                auto_calculate=True
            )

            self.logger.info(
                f"✅ Triggered F29 draft generation for company {company_id}, "
                f"period {year}-{month:02d}"
            )

        except Exception as e:
            # Log error but don't fail the request
            self.logger.error(
                f"⚠️ Failed to trigger F29 draft generation: {e}",
                exc_info=True
            )

    def _format_payment_context(self, f29_data: dict[str, Any], period: dict[str, int]) -> str:
        """Format F29 payment context for agent."""

        lines = [
            "## 💳 CONTEXTO: Pagar F29",
            "",
            f"**Período**: {f29_data['period_display']}",
            f"**Impuesto mensual a pagar**: {f29_data['monthly_tax_formatted']}",
            "",
            "**Desglose:**",
            f"- IVA débito fiscal: ${int(f29_data['iva_collected']):,}",
            f"- IVA crédito fiscal: ${int(f29_data['iva_paid']):,}",
        ]

        if f29_data.get("previous_month_credit", 0) > 0:
            lines.append(f"- Crédito mes anterior: ${int(f29_data['previous_month_credit']):,}")

        if f29_data.get("ppm", 0) > 0:
            lines.append(f"- PPM: ${int(f29_data['ppm']):,}")

        if f29_data.get("retencion", 0) > 0:
            lines.append(f"- Retención: ${int(f29_data['retencion']):,}")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("💡 **INSTRUCCIONES:**")
        lines.append("- Ya se mostró el widget con el paso a paso de pago arriba")
        lines.append("- Confirma el F29 a pagar (período y monto)")
        lines.append("- Responde en máximo 2-3 líneas")
        lines.append("- Ofrece ayuda adicional si la necesita")
        lines.append("- **NO llames a herramientas adicionales**")

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

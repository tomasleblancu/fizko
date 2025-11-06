"""UI Tool for Tax Summary IVA component."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.models import Company
from ....repositories.tax import TaxSummaryRepository
from ...tools.widgets.widgets import create_tax_calculation_widget, tax_calculation_widget_copy_text
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class TaxSummaryIVATool(BaseUITool):
    """
    UI Tool for Tax Summary IVA component.

    When a user clicks on the IVA amount in the tax summary card,
    this tool pre-loads:
    - IVA débito fiscal (from sales)
    - IVA crédito fiscal (from purchases)
    - Net IVA to pay
    - Document breakdown
    - Calculation explanation

    This allows the agent to immediately explain the IVA calculation
    without needing to call calculation tools first.
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

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process IVA summary interaction and load relevant data."""

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
            # Get period from entity_id (format: "YYYY-MM") or default to current month
            period = self._parse_period_from_entity_id(context.additional_data.get("entity_id"))

            # Get company info
            company_data = await self._get_company_info(context.db, context.company_id)
            if not company_data:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se encontró información de la empresa",
                )

            # Get IVA summary for the period
            iva_data = await self._get_iva_summary(
                context.db,
                context.company_id,
                period["year"],
                period["month"],
            )

            # Combine data
            full_data = {
                **company_data,
                "iva_data": iva_data,
                "period": period,
            }

            # Format context text
            context_text = self._format_iva_context(full_data)

            # Create widget to stream immediately
            widget = None
            widget_copy_text = None
            if iva_data["total_documents"] > 0:
                # Get month name for widget
                month_names = [
                    "enero", "febrero", "marzo", "abril", "mayo", "junio",
                    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
                ]
                month_name = month_names[period["month"] - 1]
                period_str = f"{month_name.title()} {period['year']}"

                widget = create_tax_calculation_widget(
                    iva_collected=iva_data["iva_debito_fiscal"],
                    iva_paid=iva_data["iva_credito_fiscal"],
                    previous_month_credit=iva_data.get("previous_month_credit") or 0.0,
                    monthly_tax=iva_data["monthly_tax"],
                    period=period_str,
                    ppm=iva_data.get("ppm") or 0.0,
                    retencion=iva_data.get("retencion") or 0.0,
                    impuesto_trabajadores=iva_data.get("impuesto_trabajadores") or 0.0,
                )

                widget_copy_text = tax_calculation_widget_copy_text(
                    iva_collected=iva_data["iva_debito_fiscal"],
                    iva_paid=iva_data["iva_credito_fiscal"],
                    previous_month_credit=iva_data.get("previous_month_credit") or 0.0,
                    monthly_tax=iva_data["monthly_tax"],
                    period=period_str,
                    ppm=iva_data.get("ppm") or 0.0,
                    retencion=iva_data.get("retencion") or 0.0,
                    impuesto_trabajadores=iva_data.get("impuesto_trabajadores") or 0.0,
                )

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=full_data,
                metadata={
                    "period": f"{period['year']}-{period['month']:02d}",
                    "iva_to_pay": iva_data["iva_a_pagar"],
                    "has_documents": iva_data["total_documents"] > 0,
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

    async def _get_iva_summary(
        self,
        db: AsyncSession,
        company_id: str,
        year: int,
        month: int,
    ) -> dict[str, Any]:
        """
        Get IVA summary for a specific period using TaxSummaryRepository.

        This ensures consistency with the /api/tax-summary endpoint.
        """
        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return self._empty_iva_summary()

        try:
            # Use TaxSummaryRepository for consistent calculation
            repo = TaxSummaryRepository(db)
            period_str = f"{year}-{month:02d}"

            tax_summary = await repo.get_tax_summary(company_uuid, period_str)

            # Convert TaxSummary to legacy format for backwards compatibility
            # The widget and context expect the old dict format
            return {
                "sales": {
                    "count": 0,  # Not available in TaxSummary, but not used in widget
                    "neto": 0.0,  # Not available in TaxSummary, but not used in widget
                    "iva": tax_summary.iva_collected,
                    "total": tax_summary.total_revenue,
                },
                "purchases": {
                    "count": 0,  # Not available in TaxSummary, but not used in widget
                    "neto": 0.0,  # Not available in TaxSummary, but not used in widget
                    "iva": tax_summary.iva_paid,
                    "total": tax_summary.total_expenses,
                },
                "iva_debito_fiscal": tax_summary.iva_collected,
                "iva_credito_fiscal": tax_summary.iva_paid,
                "iva_neto": tax_summary.net_iva,
                "previous_month_credit": tax_summary.previous_month_credit,
                "ppm": tax_summary.ppm,
                "retencion": tax_summary.retencion,
                "impuesto_trabajadores": tax_summary.impuesto_trabajadores,
                "monthly_tax": tax_summary.monthly_tax,
                "iva_a_pagar": tax_summary.monthly_tax,  # Keep for backward compatibility
                "total_documents": 1 if tax_summary.iva_collected > 0 or tax_summary.iva_paid > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Error getting tax summary from repository: {e}", exc_info=True)
            return self._empty_iva_summary()

    def _empty_iva_summary(self) -> dict[str, Any]:
        """Return empty IVA summary structure."""
        return {
            "sales": {"count": 0, "neto": 0.0, "iva": 0.0, "total": 0.0},
            "purchases": {"count": 0, "neto": 0.0, "iva": 0.0, "total": 0.0},
            "iva_debito_fiscal": 0.0,
            "iva_credito_fiscal": 0.0,
            "iva_neto": 0.0,
            "previous_month_credit": None,
            "ppm": None,
            "retencion": None,
            "impuesto_trabajadores": None,
            "monthly_tax": 0.0,
            "iva_a_pagar": 0.0,
            "total_documents": 0,
        }

    def _parse_period_from_entity_id(self, entity_id: str | None) -> dict[str, int]:
        """
        Parse period from entity_id (format: "YYYY-MM" or ISO datetime).

        Args:
            entity_id: Period string in format "YYYY-MM" or ISO datetime (e.g., "2025-10-01T00:00:00") or None

        Returns:
            Dict with year and month keys
        """
        # Default to current month
        now = datetime.now()
        year = now.year
        month = now.month

        # Parse entity_id if provided
        if entity_id:
            try:
                # Handle ISO datetime format (e.g., "2025-10-01T00:00:00")
                if "T" in entity_id:
                    # Extract just the date part before 'T'
                    date_part = entity_id.split("T")[0]
                    parts = date_part.split("-")
                    if len(parts) >= 2:
                        year = int(parts[0])
                        month = int(parts[1])
                # Handle simple "YYYY-MM" format
                else:
                    parts = entity_id.split("-")
                    if len(parts) == 2:
                        year = int(parts[0])
                        month = int(parts[1])
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse period from entity_id '{entity_id}': {e}. Using current month.")

        return {"year": year, "month": month}

    def _format_iva_context(self, data: dict[str, Any]) -> str:
        """Format IVA data into human-readable context for agent."""

        period = data["period"]
        month_names = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        month_name = month_names[period["month"] - 1]

        iva_data = data["iva_data"]
        sales = iva_data["sales"]
        purchases = iva_data["purchases"]

        # Get tax components
        previous_credit = iva_data.get('previous_month_credit')
        iva_neto = iva_data.get('iva_neto', iva_data['iva_debito_fiscal'] - iva_data['iva_credito_fiscal'])
        monthly_tax = iva_data.get('monthly_tax', 0.0)
        ppm = iva_data.get('ppm', 0.0)
        retencion = iva_data.get('retencion', 0.0)
        impuesto_trabajadores = iva_data.get('impuesto_trabajadores', 0.0)

        # Calculate IVA balance and IVA a pagar
        iva_balance = iva_data['iva_debito_fiscal'] - iva_data['iva_credito_fiscal'] - (previous_credit or 0.0)
        iva_a_pagar = max(0.0, iva_balance)

        lines = [
            "## 💰 CONTEXTO: Cálculo de Impuesto Mensual",
            "",
            f"**{data['business_name']}** (RUT: {data['rut']})",
            f"**Período:** {month_name.title()} {period['year']}",
            "",
            "### 📤 Débito Fiscal (Ventas)",
            f"- **{sales['count']} documentos** emitidos",
            f"- Monto Neto: ${sales['neto']:,.0f}",
            f"- **IVA Débito Fiscal (IVA Cobrado): ${sales['iva']:,.0f}**",
            f"- Monto Total: ${sales['total']:,.0f}",
            "",
            "### 📥 Crédito Fiscal (Compras)",
            f"- **{purchases['count']} documentos** recibidos",
            f"- Monto Neto: ${purchases['neto']:,.0f}",
            f"- **IVA Crédito Fiscal (IVA Pagado): ${purchases['iva']:,.0f}**",
            f"- Monto Total: ${purchases['total']:,.0f}",
            "",
            "### 🧮 Cálculo del Impuesto Mensual",
            "```",
            "PASO 1: Calcular IVA a pagar",
            f"  + IVA Cobrado: ${iva_data['iva_debito_fiscal']:,.0f}",
            f"  - IVA Pagado: ${iva_data['iva_credito_fiscal']:,.0f}",
        ]

        if previous_credit is not None:
            lines.append(f"  - Crédito Mes Anterior (código 077 del F29): ${previous_credit:,.0f}")
        else:
            lines.append(f"  - Crédito Mes Anterior: $0 (no se encontró F29 del mes anterior)")

        lines.extend([
            "  " + "=" * 40,
            f"  IVA a Pagar = MAX(0, resultado) = ${iva_a_pagar:,.0f}",
            "",
        ])

        # Add other taxes if present
        has_other_taxes = False
        if ppm and ppm > 0:
            if not has_other_taxes:
                lines.append("PASO 2: Sumar otros impuestos mensuales")
                has_other_taxes = True
            # Note: PPM is calculated as 0.125% of total revenue
            lines.append(f"  + PPM (Pago Provisional Mensual - 0.125% de ventas): ${ppm:,.0f}")

        if retencion and retencion > 0:
            if not has_other_taxes:
                lines.append("PASO 2: Sumar otros impuestos mensuales")
                has_other_taxes = True
            lines.append(f"  + Retención (Honorarios): ${retencion:,.0f}")

        if impuesto_trabajadores and impuesto_trabajadores > 0:
            if not has_other_taxes:
                lines.append("PASO 2: Sumar otros impuestos mensuales")
                has_other_taxes = True
            lines.append(f"  + Impuesto Trabajadores: ${impuesto_trabajadores:,.0f}")

        if has_other_taxes:
            lines.extend([
                "  " + "=" * 40,
                f"  Impuesto Total a Pagar = ${monthly_tax:,.0f}",
            ])
        else:
            lines.append(f"  Impuesto Total a Pagar = ${monthly_tax:,.0f}")

        lines.extend([
            "```",
            "",
            "**NOTAS IMPORTANTES:**",
            "- El crédito del mes anterior se obtiene del código 077 (remanente) del F29 del mes anterior.",
            "- Si el balance de IVA es negativo, significa que hay un remanente a favor que se arrastra al próximo mes.",
            "- El PPM se calcula automáticamente como 0.125% de las ventas totales.",
            "",
        ])

        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("💡 **INSTRUCCIONES PARA EL AGENTE:**")
        if iva_data["total_documents"] == 0:
            lines.append("- Informa de forma breve que no hay documentos para este período")
            lines.append("- Pregunta al usuario qué le gustaría saber sobre el impuesto mensual")
        else:
            lines.append("- Ya se mostró el widget con el desglose del cálculo arriba")
            lines.append("- Responde en máximo 2 líneas explicando brevemente el resultado")
            lines.append("- NO repitas los números que ya están en el widget")
            lines.append("- Termina preguntando si quiere más detalles")
        lines.append("- **NO llames a herramientas adicionales**")

        lines.append("")
        return "\n".join(lines)

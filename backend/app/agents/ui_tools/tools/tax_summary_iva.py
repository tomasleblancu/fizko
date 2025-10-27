"""UI Tool for Tax Summary IVA component."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.models import Company, Form29SIIDownload, PurchaseDocument, SalesDocument
from ...widgets import create_tax_calculation_widget, tax_calculation_widget_copy_text
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
            # Get current period (default to current month)
            period = self._extract_period_from_message(context.user_message)

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
                    previous_month_credit=iva_data.get("previous_month_credit"),
                    monthly_tax=iva_data["monthly_tax"],
                    period=period_str,
                )

                widget_copy_text = tax_calculation_widget_copy_text(
                    iva_collected=iva_data["iva_debito_fiscal"],
                    iva_paid=iva_data["iva_credito_fiscal"],
                    previous_month_credit=iva_data.get("previous_month_credit"),
                    monthly_tax=iva_data["monthly_tax"],
                    period=period_str,
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
        """Get IVA summary for a specific period."""
        import time

        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return self._empty_iva_summary()

        # Date range for the month
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        # Get sales summary (IVA débito)
        sales_query_start = time.time()
        sales_stmt = select(
            func.count(SalesDocument.id).label("count"),
            func.coalesce(func.sum(SalesDocument.net_amount), 0).label("neto"),
            func.coalesce(func.sum(SalesDocument.tax_amount), 0).label("iva"),
            func.coalesce(func.sum(SalesDocument.total_amount), 0).label("total"),
        ).where(
            SalesDocument.company_id == company_uuid,
            SalesDocument.issue_date >= start_date,
            SalesDocument.issue_date < end_date,
        )

        sales_result = await db.execute(sales_stmt)
        sales = sales_result.first()
        logger.debug(f"    💰 Sales query: {(time.time() - sales_query_start):.3f}s")

        # Get purchases summary (IVA crédito)
        purchases_query_start = time.time()
        purchases_stmt = select(
            func.count(PurchaseDocument.id).label("count"),
            func.coalesce(func.sum(PurchaseDocument.net_amount), 0).label("neto"),
            func.coalesce(func.sum(PurchaseDocument.tax_amount), 0).label("iva"),
            func.coalesce(func.sum(PurchaseDocument.total_amount), 0).label("total"),
        ).where(
            PurchaseDocument.company_id == company_uuid,
            PurchaseDocument.issue_date >= start_date,
            PurchaseDocument.issue_date < end_date,
        )

        purchases_result = await db.execute(purchases_stmt)
        purchases = purchases_result.first()
        logger.debug(f"    💳 Purchases query: {(time.time() - purchases_query_start):.3f}s")

        # Calculate IVA
        iva_debito = float(sales.iva) if sales else 0.0
        iva_credito = float(purchases.iva) if purchases else 0.0

        # Get previous month credit from F29
        previous_month_credit = None
        try:
            # Calculate previous month
            if month == 1:
                prev_year = year - 1
                prev_month = 12
            else:
                prev_year = year
                prev_month = month - 1

            # Query for the "Vigente" (valid) F29 of previous month
            f29_query_start = time.time()
            f29_prev_stmt = select(Form29SIIDownload).where(
                and_(
                    Form29SIIDownload.company_id == company_uuid,
                    Form29SIIDownload.period_year == prev_year,
                    Form29SIIDownload.period_month == prev_month,
                    Form29SIIDownload.status == 'Vigente'
                )
            ).order_by(Form29SIIDownload.created_at.desc()).limit(1)

            f29_prev_result = await db.execute(f29_prev_stmt)
            f29_prev = f29_prev_result.scalar_one_or_none()
            logger.debug(f"    📋 F29 previous month query: {(time.time() - f29_query_start):.3f}s")

            if f29_prev and f29_prev.extra_data:
                # Extract remanente from extra_data["f29_data"]["codes"]["077"]["value"]
                f29_data = f29_prev.extra_data.get("f29_data", {})
                codes = f29_data.get("codes", {})
                code_077 = codes.get("077", {})
                remanente_value = code_077.get("value")

                if remanente_value is not None:
                    previous_month_credit = float(remanente_value)
        except Exception as e:
            logger.warning(f"Error fetching previous month credit: {e}")
            # Continue without previous_month_credit

        # Calculate monthly tax (IVA to pay after applying previous month credit)
        iva_neto = iva_debito - iva_credito
        monthly_tax = max(0, iva_neto - (previous_month_credit or 0.0))

        return {
            "sales": {
                "count": sales.count if sales else 0,
                "neto": float(sales.neto) if sales else 0.0,
                "iva": iva_debito,
                "total": float(sales.total) if sales else 0.0,
            },
            "purchases": {
                "count": purchases.count if purchases else 0,
                "neto": float(purchases.neto) if purchases else 0.0,
                "iva": iva_credito,
                "total": float(purchases.total) if purchases else 0.0,
            },
            "iva_debito_fiscal": iva_debito,
            "iva_credito_fiscal": iva_credito,
            "iva_neto": iva_neto,
            "previous_month_credit": previous_month_credit,
            "monthly_tax": monthly_tax,
            "iva_a_pagar": monthly_tax,  # Keep for backward compatibility
            "total_documents": (sales.count if sales else 0) + (purchases.count if purchases else 0),
        }

    def _empty_iva_summary(self) -> dict[str, Any]:
        """Return empty IVA summary structure."""
        return {
            "sales": {"count": 0, "neto": 0.0, "iva": 0.0, "total": 0.0},
            "purchases": {"count": 0, "neto": 0.0, "iva": 0.0, "total": 0.0},
            "iva_debito_fiscal": 0.0,
            "iva_credito_fiscal": 0.0,
            "iva_neto": 0.0,
            "previous_month_credit": None,
            "monthly_tax": 0.0,
            "iva_a_pagar": 0.0,
            "total_documents": 0,
        }

    def _extract_period_from_message(self, message: str) -> dict[str, int]:
        """Extract period (year/month) from message, default to current month."""
        import re

        # Default to current month
        now = datetime.now()
        year = now.year
        month = now.month

        # Try to find year and month in message
        # Pattern: YYYY-MM or YYYY/MM
        match = re.search(r"(\d{4})[-/](\d{1,2})", message)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))

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

        # Get previous month credit info
        previous_credit = iva_data.get('previous_month_credit')
        iva_neto = iva_data.get('iva_neto', iva_data['iva_debito_fiscal'] - iva_data['iva_credito_fiscal'])
        monthly_tax = iva_data.get('monthly_tax', 0.0)

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
            f"IVA Neto = IVA Cobrado - IVA Pagado",
            f"IVA Neto = ${iva_data['iva_debito_fiscal']:,.0f} - ${iva_data['iva_credito_fiscal']:,.0f}",
            f"IVA Neto = ${iva_neto:,.0f}",
            "",
        ]

        if previous_credit is not None:
            lines.extend([
                f"Crédito Mes Anterior (código 077 del F29): ${previous_credit:,.0f}",
                "",
                f"Impuesto Mensual = MAX(0, IVA Neto - Crédito Mes Anterior)",
                f"Impuesto Mensual = MAX(0, ${iva_neto:,.0f} - ${previous_credit:,.0f})",
                f"Impuesto Mensual = ${monthly_tax:,.0f}",
            ])
        else:
            lines.extend([
                f"Crédito Mes Anterior: No disponible (no se encontró F29 del mes anterior)",
                "",
                f"Impuesto Mensual = MAX(0, IVA Neto - Crédito Mes Anterior)",
                f"Impuesto Mensual = MAX(0, ${iva_neto:,.0f} - $0)",
                f"Impuesto Mensual = ${monthly_tax:,.0f}",
            ])

        lines.extend([
            "```",
            "",
            "**NOTA:** El crédito del mes anterior se obtiene del código 077 (remanente) del F29 del mes anterior.",
            "Si el resultado es negativo, significa que hay un remanente a favor que se arrastra al próximo mes.",
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

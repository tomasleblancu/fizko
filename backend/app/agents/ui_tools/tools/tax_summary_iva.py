"""UI Tool for Tax Summary IVA component."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.models import Company, PurchaseDocument, SalesDocument
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

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=full_data,
                metadata={
                    "period": f"{period['year']}-{period['month']:02d}",
                    "iva_to_pay": iva_data["iva_a_pagar"],
                    "has_documents": iva_data["total_documents"] > 0,
                },
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

        # Get purchases summary (IVA crédito)
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

        # Calculate IVA
        iva_debito = float(sales.iva) if sales else 0.0
        iva_credito = float(purchases.iva) if purchases else 0.0
        iva_a_pagar = max(0, iva_debito - iva_credito)

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
            "iva_a_pagar": iva_a_pagar,
            "total_documents": (sales.count if sales else 0) + (purchases.count if purchases else 0),
        }

    def _empty_iva_summary(self) -> dict[str, Any]:
        """Return empty IVA summary structure."""
        return {
            "sales": {"count": 0, "neto": 0.0, "iva": 0.0, "total": 0.0},
            "purchases": {"count": 0, "neto": 0.0, "iva": 0.0, "total": 0.0},
            "iva_debito_fiscal": 0.0,
            "iva_credito_fiscal": 0.0,
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

        lines = [
            "## 💰 CONTEXTO: Cálculo de IVA",
            "",
            f"**{data['business_name']}** (RUT: {data['rut']})",
            f"**Período:** {month_name.title()} {period['year']}",
            "",
            "### 📤 Débito Fiscal (Ventas)",
            f"- **{sales['count']} documentos** emitidos",
            f"- Monto Neto: ${sales['neto']:,.0f}",
            f"- **IVA Débito Fiscal: ${sales['iva']:,.0f}**",
            f"- Monto Total: ${sales['total']:,.0f}",
            "",
            "### 📥 Crédito Fiscal (Compras)",
            f"- **{purchases['count']} documentos** recibidos",
            f"- Monto Neto: ${purchases['neto']:,.0f}",
            f"- **IVA Crédito Fiscal: ${purchases['iva']:,.0f}**",
            f"- Monto Total: ${purchases['total']:,.0f}",
            "",
            "### 🧮 Cálculo del IVA a Pagar",
            "```",
            f"IVA a Pagar = Débito Fiscal - Crédito Fiscal",
            f"IVA a Pagar = ${iva_data['iva_debito_fiscal']:,.0f} - ${iva_data['iva_credito_fiscal']:,.0f}",
            f"IVA a Pagar = ${iva_data['iva_a_pagar']:,.0f}",
            "```",
            "",
        ]

        lines.append("")
        lines.append("---")
        lines.append("")

        if iva_data["total_documents"] == 0:
            lines.append("💡 **INSTRUCCIONES PARA EL AGENTE:**")
            lines.append("- Informa de forma breve que no hay documentos para este período")
            lines.append("- **NO llames a herramientas adicionales**")
            lines.append("- Pregunta al usuario qué le gustaría saber sobre el IVA")
        else:
            lines.append("💡 **INSTRUCCIONES PARA EL AGENTE:**")
            lines.append("- Responde de forma **breve y directa** con el resumen de IVA del período")
            lines.append("- **NO llames a herramientas adicionales** - toda la información necesaria ya está arriba")
            lines.append("- Termina tu respuesta preguntando al usuario qué le gustaría saber sobre este cálculo de IVA")

        lines.append("")
        return "\n".join(lines)

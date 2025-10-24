"""UI Tool for Tax Summary Expenses component."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.models import Company, Contact, PurchaseDocument
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class TaxSummaryExpensesTool(BaseUITool):
    """
    UI Tool for Tax Summary Expenses component.

    When a user clicks on the expenses (gastos) amount,
    this tool pre-loads:
    - Total expenses for the period
    - Document breakdown by type
    - Top 5 providers by amount
    - Comparison with previous period

    This allows the agent to immediately provide detailed
    expense analysis without needing additional queries.
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

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process expenses summary interaction and load relevant data."""

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
            # Get current period
            period = self._extract_period_from_message(context.user_message)

            # Get company info
            company_data = await self._get_company_info(context.db, context.company_id)
            if not company_data:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se encontró información de la empresa",
                )

            # Get expenses summary
            expenses_data = await self._get_expenses_summary(
                context.db,
                context.company_id,
                period["year"],
                period["month"],
            )

            # Get top providers
            top_providers = await self._get_top_providers(
                context.db,
                context.company_id,
                period["year"],
                period["month"],
                limit=5,
            )

            # Combine data
            full_data = {
                **company_data,
                "expenses_data": expenses_data,
                "top_providers": top_providers,
                "period": period,
            }

            # Format context text
            context_text = self._format_expenses_context(full_data)

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=full_data,
                metadata={
                    "period": f"{period['year']}-{period['month']:02d}",
                    "total_expenses": expenses_data["total_expenses"],
                    "document_count": expenses_data["total_documents"],
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing expenses summary: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar resumen de gastos: {str(e)}",
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

    async def _get_expenses_summary(
        self,
        db: AsyncSession,
        company_id: str,
        year: int,
        month: int,
    ) -> dict[str, Any]:
        """Get expenses summary for a specific period."""

        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return {"total_expenses": 0.0, "total_documents": 0, "by_type": []}

        # Date range
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        # Get total expenses
        total_stmt = select(
            func.count(PurchaseDocument.id).label("count"),
            func.coalesce(func.sum(PurchaseDocument.total_amount), 0).label("total"),
        ).where(
            PurchaseDocument.company_id == company_uuid,
            PurchaseDocument.issue_date >= start_date,
            PurchaseDocument.issue_date < end_date,
        )

        total_result = await db.execute(total_stmt)
        total_row = total_result.first()

        # Get breakdown by document type
        by_type_stmt = select(
            PurchaseDocument.document_type,
            func.count(PurchaseDocument.id).label("count"),
            func.coalesce(func.sum(PurchaseDocument.total_amount), 0).label("total"),
        ).where(
            PurchaseDocument.company_id == company_uuid,
            PurchaseDocument.issue_date >= start_date,
            PurchaseDocument.issue_date < end_date,
        ).group_by(PurchaseDocument.document_type)

        by_type_result = await db.execute(by_type_stmt)
        by_type_data = [
            {
                "tipo": row.document_type or "Sin tipo",
                "count": row.count,
                "total": float(row.total),
            }
            for row in by_type_result
        ]

        return {
            "total_expenses": float(total_row.total) if total_row else 0.0,
            "total_documents": total_row.count if total_row else 0,
            "by_type": by_type_data,
        }

    async def _get_top_providers(
        self,
        db: AsyncSession,
        company_id: str,
        year: int,
        month: int,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get top providers by expenses for the period."""

        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return []

        # Date range
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        # Query top providers
        stmt = (
            select(
                Contact.business_name,
                Contact.rut,
                func.count(PurchaseDocument.id).label("doc_count"),
                func.coalesce(func.sum(PurchaseDocument.total_amount), 0).label("total"),
            )
            .join(Contact, PurchaseDocument.contact_id == Contact.id)
            .where(
                PurchaseDocument.company_id == company_uuid,
                PurchaseDocument.issue_date >= start_date,
                PurchaseDocument.issue_date < end_date,
            )
            .group_by(Contact.id, Contact.business_name, Contact.rut)
            .order_by(func.sum(PurchaseDocument.total_amount).desc())
            .limit(limit)
        )

        result = await db.execute(stmt)
        return [
            {
                "name": row.business_name,
                "rut": row.rut,
                "document_count": row.doc_count,
                "total": float(row.total),
            }
            for row in result
        ]

    def _extract_period_from_message(self, message: str) -> dict[str, int]:
        """Extract period (year/month) from message, default to current month."""
        import re

        now = datetime.now()
        year = now.year
        month = now.month

        match = re.search(r"(\d{4})[-/](\d{1,2})", message)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))

        return {"year": year, "month": month}

    def _format_expenses_context(self, data: dict[str, Any]) -> str:
        """Format expenses data into human-readable context for agent."""

        period = data["period"]
        month_names = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        month_name = month_names[period["month"] - 1]

        expenses_data = data["expenses_data"]
        top_providers = data["top_providers"]

        lines = [
            "## 📉 CONTEXTO: Análisis de Gastos",
            "",
            f"**{data['business_name']}** (RUT: {data['rut']})",
            f"**Período:** {month_name.title()} {period['year']}",
            "",
            "### 💸 Resumen de Gastos",
            f"- **Total Gastos: ${expenses_data['total_expenses']:,.0f}**",
            f"- **{expenses_data['total_documents']} documentos** recibidos",
            "",
        ]

        # Document breakdown
        if expenses_data["by_type"]:
            lines.append("### 📄 Desglose por Tipo de Documento")
            for doc_type in expenses_data["by_type"]:
                lines.append(
                    f"- {doc_type['tipo']}: {doc_type['count']} docs, "
                    f"${doc_type['total']:,.0f}"
                )
            lines.append("")

        # Top providers
        if top_providers:
            lines.append("### 🏢 Top 5 Proveedores del Período")
            for i, provider in enumerate(top_providers, 1):
                lines.append(
                    f"{i}. **{provider['name']}** (RUT: {provider['rut']}): "
                    f"${provider['total']:,.0f} ({provider['document_count']} docs)"
                )
            lines.append("")

        lines.append("")
        lines.append("---")
        lines.append("")

        if expenses_data["total_documents"] == 0:
            lines.append("💡 **INSTRUCCIONES PARA EL AGENTE:**")
            lines.append("- Informa de forma breve que no hay documentos de compra para este período")
            lines.append("- **NO llames a herramientas adicionales**")
            lines.append("- Pregunta al usuario qué le gustaría saber sobre los gastos")
        else:
            lines.append("💡 **INSTRUCCIONES PARA EL AGENTE:**")
            lines.append("- Responde de forma **breve y directa** con el resumen de gastos del período")
            lines.append("- **NO llames a herramientas adicionales** - toda la información necesaria ya está arriba")
            lines.append("- Termina tu respuesta preguntando al usuario qué le gustaría saber sobre estos gastos")

        lines.append("")
        return "\n".join(lines)

"""UI Tool for Tax Summary Revenue component."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.models import Company, Contact, SalesDocument
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class TaxSummaryRevenueTool(BaseUITool):
    """
    UI Tool for Tax Summary Revenue component.

    When a user clicks on the revenue (ingresos) amount,
    this tool pre-loads:
    - Total revenue for the period
    - Document breakdown by type
    - Top 5 clients by amount
    - Comparison with previous period

    This allows the agent to immediately provide detailed
    revenue analysis without needing additional queries.
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

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process revenue summary interaction and load relevant data."""

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

            # Get revenue summary
            revenue_data = await self._get_revenue_summary(
                context.db,
                context.company_id,
                period["year"],
                period["month"],
            )

            # Get top clients
            top_clients = await self._get_top_clients(
                context.db,
                context.company_id,
                period["year"],
                period["month"],
                limit=5,
            )

            # Combine data
            full_data = {
                **company_data,
                "revenue_data": revenue_data,
                "top_clients": top_clients,
                "period": period,
            }

            # Format context text
            context_text = self._format_revenue_context(full_data)

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=full_data,
                metadata={
                    "period": f"{period['year']}-{period['month']:02d}",
                    "total_revenue": revenue_data["total_revenue"],
                    "document_count": revenue_data["total_documents"],
                },
            )

        except Exception as e:
            self.logger.error(f"Error processing revenue summary: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar resumen de ingresos: {str(e)}",
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

    async def _get_revenue_summary(
        self,
        db: AsyncSession,
        company_id: str,
        year: int,
        month: int,
    ) -> dict[str, Any]:
        """Get revenue summary for a specific period."""

        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return {"total_revenue": 0.0, "total_documents": 0, "by_type": []}

        # Date range
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        # Get total revenue
        total_stmt = select(
            func.count(SalesDocument.id).label("count"),
            func.coalesce(func.sum(SalesDocument.total_amount), 0).label("total"),
        ).where(
            SalesDocument.company_id == company_uuid,
            SalesDocument.issue_date >= start_date,
            SalesDocument.issue_date < end_date,
        )

        total_result = await db.execute(total_stmt)
        total_row = total_result.first()

        # Get breakdown by document type
        by_type_stmt = select(
            SalesDocument.document_type,
            func.count(SalesDocument.id).label("count"),
            func.coalesce(func.sum(SalesDocument.total_amount), 0).label("total"),
        ).where(
            SalesDocument.company_id == company_uuid,
            SalesDocument.issue_date >= start_date,
            SalesDocument.issue_date < end_date,
        ).group_by(SalesDocument.document_type)

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
            "total_revenue": float(total_row.total) if total_row else 0.0,
            "total_documents": total_row.count if total_row else 0,
            "by_type": by_type_data,
        }

    async def _get_top_clients(
        self,
        db: AsyncSession,
        company_id: str,
        year: int,
        month: int,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get top clients by revenue for the period."""

        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return []

        # Date range
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        # Query top clients
        stmt = (
            select(
                Contact.business_name,
                Contact.rut,
                func.count(SalesDocument.id).label("doc_count"),
                func.coalesce(func.sum(SalesDocument.total_amount), 0).label("total"),
            )
            .join(Contact, SalesDocument.contact_id == Contact.id)
            .where(
                SalesDocument.company_id == company_uuid,
                SalesDocument.issue_date >= start_date,
                SalesDocument.issue_date < end_date,
            )
            .group_by(Contact.id, Contact.business_name, Contact.rut)
            .order_by(func.sum(SalesDocument.total_amount).desc())
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

    def _format_revenue_context(self, data: dict[str, Any]) -> str:
        """Format revenue data into human-readable context for agent."""

        period = data["period"]
        month_names = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        month_name = month_names[period["month"] - 1]

        revenue_data = data["revenue_data"]
        top_clients = data["top_clients"]

        lines = [
            "## 📈 CONTEXTO: Análisis de Ingresos",
            "",
            f"**{data['business_name']}** (RUT: {data['rut']})",
            f"**Período:** {month_name.title()} {period['year']}",
            "",
            "### 💰 Resumen de Ingresos",
            f"- **Total Ingresos: ${revenue_data['total_revenue']:,.0f}**",
            f"- **{revenue_data['total_documents']} documentos** emitidos",
            "",
        ]

        # Document breakdown
        if revenue_data["by_type"]:
            lines.append("### 📄 Desglose por Tipo de Documento")
            for doc_type in revenue_data["by_type"]:
                lines.append(
                    f"- {doc_type['tipo']}: {doc_type['count']} docs, "
                    f"${doc_type['total']:,.0f}"
                )
            lines.append("")

        # Top clients
        if top_clients:
            lines.append("### 👥 Top 5 Clientes del Período")
            for i, client in enumerate(top_clients, 1):
                lines.append(
                    f"{i}. **{client['name']}** (RUT: {client['rut']}): "
                    f"${client['total']:,.0f} ({client['document_count']} docs)"
                )
            lines.append("")

        lines.append("")
        lines.append("---")
        lines.append("")

        if revenue_data["total_documents"] == 0:
            lines.append("💡 **INSTRUCCIONES PARA EL AGENTE:**")
            lines.append("- Informa de forma breve que no hay documentos de venta para este período")
            lines.append("- **NO llames a herramientas adicionales**")
            lines.append("- Pregunta al usuario qué le gustaría saber sobre los ingresos")
        else:
            lines.append("💡 **INSTRUCCIONES PARA EL AGENTE:**")
            lines.append("- Responde de forma **breve y directa** con el resumen de ingresos del período")
            lines.append("- **NO llames a herramientas adicionales** - toda la información necesaria ya está arriba")
            lines.append("- Termina tu respuesta preguntando al usuario qué le gustaría saber sobre estos ingresos")

        lines.append("")
        return "\n".join(lines)

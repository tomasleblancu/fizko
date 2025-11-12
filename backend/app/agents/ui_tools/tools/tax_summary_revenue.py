"""UI Tool for Tax Summary Revenue component."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, Contact, SalesDocument
from app.repositories.tax import TaxSummaryRepository
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
        """
        Get revenue summary for a specific period using TaxSummaryRepository.

        This ensures consistency with the /api/tax-summary endpoint.
        """
        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return {"total_revenue": 0.0, "total_documents": 0, "by_type": []}

        try:
            # Use TaxSummaryRepository for consistent calculation
            repo = TaxSummaryRepository(db)
            period_str = f"{year}-{month:02d}"

            tax_summary = await repo.get_tax_summary(company_uuid, period_str)

            # Get breakdown by document type (not in TaxSummary, needs direct query)
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date()
            else:
                end_date = datetime(year, month + 1, 1).date()

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
                "total_revenue": tax_summary.total_revenue,
                "total_documents": len(by_type_data) if by_type_data else 0,  # Approximation
                "by_type": by_type_data,
            }

        except Exception as e:
            logger.error(f"Error getting revenue summary: {e}", exc_info=True)
            return {"total_revenue": 0.0, "total_documents": 0, "by_type": []}

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

    def _parse_period_from_entity_id(self, entity_id: str | None) -> dict[str, int]:
        """
        Parse period from entity_id (format: "YYYY-MM" or ISO datetime).

        Args:
            entity_id: Period string in format "YYYY-MM" or ISO datetime (e.g., "2025-10-01T00:00:00") or None

        Returns:
            Dict with year and month integers
        """
        now = datetime.now()
        year = now.year
        month = now.month

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
                logger.warning(f"Failed to parse period from entity_id '{entity_id}': {e}")

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

        return "\n".join(lines)

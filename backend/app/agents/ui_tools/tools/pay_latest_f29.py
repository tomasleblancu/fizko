"""UI Tool for Pay Latest F29 action."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.models import Form29SIIDownload
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
    - Fetches the latest F29 form for the company
    - Shows a step-by-step widget guide to pay on SII
    - Provides context about the F29 being paid

    This gives the agent immediate context about the latest F29
    and displays a helpful payment flow guide.
    """

    @property
    def component_name(self) -> str:
        return "pay_latest_f29"

    @property
    def description(self) -> str:
        return "Shows step-by-step guide to pay the latest F29 on SII"

    @property
    def domain(self) -> str:
        return "tax"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario quiere pagar el F29."""
        return """
## 💡 INSTRUCCIONES: Pagar F29

El usuario quiere pagar su F29 más reciente en el SII.

**Tu objetivo:**
- Confirmar el F29 que se va a pagar (período y monto)
- Ya se mostró el widget con el paso a paso arriba
- Sé breve y directo (máximo 2-3 líneas)
- Ofrece ayuda adicional si la necesita

**Formato de respuesta:**
1. Confirma el F29: "Perfecto, aquí está la guía para pagar tu F29 de [PERÍODO]."
2. Menciona el monto a pagar si está disponible
3. Ofrece ayuda: "¿Necesitas ayuda con algún paso?"

**Evita:**
- Explicar cada paso manualmente (ya está en el widget)
- Respuestas largas
- **NO llames a herramientas adicionales**
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process pay latest F29 action and show payment flow guide."""

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
            # Get latest F29 for company
            latest_f29 = await self._get_latest_f29(
                context.db,
                context.company_id,
            )

            if not latest_f29:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error="No se encontraron formularios F29 para esta empresa",
                )

            # Format context text for agent
            context_text = self._format_payment_context(latest_f29)

            # Create payment flow widget
            widget = create_f29_payment_flow_widget(
                title=f"Paso a paso: pagar F29 {latest_f29['period_display']}",
                url="https://zeusr.sii.cl/AUT2000/InicioAutenticacion/IngresoRutClave.html?https://www4.sii.cl/propuestaf29ui/#/default",
            )

            widget_copy_text = f29_payment_flow_widget_copy_text(
                title=f"Paso a paso: pagar F29 {latest_f29['period_display']}",
                url="https://zeusr.sii.cl/AUT2000/InicioAutenticacion/IngresoRutClave.html?https://www4.sii.cl/propuestaf29ui/#/default",
            )

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=latest_f29,
                metadata={
                    "form_folio": latest_f29.get("folio"),
                    "form_status": latest_f29.get("status"),
                    "period": latest_f29.get("period_display"),
                    "amount_cents": latest_f29.get("amount_cents"),
                },
                widget=widget,
                widget_copy_text=widget_copy_text,
            )

        except Exception as e:
            self.logger.error(f"Error processing pay latest F29: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar información del F29: {str(e)}",
            )

    async def _get_latest_f29(
        self,
        db: AsyncSession,
        company_id: str,
    ) -> dict[str, Any] | None:
        """Fetch the latest F29 form for company."""

        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return None

        # Get latest F29 (order by period year DESC, period month DESC)
        stmt = (
            select(Form29SIIDownload)
            .where(Form29SIIDownload.company_id == company_uuid)
            .where(Form29SIIDownload.period_month > 0)  # Exclude annual forms
            .order_by(
                desc(Form29SIIDownload.period_year),
                desc(Form29SIIDownload.period_month)
            )
            .limit(1)
        )

        result = await db.execute(stmt)
        form = result.scalar_one_or_none()

        if not form:
            return None

        # Determine form type
        form_type = "Anual" if form.period_month == 0 else "Mensual"

        return {
            "id": str(form.id),
            "folio": form.sii_folio,
            "sii_id_interno": form.sii_id_interno,
            "period_year": form.period_year,
            "period_month": form.period_month,
            "period_display": form.period_display,
            "form_type": form_type,
            "contributor_rut": form.contributor_rut,
            "submission_date": form.submission_date.isoformat() if form.submission_date else None,
            "status": form.status,
            "amount_cents": form.amount_cents,
            "amount_formatted": f"${form.amount_cents:,.0f}",
            "pdf_download_status": form.pdf_download_status,
            "has_pdf": form.has_pdf,
            "pdf_url": form.pdf_storage_url,
            "can_download_pdf": form.can_download_pdf,
        }

    def _format_payment_context(self, form_data: dict[str, Any]) -> str:
        """Format F29 payment context for agent."""

        status_emoji = {
            "Vigente": "✅",
            "Rectificado": "🔄",
            "Anulado": "❌",
        }.get(form_data["status"], "📄")

        lines = [
            "## 💳 CONTEXTO: Pagar F29",
            "",
            f"**Período**: {form_data['period_display']} ({form_data['form_type']})",
            f"**Folio**: {form_data['folio']}",
            f"**Estado**: {status_emoji} {form_data['status']}",
            f"**Monto**: {form_data['amount_formatted']}",
        ]

        if form_data.get("submission_date"):
            lines.append(f"**Fecha de presentación**: {form_data['submission_date']}")

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

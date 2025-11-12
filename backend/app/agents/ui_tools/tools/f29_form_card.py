"""UI Tool for F29 Form Card component."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Form29SIIDownload, Form29, Company
from ...tools.widgets.builders import create_f29_summary_widget, f29_summary_widget_copy_text
from ..core.base import BaseUITool, UIToolContext, UIToolResult
from ..core.registry import ui_tool_registry

logger = logging.getLogger(__name__)


@ui_tool_registry.register
class F29FormCardTool(BaseUITool):
    """
    UI Tool for F29 Form Card component.

    When a user clicks or interacts with an F29 form card in the frontend,
    this tool pre-loads:
    - F29 form basic information (folio, period, status)
    - PDF download status and availability
    - Submission details
    - Amount information

    This gives the agent immediate context about the form without
    needing to call additional tools.
    """

    @property
    def component_name(self) -> str:
        return "f29_form_card"

    @property
    def description(self) -> str:
        return "Loads F29 form information when user views a form card"

    @property
    def domain(self) -> str:
        return "tax"

    @property
    def agent_instructions(self) -> str:
        """Instrucciones específicas cuando el usuario ve una tarjeta de formulario F29."""
        return """
## 💡 INSTRUCCIONES: Tarjeta de Formulario F29

El usuario está viendo la ficha de un formulario F29 específico.

**Tu objetivo:**
- Responde preguntas sobre ESTE formulario F29 (detalles, estado, PDF)
- Ya se mostró el widget con el desglose del F29 arriba
- Sé breve y directo (máximo 2-3 líneas)

**Formato de respuesta:**
1. Saluda brevemente y menciona el período del F29
2. Pregunta qué le gustaría saber o hacer

**Evita:**
- Temas generales no relacionados con este formulario
- Respuestas largas
- Describir manualmente los números (ya están en el widget)
- **NO llames a herramientas adicionales**
""".strip()

    async def process(self, context: UIToolContext) -> UIToolResult:
        """Process F29 form card interaction and load relevant data."""

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
            # Priority 1: Get form folio from entity_id (frontend UI component click)
            form_folio = context.additional_data.get("entity_id") if context.additional_data else None

            # Priority 2: Fallback to form_folio in additional_data
            if not form_folio:
                form_folio = context.additional_data.get("form_folio") if context.additional_data else None

            # Get form data
            form_data = await self._get_form_data(
                context.db,
                context.company_id,
                form_folio,
            )

            if not form_data:
                return UIToolResult(
                    success=False,
                    context_text="",
                    error=f"No se encontró el formulario F29 con folio {form_folio}" if form_folio else "No se especificó un folio de formulario",
                )

            # Get company info for widget
            company_info = await self._get_company_info(context.db, context.company_id)

            # Format context text for agent
            context_text = self._format_form_context(form_data)

            # Create widget if we have detailed breakdown data
            widget = None
            widget_copy_text = None

            if form_data.get("has_detailed_breakdown") and company_info:
                # Format amounts for widget
                total_determinado_fmt = f"CLP ${form_data['total_determinado']:,.0f}"
                total_a_pagar_fmt = f"CLP ${form_data['total_determinado']:,.0f}"  # Same as total_determinado

                # All F29 forms are considered paid
                is_paid = True

                widget = create_f29_summary_widget(
                    company=company_info["business_name"],
                    rut=company_info["rut"],
                    periodo=form_data["period_display"],
                    folio=form_data["folio"],
                    total_determinado=total_determinado_fmt,
                    total_a_pagar_plazo=total_a_pagar_fmt,
                    estado=form_data["status"],
                    fecha_presentacion=form_data.get("submission_date", "N/A"),
                    tipo_declaracion="Primitiva",  # Default, could be extracted from extra_data
                    is_paid=is_paid,
                )

                widget_copy_text = f29_summary_widget_copy_text(
                    company=company_info["business_name"],
                    rut=company_info["rut"],
                    periodo=form_data["period_display"],
                    folio=form_data["folio"],
                    total_determinado=total_determinado_fmt,
                    total_a_pagar_plazo=total_a_pagar_fmt,
                    estado=form_data["status"],
                    fecha_presentacion=form_data.get("submission_date", "N/A"),
                    tipo_declaracion="Primitiva",
                    is_paid=is_paid,
                )

            return UIToolResult(
                success=True,
                context_text=context_text,
                structured_data=form_data,
                metadata={
                    "form_folio": form_data.get("folio"),
                    "form_status": form_data.get("status"),
                    "has_pdf": form_data.get("has_pdf"),
                    "period": form_data.get("period_display"),
                },
                widget=widget,
                widget_copy_text=widget_copy_text,
            )

        except Exception as e:
            self.logger.error(f"Error processing F29 form card: {e}", exc_info=True)
            return UIToolResult(
                success=False,
                context_text="",
                error=f"Error al cargar información del formulario F29: {str(e)}",
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

    async def _get_form_data(
        self,
        db: AsyncSession,
        company_id: str,
        form_folio: str | None = None,
    ) -> dict[str, Any] | None:
        """Fetch F29 form data from database."""

        company_uuid = self._safe_get_uuid(company_id)
        if not company_uuid:
            return None

        # Build query
        query = select(Form29SIIDownload).where(Form29SIIDownload.company_id == company_uuid)

        if form_folio:
            query = query.where(Form29SIIDownload.sii_folio == form_folio)
        else:
            # If no folio specified, just return None
            return None

        result = await db.execute(query)
        form = result.scalar_one_or_none()

        if not form:
            return None

        # Determine form type (monthly or annual)
        form_type = "Anual" if form.period_month == 0 else "Mensual"

        # Base data from SII download
        form_data = {
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
            "is_linked_to_local_form": form.is_linked_to_local_form,
            "created_at": form.created_at.isoformat() if form.created_at else None,
        }

        # Extract F29 data from extra_data if available
        if form.extra_data and "f29_data" in form.extra_data:
            f29_data = form.extra_data["f29_data"]

            # Check if we have the necessary codes
            codes = f29_data.get("codes", {})
            grouped = f29_data.get("grouped", {})
            summary = f29_data.get("summary", {})
            header = f29_data.get("header", {})

            if codes or summary:
                form_data["has_detailed_breakdown"] = True
                form_data["f29_codes"] = codes
                form_data["f29_grouped"] = grouped
                form_data["f29_summary"] = summary
                form_data["f29_header"] = header

                # Extract key values for widgets
                form_data["total_debitos"] = summary.get("total_debitos", 0)
                form_data["total_creditos"] = summary.get("total_creditos", 0)
                form_data["iva_determinado"] = summary.get("iva_determinado", 0)
                form_data["total_determinado"] = summary.get("total_determinado", 0)
                form_data["ppm_neto"] = summary.get("ppm_neto", 0)
                form_data["remanente_credito"] = codes.get("077", {}).get("value", 0)
                form_data["remanente_mes_anterior"] = codes.get("504", {}).get("value", 0)
            else:
                form_data["has_detailed_breakdown"] = False
        else:
            form_data["has_detailed_breakdown"] = False

        return form_data

    def _format_form_context(self, form_data: dict[str, Any]) -> str:
        """Format F29 form data into human-readable context for agent."""

        status_emoji = {
            "Vigente": "✅",
            "Rectificado": "🔄",
            "Anulado": "❌",
        }.get(form_data["status"], "📄")

        pdf_status_text = {
            "pending": "⏳ Pendiente",
            "downloaded": "✅ Descargado",
            "error": "❌ Error al descargar",
        }.get(form_data["pdf_download_status"], form_data["pdf_download_status"])

        lines = [
            "## 📋 CONTEXTO: Formulario F29",
            "",
            f"**Folio**: {form_data['folio']}",
            f"**Periodo**: {form_data['period_display']} ({form_data['form_type']})",
            f"**Estado**: {status_emoji} {form_data['status']}",
            f"**Monto**: {form_data['amount_formatted']}",
        ]

        if form_data.get("submission_date"):
            lines.append(f"**Fecha de presentación**: {form_data['submission_date']}")

        # PDF status
        lines.append("")
        lines.append(f"**Estado del PDF**: {pdf_status_text}")

        if form_data["has_pdf"] and form_data.get("pdf_url"):
            lines.append(f"**URL del PDF**: {form_data['pdf_url']}")
        elif not form_data["can_download_pdf"]:
            lines.append("⚠️ Este formulario no tiene ID interno del SII para descargar PDF")

        # Additional info
        if form_data.get("sii_id_interno"):
            lines.append("")
            lines.append(f"**ID Interno SII**: {form_data['sii_id_interno']}")

        if form_data["is_linked_to_local_form"]:
            lines.append("")
            lines.append("🔗 Este formulario está vinculado a un cálculo local")

        # Add detailed breakdown info if available
        if form_data.get("has_detailed_breakdown"):
            lines.append("")
            lines.append("## 📊 Desglose Detallado")
            lines.append("")
            lines.append("✅ **Widget mostrado arriba con el resumen del F29**")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("💡 **INSTRUCCIONES:**")
        lines.append("- Ya se mostró el widget con los detalles del F29 arriba")
        lines.append("- Responde en máximo 2-3 líneas")
        lines.append("- NO repitas la información del widget")
        lines.append("- Pregunta si necesita más información")
        lines.append("- **NO llames a herramientas adicionales**")

        return "\n".join(lines)

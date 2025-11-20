"""
Context Builder - Simplified for Backend V2.

Stateless version that formats context without database dependencies.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds context for agent execution (stateless version).

    Unlike the full backend version, this does NOT:
    - Load company info from database
    - Cache company information
    - Load UI tool context

    This version only formats provided data.
    """

    @staticmethod
    def format_company_context_text(company_info: Dict[str, Any]) -> str:
        """
        Format company info as context text for agent.

        Args:
            company_info: Company information dict

        Returns:
            Formatted context string

        Example:
            ```python
            company_info = {
                "rut": "77794858-k",
                "razon_social": "EMPRESA DEMO SPA",
                "actividad_economica": "Servicios de software"
            }
            context = ContextBuilder.format_company_context_text(company_info)
            ```
        """
        if not company_info:
            return ""

        lines = ["# Información de la Empresa"]

        # Basic info
        if rut := company_info.get("rut"):
            lines.append(f"- RUT: {rut}")

        if razon_social := company_info.get("razon_social"):
            lines.append(f"- Razón Social: {razon_social}")

        if nombre_fantasia := company_info.get("nombre_fantasia"):
            lines.append(f"- Nombre Fantasía: {nombre_fantasia}")

        # Activity
        if actividad := company_info.get("actividad_economica"):
            lines.append(f"- Actividad Económica: {actividad}")

        # Contact info
        if direccion := company_info.get("direccion"):
            comuna = company_info.get("comuna", "")
            if comuna:
                lines.append(f"- Dirección: {direccion}, {comuna}")
            else:
                lines.append(f"- Dirección: {direccion}")

        if email := company_info.get("email"):
            lines.append(f"- Email: {email}")

        if telefono := company_info.get("telefono"):
            lines.append(f"- Teléfono: {telefono}")

        # Contributor type
        if tipo := company_info.get("tipo_contribuyente"):
            lines.append(f"- Tipo de Contribuyente: {tipo}")

        # Legal representative
        if rep_legal := company_info.get("representante_legal"):
            if isinstance(rep_legal, dict) and rep_legal:
                nombre = rep_legal.get("nombre", "")
                rut_rep = rep_legal.get("rut", "")
                if nombre:
                    lines.append(f"- Representante Legal: {nombre}" + (f" (RUT: {rut_rep})" if rut_rep else ""))

        # Activities (if multiple)
        if actividades := company_info.get("actividades"):
            if isinstance(actividades, list) and len(actividades) > 1:
                lines.append("- Actividades:")
                for act in actividades[:5]:  # Limit to first 5
                    if isinstance(act, dict):
                        cod = act.get("codigo", "")
                        desc = act.get("descripcion", "")
                        if desc:
                            lines.append(f"  - {desc}" + (f" ({cod})" if cod else ""))
                    elif isinstance(act, str):
                        lines.append(f"  - {act}")

        return "\n".join(lines)

    @staticmethod
    def format_sii_document_context(
        document_type: str,
        documents: list[Dict[str, Any]],
        max_documents: int = 10
    ) -> str:
        """
        Format SII documents as context text.

        Useful for providing recent documents to agents.

        Args:
            document_type: Type of document ("compras", "ventas", "f29", etc.)
            documents: List of document dicts
            max_documents: Maximum number of documents to include (default: 10)

        Returns:
            Formatted context string

        Example:
            ```python
            compras = [
                {"folio": "123", "rut_emisor": "12345678-9", "monto_total": 100000},
                {"folio": "124", "rut_emisor": "98765432-1", "monto_total": 50000},
            ]
            context = ContextBuilder.format_sii_document_context("compras", compras)
            ```
        """
        if not documents:
            return f"No hay documentos de {document_type} disponibles."

        doc_type_labels = {
            "compras": "Documentos de Compra",
            "ventas": "Documentos de Venta",
            "f29": "Formularios F29",
            "boletas_honorarios": "Boletas de Honorarios",
        }

        label = doc_type_labels.get(document_type, document_type.title())
        lines = [f"# {label} Recientes", ""]

        limited_docs = documents[:max_documents]

        for i, doc in enumerate(limited_docs, 1):
            lines.append(f"## Documento {i}")

            # Common fields
            if folio := doc.get("folio"):
                lines.append(f"- Folio: {folio}")

            if tipo_doc := doc.get("tipo_documento") or doc.get("tipo_dte"):
                lines.append(f"- Tipo: {tipo_doc}")

            if fecha := doc.get("fecha_emision") or doc.get("fecha"):
                lines.append(f"- Fecha: {fecha}")

            # Specific to compras/ventas
            if rut_emisor := doc.get("rut_emisor"):
                lines.append(f"- RUT Emisor: {rut_emisor}")

            if razon_social := doc.get("razon_social_emisor"):
                lines.append(f"- Emisor: {razon_social}")

            # Amounts
            if monto_neto := doc.get("monto_neto"):
                lines.append(f"- Monto Neto: ${monto_neto:,.0f}")

            if monto_iva := doc.get("monto_iva"):
                lines.append(f"- IVA: ${monto_iva:,.0f}")

            if monto_total := doc.get("monto_total"):
                lines.append(f"- Total: ${monto_total:,.0f}")

            lines.append("")

        if len(documents) > max_documents:
            lines.append(f"... y {len(documents) - max_documents} documentos más")

        return "\n".join(lines)

    @staticmethod
    def format_f29_context(f29_data: Dict[str, Any]) -> str:
        """
        Format F29 form data as context text.

        Args:
            f29_data: F29 form dictionary

        Returns:
            Formatted context string

        Example:
            ```python
            f29 = {
                "periodo": "2024-01",
                "total_a_pagar": 500000,
                "debito_fiscal": 1000000,
                "credito_fiscal": 500000
            }
            context = ContextBuilder.format_f29_context(f29)
            ```
        """
        if not f29_data:
            return "No hay datos de F29 disponibles."

        lines = ["# Formulario 29", ""]

        if periodo := f29_data.get("periodo"):
            lines.append(f"**Período**: {periodo}")

        if folio := f29_data.get("folio"):
            lines.append(f"**Folio**: {folio}")

        lines.append("")
        lines.append("## Montos")

        # IVA
        if debito := f29_data.get("debito_fiscal"):
            lines.append(f"- Débito Fiscal (IVA Ventas): ${debito:,.0f}")

        if credito := f29_data.get("credito_fiscal"):
            lines.append(f"- Crédito Fiscal (IVA Compras): ${credito:,.0f}")

        if iva_a_pagar := f29_data.get("iva_a_pagar"):
            lines.append(f"- **IVA a Pagar**: ${iva_a_pagar:,.0f}")

        # PPM
        if ppm := f29_data.get("ppm"):
            lines.append(f"- PPM (Impuesto Renta): ${ppm:,.0f}")

        # Total
        if total := f29_data.get("total_a_pagar"):
            lines.append("")
            lines.append(f"### **Total a Pagar**: ${total:,.0f}")

        # Status
        if estado := f29_data.get("estado"):
            lines.append("")
            lines.append(f"**Estado**: {estado}")

        if fecha_vencimiento := f29_data.get("fecha_vencimiento"):
            lines.append(f"**Vencimiento**: {fecha_vencimiento}")

        return "\n".join(lines)

    @staticmethod
    def build_agent_context(
        company_info: Optional[Dict[str, Any]] = None,
        recent_compras: Optional[list[Dict[str, Any]]] = None,
        recent_ventas: Optional[list[Dict[str, Any]]] = None,
        recent_f29: Optional[Dict[str, Any]] = None,
        custom_context: Optional[str] = None,
    ) -> str:
        """
        Build complete context for agent from various sources.

        This is a convenience method that combines multiple context pieces.

        Args:
            company_info: Company information
            recent_compras: Recent purchase documents
            recent_ventas: Recent sales documents
            recent_f29: Recent F29 form
            custom_context: Additional custom context text

        Returns:
            Combined context string

        Example:
            ```python
            context = ContextBuilder.build_agent_context(
                company_info={"rut": "77794858-k", "razon_social": "DEMO SPA"},
                recent_compras=[...],
                recent_f29={...}
            )
            ```
        """
        sections = []

        # Company info
        if company_info:
            company_text = ContextBuilder.format_company_context_text(company_info)
            if company_text:
                sections.append(company_text)

        # Recent compras
        if recent_compras:
            compras_text = ContextBuilder.format_sii_document_context("compras", recent_compras)
            sections.append(compras_text)

        # Recent ventas
        if recent_ventas:
            ventas_text = ContextBuilder.format_sii_document_context("ventas", recent_ventas)
            sections.append(ventas_text)

        # Recent F29
        if recent_f29:
            f29_text = ContextBuilder.format_f29_context(recent_f29)
            sections.append(f29_text)

        # Custom context
        if custom_context:
            sections.append(custom_context)

        return "\n\n---\n\n".join(sections) if sections else ""

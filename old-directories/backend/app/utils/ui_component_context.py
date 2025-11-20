"""
Utility to extract relevant context information from UI components.

This module helps extract contextual information when a message comes from
a UI component, enriching the agent's understanding without needing explicit tools.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_ui_component_context(
    ui_component: str | None,
    message: str,
    company_id: str | None = None,
) -> dict[str, Any]:
    """
    Extract relevant contextual information based on the UI component that triggered the message.

    Args:
        ui_component: Name of the UI component (e.g., "tax_summary_card", "revenue_chart")
        message: The user's message (may contain [UI:tool_name] prefix)
        company_id: Optional company ID for additional context

    Returns:
        Dictionary with extracted contextual information to pass to the agent
    """
    # If ui_component is null or None string, return empty context
    if not ui_component or ui_component == "null":
        return {}

    context: dict[str, Any] = {
        "ui_component": ui_component,
        "has_ui_context": True,
    }

    # Extract tool name from [UI:tool_name] prefix if present
    tool_name = None
    if message.startswith("[UI:"):
        end_idx = message.find("]")
        if end_idx != -1:
            tool_name = message[4:end_idx].strip()
            context["ui_tool"] = tool_name

    # Map UI components to their relevant context
    component_context_map = {
        "tax_summary_card": {
            "domain": "financial_overview",
            "relevant_data": ["tax_summary", "period_data", "iva_calculation"],
            "suggested_agents": ["monthly_taxes_agent", "documentos_tributarios_agent"],
            "context_hint": "Usuario está viendo el resumen de impuestos en el dashboard",
        },
        "revenue_chart": {
            "domain": "revenue_analysis",
            "relevant_data": ["sales_documents", "revenue_trends", "customer_data"],
            "suggested_agents": ["documentos_tributarios_agent"],
            "context_hint": "Usuario está analizando gráficos de ingresos",
        },
        "expenses_chart": {
            "domain": "expense_analysis",
            "relevant_data": ["purchase_documents", "expense_trends", "supplier_data"],
            "suggested_agents": ["documentos_tributarios_agent"],
            "context_hint": "Usuario está analizando gráficos de gastos",
        },
        "recent_documents": {
            "domain": "document_management",
            "relevant_data": ["sales_documents", "purchase_documents", "document_status"],
            "suggested_agents": ["documentos_tributarios_agent"],
            "context_hint": "Usuario está revisando documentos tributarios recientes",
        },
        "f29_form": {
            "domain": "tax_declaration",
            "relevant_data": ["f29_data", "tax_obligations", "payment_status"],
            "suggested_agents": ["monthly_taxes_agent"],
            "context_hint": "Usuario está trabajando con declaración F29",
        },
        "operacion_renta": {
            "domain": "annual_tax",
            "relevant_data": ["annual_tax_data", "f22_form", "tax_credits"],
            "suggested_agents": ["operacion_renta_agent"],
            "context_hint": "Usuario está revisando operación renta",
        },
        "payroll": {
            "domain": "remunerations",
            "relevant_data": ["employee_data", "payroll_records", "tax_withholdings"],
            "suggested_agents": ["remuneraciones_agent"],
            "context_hint": "Usuario está gestionando remuneraciones",
        },
        "tax_calendar_event": {
            "domain": "tax_calendar",
            "relevant_data": ["calendar_event", "event_template", "event_tasks", "compliance_status"],
            "suggested_agents": ["monthly_taxes_agent", "operacion_renta_agent"],
            "context_hint": "Usuario está consultando sobre una obligación tributaria específica del calendario",
        },
        "person_detail": {
            "domain": "payroll_management",
            "relevant_data": ["employee_data", "person_info", "payroll_history", "employment_status"],
            "suggested_agents": ["payroll_agent"],
            "context_hint": "Usuario está consultando sobre un colaborador/empleado específico",
        },
    }

    # Get component-specific context
    component_info = component_context_map.get(ui_component, {})
    if component_info:
        context.update(component_info)
        logger.info(f"📍 UI Context extracted - Component: {ui_component}, Domain: {component_info.get('domain')}")
    else:
        # Unknown component - provide generic context
        context.update({
            "domain": "general",
            "context_hint": f"Usuario interactuó con componente: {ui_component}",
        })
        logger.warning(f"⚠️ Unknown UI component: {ui_component}")

    # Tool-specific enrichment
    if tool_name:
        tool_context_map = {
            "explain_iva_calculation": {
                "focus": "Explicación detallada del cálculo de IVA (débito - crédito fiscal)",
                "requires": ["sales_documents", "purchase_documents"],
                "suggested_agent": "monthly_taxes_agent",
            },
            "analyze_revenue": {
                "focus": "Análisis de ingresos por tipo de documento y clientes",
                "requires": ["sales_documents"],
                "suggested_agent": "documentos_tributarios_agent",
            },
            "analyze_expenses": {
                "focus": "Análisis de gastos por tipo de documento y proveedores",
                "requires": ["purchase_documents"],
                "suggested_agent": "documentos_tributarios_agent",
            },
            "analyze_profit_margin": {
                "focus": "Análisis de utilidad neta y margen de ganancia",
                "requires": ["sales_documents", "purchase_documents"],
                "suggested_agent": "documentos_tributarios_agent",
            },
        }

        tool_info = tool_context_map.get(tool_name, {})
        if tool_info:
            context["tool_context"] = tool_info
            logger.info(f"🔧 Tool context extracted - Tool: {tool_name}, Focus: {tool_info.get('focus')}")

    # Add company context if available
    if company_id:
        context["company_id"] = company_id

    return context


def format_ui_context_for_agent(ui_context: dict[str, Any]) -> str:
    """
    Format the UI context into a human-readable string for agent consumption.

    Args:
        ui_context: Dictionary with UI context information

    Returns:
        Formatted string to prepend to agent instructions or context
    """
    if not ui_context or not ui_context.get("has_ui_context"):
        return ""

    parts = []

    # Add main context hint
    if hint := ui_context.get("context_hint"):
        parts.append(f"📍 Contexto: {hint}")

    # Add domain information
    if domain := ui_context.get("domain"):
        parts.append(f"Dominio: {domain}")

    # Add tool-specific focus
    if tool_context := ui_context.get("tool_context"):
        if focus := tool_context.get("focus"):
            parts.append(f"Enfoque: {focus}")

    # Add suggested agents
    if suggested_agents := ui_context.get("suggested_agents"):
        agents_str = ", ".join(suggested_agents)
        parts.append(f"Agentes sugeridos: {agents_str}")

    if parts:
        return "\n".join([
            "",
            "## CONTEXTO DE INTERFAZ",
            *parts,
            "",
        ])

    return ""

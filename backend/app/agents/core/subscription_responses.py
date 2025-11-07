"""
Subscription Response Builders - Structured responses for blocked agents/tools.

This module provides functions to generate structured, user-friendly responses
when agents or tools are blocked due to subscription limitations.

These responses are designed to be consumed by AI agents, which can then
reformulate them naturally for end users with upselling context.
"""

from __future__ import annotations

from typing import Literal, TypedDict


class SubscriptionBlockResponse(TypedDict):
    """Structured response when an agent or tool is blocked."""

    blocked: Literal[True]
    blocked_type: Literal["agent", "tool"]
    blocked_item: str
    display_name: str
    plan_required: str  # "basic", "pro", "enterprise"
    user_message: str
    benefits: list[str]
    upgrade_url: str
    alternative_message: str | None  # Optional suggestion for what user CAN do


# =============================================================================
# Agent Block Responses
# =============================================================================


def create_agent_block_response(agent_name: str) -> SubscriptionBlockResponse:
    """
    Generate a structured response when an agent is blocked.

    The supervisor agent receives this response and reformulates it
    naturally for the end user with upselling context.

    Args:
        agent_name: Name of the blocked agent (e.g., "payroll", "tax_documents")

    Returns:
        SubscriptionBlockResponse with all necessary information

    Example:
        >>> response = create_agent_block_response("payroll")
        >>> print(response["user_message"])
        "🔒 El módulo de Nómina está disponible en el Plan Pro..."
    """
    agent_info = {
        "payroll": {
            "display_name": "Nómina",
            "plan_required": "pro",
            "benefits": [
                "Gestión completa de empleados y colaboradores",
                "Cálculo automático de remuneraciones",
                "Asesoría en legislación laboral chilena",
                "Generación de liquidaciones de sueldo",
                "Reportes de nómina detallados",
            ],
            "alternative": (
                "Puedo ayudarte con información general sobre legislación laboral, "
                "conceptos de remuneraciones, o dudas sobre cómo gestionar empleados."
            ),
        },
        "tax_documents": {
            "display_name": "Documentos Tributarios",
            "plan_required": "basic",
            "benefits": [
                "Acceso a facturas de compra y venta",
                "Resúmenes tributarios automáticos",
                "Búsqueda avanzada de documentos",
                "Cálculos de IVA y totales",
                "Análisis de documentos por período",
            ],
            "alternative": (
                "Puedo ayudarte con información general sobre tipos de documentos "
                "tributarios, cómo funcionan las facturas, o conceptos de IVA."
            ),
        },
        "settings": {
            "display_name": "Configuración",
            "plan_required": "basic",
            "benefits": [
                "Gestión de notificaciones personalizadas",
                "Configuración de recordatorios",
                "Preferencias de calendario",
                "Administración de cuenta",
            ],
            "alternative": None,
        },
        "general_knowledge": {
            "display_name": "Conocimiento General",
            "plan_required": "free",
            "benefits": [
                "Consultas sobre conceptos tributarios",
                "Información sobre deadlines",
                "Explicaciones sobre formularios",
                "Asesoría conceptual",
            ],
            "alternative": None,
        },
    }

    info = agent_info.get(
        agent_name,
        {
            "display_name": agent_name.replace("_", " ").title(),
            "plan_required": "pro",
            "benefits": ["Funcionalidades avanzadas del sistema"],
            "alternative": None,
        },
    )

    user_message = (
        f"🔒 El módulo de {info['display_name']} está disponible en el Plan {info['plan_required'].title()}.\n\n"
        f"Este módulo incluye:\n"
        + "\n".join(f"• {benefit}" for benefit in info["benefits"])
        + f"\n\nMejora tu plan en Configuración > Suscripción para acceder a estas funcionalidades."
    )

    return {
        "blocked": True,
        "blocked_type": "agent",
        "blocked_item": agent_name,
        "display_name": info["display_name"],
        "plan_required": info["plan_required"],
        "user_message": user_message,
        "benefits": info["benefits"],
        "upgrade_url": "/configuracion/suscripcion",
        "alternative_message": info["alternative"],
    }


# =============================================================================
# Tool Block Responses
# =============================================================================


def create_tool_block_response(tool_name: str) -> dict:
    """
    Generate a structured response when a tool is blocked.

    The agent receives this response and can:
    1. Inform the user of the limitation
    2. Offer an alternative if available
    3. Suggest upgrading the plan

    Args:
        tool_name: Name of the blocked tool (e.g., "get_f29_data", "calculate_payroll")

    Returns:
        Dictionary with error information and upgrade details

    Example:
        >>> response = create_tool_block_response("get_f29_data")
        >>> if response.get("alternative_message"):
        >>>     # Agent can offer alternative functionality
    """
    tool_info = {
        "get_f29_data": {
            "display_name": "Datos de Formulario 29",
            "plan_required": "pro",
            "benefits": [
                "Acceso completo a información del F29",
                "Histórico de declaraciones mensuales",
                "Detalle de impuestos pagados y PPM",
                "Cálculos automáticos de diferencias",
            ],
            "alternative": (
                "Puedo ayudarte con información general sobre el Formulario 29, "
                "cómo llenarlo, qué líneas usar, o fechas de vencimiento."
            ),
        },
        "calculate_payroll": {
            "display_name": "Cálculo Automático de Remuneraciones",
            "plan_required": "enterprise",
            "benefits": [
                "Cálculo automático de sueldos brutos y líquidos",
                "Consideración de AFP, Isapre, e impuestos",
                "Generación de liquidaciones de sueldo",
                "Reportes de costos laborales",
            ],
            "alternative": (
                "Puedo explicarte cómo calcular remuneraciones manualmente, "
                "qué descuentos aplicar, o responder dudas sobre el proceso."
            ),
        },
        "get_advanced_reports": {
            "display_name": "Reportes Avanzados",
            "plan_required": "pro",
            "benefits": [
                "Reportes detallados de ingresos y gastos",
                "Análisis de rentabilidad por período",
                "Proyecciones financieras",
                "Gráficos y visualizaciones",
            ],
            "alternative": (
                "Puedo ayudarte a entender tus datos básicos o explicarte "
                "qué tipo de análisis puedes hacer."
            ),
        },
        "sync_sii_automatic": {
            "display_name": "Sincronización Automática con SII",
            "plan_required": "basic",
            "benefits": [
                "Sincronización automática de documentos",
                "Actualización periódica de DTEs",
                "Notificaciones de nuevos documentos",
                "Ahorro de tiempo en carga manual",
            ],
            "alternative": None,
        },
    }

    info = tool_info.get(
        tool_name,
        {
            "display_name": tool_name.replace("_", " ").title(),
            "plan_required": "pro",
            "benefits": ["Funcionalidad avanzada"],
            "alternative": None,
        },
    )

    user_message = (
        f"🔒 {info['display_name']} requiere Plan {info['plan_required'].title()}\n\n"
        f"Esta funcionalidad incluye:\n"
        + "\n".join(f"• {benefit}" for benefit in info["benefits"])
        + f"\n\nMejora tu plan en Configuración > Suscripción."
    )

    response = {
        "error": "subscription_required",
        "blocked": True,
        "blocked_type": "tool",
        "tool_name": tool_name,
        "display_name": info["display_name"],
        "plan_required": info["plan_required"],
        "user_message": user_message,
        "benefits": info["benefits"],
        "upgrade_url": "/configuracion/suscripcion",
    }

    if info["alternative"]:
        response["alternative_message"] = info["alternative"]

    return response


# =============================================================================
# Helper Functions
# =============================================================================


def format_benefits_list(benefits: list[str], prefix: str = "•") -> str:
    """
    Format a list of benefits as a bulleted list.

    Args:
        benefits: List of benefit strings
        prefix: Bullet character (default: "•")

    Returns:
        Formatted string with one benefit per line

    Example:
        >>> benefits = ["Feature 1", "Feature 2"]
        >>> print(format_benefits_list(benefits))
        • Feature 1
        • Feature 2
    """
    return "\n".join(f"{prefix} {benefit}" for benefit in benefits)


def get_plan_display_name(plan_code: str) -> str:
    """
    Get user-friendly display name for a plan code.

    Args:
        plan_code: Plan code (e.g., "pro", "enterprise")

    Returns:
        Display name (e.g., "Pro", "Enterprise")

    Example:
        >>> print(get_plan_display_name("pro"))
        Pro
    """
    plan_names = {
        "free": "Free",
        "basic": "Básico",
        "pro": "Pro",
        "enterprise": "Enterprise",
    }
    return plan_names.get(plan_code, plan_code.title())


def create_generic_block_message(
    item_type: str, item_name: str, plan_required: str = "pro"
) -> str:
    """
    Create a generic block message for items not in predefined lists.

    Args:
        item_type: Type of item ("agent" or "tool")
        item_name: Name of the blocked item
        plan_required: Required plan code

    Returns:
        Formatted block message

    Example:
        >>> msg = create_generic_block_message("tool", "custom_feature", "enterprise")
        >>> print(msg)
        🔒 Esta funcionalidad requiere Plan Enterprise...
    """
    if item_type == "agent":
        return (
            f"🔒 Este módulo requiere Plan {get_plan_display_name(plan_required)}.\n\n"
            f"Mejora tu plan en Configuración > Suscripción para acceder a funcionalidades avanzadas."
        )
    else:  # tool
        return (
            f"🔒 Esta funcionalidad requiere Plan {get_plan_display_name(plan_required)}.\n\n"
            f"Mejora tu plan en Configuración > Suscripción."
        )

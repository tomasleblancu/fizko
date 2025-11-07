"""
Agent scopes configuration - Define which agents are available per subscription plan.

This module defines 3 scopes:
- free: No subscription - very basic agent with general knowledge only
- basic: Basic plan - access to tax documents and basic analysis
- pro: Professional plan - full access to all agents including advanced features
"""

from typing import Literal


AgentScope = Literal["free", "basic", "pro"]


# Agent availability per scope
AGENT_SCOPES = {
    "free": {
        "agents": [
            # Only general knowledge - no access to company data or tax tools
            # This will be handled specially in the supervisor to limit functionality
        ],
        "description": "Conocimiento general contable básico sin acceso a datos de la empresa",
        "limitations": [
            "Sin acceso a documentos tributarios",
            "Sin acceso a análisis históricos",
            "Solo respuestas basadas en conocimiento general"
        ]
    },
    "basic": {
        "agents": [
            "tax_documents_agent",
            "payroll_agent",
            "settings_agent",
        ],
        "description": "Asistente con acceso a documentos tributarios y nómina",
        "limitations": [
            "Análisis limitado a datos disponibles",
            "Sin predicciones ni recomendaciones avanzadas"
        ]
    },
    "pro": {
        "agents": [
            "tax_documents_agent",
            "payroll_agent",
            "settings_agent",
            # Future: "advanced_analysis_agent", "predictions_agent", "recommendations_agent"
        ],
        "description": "Asistente profesional con todas las funcionalidades",
        "limitations": []
    }
}


def get_scope_for_plan(plan_code: str | None) -> AgentScope:
    """
    Get agent scope for a given subscription plan code.

    Args:
        plan_code: Plan code ("basic", "pro") or None for no subscription

    Returns:
        AgentScope: "free", "basic", or "pro"

    Examples:
        >>> get_scope_for_plan(None)
        'free'
        >>> get_scope_for_plan("basic")
        'basic'
        >>> get_scope_for_plan("pro")
        'pro'
    """
    if not plan_code:
        return "free"

    # Map plan codes to scopes
    if plan_code.lower() == "basic":
        return "basic"
    elif plan_code.lower() == "pro":
        return "pro"
    else:
        # Unknown plan -> treat as basic
        return "basic"


def get_available_agents(scope: AgentScope) -> list[str]:
    """
    Get list of available agent identifiers for a given scope.

    Args:
        scope: Agent scope level

    Returns:
        List of agent identifiers

    Examples:
        >>> get_available_agents("free")
        []
        >>> get_available_agents("basic")
        ['tax_documents_agent', 'payroll_agent', 'settings_agent']
    """
    return AGENT_SCOPES[scope]["agents"]


def get_scope_description(scope: AgentScope) -> str:
    """
    Get human-readable description of a scope.

    Args:
        scope: Agent scope level

    Returns:
        Description string

    Examples:
        >>> get_scope_description("free")
        'Conocimiento general contable básico sin acceso a datos de la empresa'
    """
    return AGENT_SCOPES[scope]["description"]


def get_scope_limitations(scope: AgentScope) -> list[str]:
    """
    Get list of limitations for a given scope.

    Args:
        scope: Agent scope level

    Returns:
        List of limitation strings

    Examples:
        >>> get_scope_limitations("free")
        ['Sin acceso a documentos tributarios', ...]
    """
    return AGENT_SCOPES[scope]["limitations"]


def is_agent_available(agent_id: str, scope: AgentScope) -> bool:
    """
    Check if a specific agent is available in a given scope.

    Args:
        agent_id: Agent identifier
        scope: Agent scope level

    Returns:
        True if agent is available in scope

    Examples:
        >>> is_agent_available("tax_documents_agent", "free")
        False
        >>> is_agent_available("tax_documents_agent", "basic")
        True
    """
    return agent_id in AGENT_SCOPES[scope]["agents"]


__all__ = [
    "AgentScope",
    "AGENT_SCOPES",
    "get_scope_for_plan",
    "get_available_agents",
    "get_scope_description",
    "get_scope_limitations",
    "is_agent_available",
]

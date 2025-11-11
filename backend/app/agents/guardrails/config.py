"""
Centralized guardrail configuration for all agents.

This file defines which guardrails are applied to each agent type.
"""

from typing import Callable

from app.agents.guardrails.implementations import (
    abuse_detection_guardrail,
    pii_output_guardrail,
    subscription_limit_guardrail,
)


# Guardrail configuration per agent
GUARDRAIL_CONFIG: dict[str, dict[str, list[Callable]]] = {
    "supervisor_agent": {
        "input": [
            abuse_detection_guardrail,  # Check for malicious usage
            # subscription_limit_guardrail,  # Uncomment to enable subscription checks
        ],
        "output": [
            pii_output_guardrail,  # Check for PII leakage
        ],
    },
    "general_knowledge_agent": {
        "input": [],  # Supervisor already checked
        "output": [
            pii_output_guardrail,
        ],
    },
    "tax_documents_agent": {
        "input": [],  # Supervisor already checked
        "output": [
            pii_output_guardrail,  # Important: tax docs may contain sensitive info
        ],
    },
    "monthly_taxes_agent": {
        "input": [],
        "output": [
            pii_output_guardrail,
        ],
    },
    "payroll_agent": {
        "input": [],
        "output": [
            pii_output_guardrail,  # Payroll data is highly sensitive
        ],
    },
    "settings_agent": {
        "input": [],
        "output": [],  # Settings are usually safe
    },
    "expense_agent": {
        "input": [],
        "output": [
            pii_output_guardrail,
        ],
    },
    "feedback_agent": {
        "input": [],
        "output": [],  # Feedback is user-generated
    },
}


def get_guardrails_for_agent(agent_name: str) -> dict[str, list[Callable]]:
    """
    Get guardrails for a specific agent.

    Args:
        agent_name: Name of the agent (e.g., "supervisor_agent")

    Returns:
        Dict with "input" and "output" keys containing lists of guardrail functions
    """
    return GUARDRAIL_CONFIG.get(agent_name, {"input": [], "output": []})


def apply_guardrails_to_agent(agent, agent_name: str):
    """
    Apply configured guardrails to an agent instance.

    Args:
        agent: Agent instance from agents.Agent
        agent_name: Name of the agent type

    Returns:
        Agent with guardrails applied
    """
    guardrails = get_guardrails_for_agent(agent_name)

    if guardrails["input"]:
        agent.input_guardrails = guardrails["input"]

    if guardrails["output"]:
        agent.output_guardrails = guardrails["output"]

    return agent

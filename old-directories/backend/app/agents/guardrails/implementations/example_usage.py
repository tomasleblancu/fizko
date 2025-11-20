"""
Example usage of guardrails with OpenAI Agents SDK.

This file shows how to add guardrails to your agents using the native SDK support.
"""

from agents import Agent
from app.agents.guardrails.implementations import (
    abuse_detection_guardrail,
    pii_output_guardrail,
)

from agents.model_settings import ModelSettings, Reasoning


# Example 1: Add guardrails to a new agent
def create_agent_with_guardrails():
    """Create an agent with input and output guardrails."""
    agent = Agent(
        name="Tax Assistant",
        instructions="You help users with tax questions.",
        model="gpt-5-nano",
        # Add input guardrails (run before agent execution)
        input_guardrails=[
            abuse_detection_guardrail,
        ],
        # Add output guardrails (run after agent execution)
        output_guardrails=[
            pii_output_guardrail,
        ],
        model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
    )
    return agent


# Example 2: Add guardrails to existing agent (in your specialized agent factories)
def add_guardrails_to_supervisor(agent: Agent) -> Agent:
    """
    Add guardrails to supervisor agent.

    This can be called in create_supervisor_agent() to add guardrails.
    """
    agent.input_guardrails = [
        abuse_detection_guardrail,
    ]
    agent.output_guardrails = [
        pii_output_guardrail,
    ]
    return agent


# Example 3: Conditional guardrails based on environment
def create_production_agent():
    """Create agent with guardrails enabled only in production."""
    import os

    is_production = os.getenv("ENVIRONMENT") == "production"

    agent = Agent(
        name="Tax Assistant",
        instructions="You help users with tax questions.",
        model="gpt-5-nano",
        model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
    )

    # Only add guardrails in production
    if is_production:
        agent.input_guardrails = [abuse_detection_guardrail]
        agent.output_guardrails = [pii_output_guardrail]

    return agent


# Example 4: Per-agent guardrail configuration
def get_guardrails_for_agent(agent_name: str):
    """
    Get appropriate guardrails for each agent type.

    Different agents may need different guardrails.
    """
    guardrail_config = {
        "supervisor_agent": {
            "input": [abuse_detection_guardrail],
            "output": [pii_output_guardrail],
        },
        "tax_documents_agent": {
            "input": [],  # No input guardrails for this agent
            "output": [pii_output_guardrail],  # But check output for PII
        },
        "payroll_agent": {
            "input": [abuse_detection_guardrail],
            "output": [pii_output_guardrail],
        },
        # ... other agents
    }

    return guardrail_config.get(agent_name, {"input": [], "output": []})

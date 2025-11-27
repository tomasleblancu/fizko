"""Classifier Agent - Pure routing with structured output (NO handoffs, NO tools)."""

from __future__ import annotations

import logging

from agents import Agent
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config.constants import SUPERVISOR_MODEL
from app.agents.instructions import CLASSIFIER_INSTRUCTIONS

logger = logging.getLogger(__name__)


class ClassificationAgentSchema(BaseModel):
    """Output schema for classification agent."""
    agent_name: str


def create_classifier_agent(
    db=None,  # Stub parameter for compatibility
    openai_client: AsyncOpenAI | None = None,
) -> Agent:
    """
    Create the Classifier Agent (pure router with structured output).

    This classifier agent:
    1. Analyzes user query + conversation history
    2. Returns structured output: ClassificationAgentSchema with agent_name
    3. NO handoffs, NO tools, ONLY structured output

    The agent_name is then used by the runner to call the appropriate specialized agent.

    Architecture:
        User Query → Classifier Agent → Returns {agent_name: "..."}
                                            ↓
                                    Runner maps to specialized agent
                                            ↓
                                    Specialized Agent processes with full history

    Args:
        db: Stub parameter for compatibility (not used)
        openai_client: OpenAI client (not used in simplified version)

    Returns:
        Classifier agent (no handoffs, structured output)
    """

    agent = Agent(
        name="classifier_agent",
        model=SUPERVISOR_MODEL,  # gpt-4o-mini (fast classification)
        instructions=CLASSIFIER_INSTRUCTIONS,
        tools=[],  # NO tools - pure structured output
        output_type=ClassificationAgentSchema,  # Structured output schema
    )

    logger.info("🎯 [CLASSIFIER] Created classifier agent (structured output)")

    return agent

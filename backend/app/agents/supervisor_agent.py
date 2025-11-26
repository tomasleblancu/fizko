"""Classifier Agent - Classifies user queries and routes to specialized agents."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI

from app.config.constants import SUPERVISOR_MODEL
from app.agents.instructions import SUPERVISOR_INSTRUCTIONS

logger = logging.getLogger(__name__)


def create_supervisor_agent(
    db=None,  # Stub parameter for compatibility
    openai_client: AsyncOpenAI = None,
) -> Agent:
    """
    Create the Classifier Agent (entry point for multi-agent system).

    The Classifier Agent:
    1. Analyzes user query (intent, domain, context, specificity)
    2. Classifies into ONE category (general_knowledge, tax_documents, f29, etc.)
    3. Calls handoff function to transfer to specialized agent

    This is a PURE CLASSIFIER - it does NOT answer questions, only routes them.

    Architecture:
        User Query → Classifier → Analyze → Classify → Call handoff
                                                         ↓
                                    Specialized Agent ← Handoff

    Args:
        db: Stub parameter for compatibility (not used in backend-v2)
        openai_client: OpenAI client (not used in simplified version)
    """

    agent = Agent(
        name="supervisor_agent",  # Keep name for compatibility
        model=SUPERVISOR_MODEL,  # gpt-4o-mini (fast classification)
        instructions=SUPERVISOR_INSTRUCTIONS,
        tools=[],  # No tools - only handoffs
        # No guardrails in backend-v2 simplified version
    )

    return agent

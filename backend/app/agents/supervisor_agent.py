"""Supervisor Agent - Routes user queries to specialized agents."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SUPERVISOR_MODEL
from app.agents.instructions import SUPERVISOR_INSTRUCTIONS
from app.agents.tools.widgets.subscription_widget_tools import (
    show_subscription_upgrade,
)

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

logger = logging.getLogger(__name__)


def create_supervisor_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Supervisor Agent that routes to specialized agents.

    The Supervisor Agent:
    1. Analyzes user intent (using gpt-4o-mini for speed)
    2. Routes IMMEDIATELY to the appropriate specialized agent
    3. Does NOT generate text responses - only function calls (handoffs)
    4. Does NOT have access to memory search tools (delegated to specialists)

    This is a pure router agent - it delegates all actual work to specialists.
    """

    agent = Agent(
        name="supervisor_agent",
        model=SUPERVISOR_MODEL,  # gpt-4o-mini (fast routing)
        instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n\n{SUPERVISOR_INSTRUCTIONS}",
        # model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
        tools=[
            show_subscription_upgrade,  # Show subscription upgrade widget when agent is blocked
        ],
    )

    return agent

"""Supervisor Agent - Routes user queries to specialized agents."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.constants import SUPERVISOR_MODEL, SUPERVISOR_INSTRUCTIONS

logger = logging.getLogger(__name__)


def create_supervisor_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Supervisor Agent that routes to specialized agents.

    The Supervisor Agent:
    1. Analyzes user intent (using gpt-4o-mini for speed)
    2. Routes to General Knowledge or Tax Documents agent
    3. Does NOT generate text responses - only function calls

    This is a pure router agent - it delegates all actual work to specialists.
    """

    agent = Agent(
        name="supervisor_agent",
        model=SUPERVISOR_MODEL,  # gpt-4o-mini (fast routing)
        instructions=SUPERVISOR_INSTRUCTIONS,
        # model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
        tools=[],  # Handoffs will be configured by orchestrator
    )

    return agent

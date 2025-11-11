"""Settings agent for managing user preferences and configuration."""

from __future__ import annotations

from agents import Agent
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SPECIALIZED_MODEL, REASONING_EFFORT
from ..instructions import SETTINGS_INSTRUCTIONS
from ..tools.settings import list_notifications, edit_notification
from ..tools.memory import (
    search_user_memory,
    search_company_memory,
)


def create_settings_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """Create settings management agent.

    This agent helps users manage their account settings and preferences,
    with a focus on notification preferences. It can:
    - List all available notifications and their current status
    - Enable/disable notifications globally
    - Mute/unmute specific notification templates

    Args:
        db: Database session
        openai_client: OpenAI client

    Returns:
        Agent: Configured settings agent
    """
    # Build agent kwargs
    agent_kwargs = {
        "name": "settings",
        "model": SPECIALIZED_MODEL,
        "instructions": SETTINGS_INSTRUCTIONS,
        "tools": [
            list_notifications,
            edit_notification,
            # Memory tools - dual system for user and company memory (read-only)
            search_user_memory,      # Search personal user preferences and history
            search_company_memory,   # Search company-wide knowledge and settings
        ],
    }

    # Add model_settings only for gpt-5* models
    if SPECIALIZED_MODEL.startswith("gpt-5"):
        agent_kwargs["model_settings"] = ModelSettings(reasoning=Reasoning(effort=REASONING_EFFORT))

    return Agent(**agent_kwargs)

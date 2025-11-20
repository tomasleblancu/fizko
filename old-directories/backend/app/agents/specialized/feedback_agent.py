"""Feedback Agent - Specialized in collecting user feedback and issue reporting."""

from __future__ import annotations

from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from agents.model_settings import ModelSettings, Reasoning

from app.config.constants import SPECIALIZED_MODEL, REASONING_EFFORT
from app.agents.instructions import FEEDBACK_INSTRUCTIONS
from app.agents.tools.feedback import (
    submit_feedback,
    update_feedback,
    get_my_feedback,
)
from app.agents.tools.memory import (
    search_user_memory,
    search_company_memory,
)
from app.agents.tools.orchestration import return_to_supervisor


def create_feedback_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Feedback Agent for user feedback collection.

    This agent specializes in:
    - Collecting user feedback, bug reports, and feature requests
    - Automatically categorizing feedback (bug, feature_request, improvement, etc.)
    - Determining priority levels intelligently (low, medium, high, urgent)
    - Registering feedback in the system
    - Allowing users to add more details to submitted feedback
    - Providing feedback history and status tracking

    Args:
        db: Database session
        openai_client: OpenAI client

    Examples of queries it handles:
    - "El botón no funciona"
    - "Sería bueno poder exportar a Excel"
    - "Esto es muy lento"
    - "Me encanta la nueva interfaz!"
    - "¿Qué pasó con el feedback que envié?"

    Key Features:
    - Automatic categorization (no need to ask users)
    - Intelligent priority assessment
    - Empathetic and encouraging responses
    - Seamless feedback submission workflow
    - Iterative detail collection
    """

    tools = [
        # Feedback tools
        submit_feedback,      # Register new feedback with auto-categorization
        update_feedback,      # Add details to recently submitted feedback
        get_my_feedback,      # View user's feedback history
        # Memory tools - dual system for user and company memory (read-only)
        search_user_memory,   # Search personal user preferences and history
        search_company_memory,# Search company-wide knowledge and settings
        # Orchestration tools
        return_to_supervisor, # Return to supervisor and clear active agent
    ]

    # Build agent kwargs
    agent_kwargs = {
        "name": "feedback_agent",
        "model": SPECIALIZED_MODEL,
        "instructions": f"{RECOMMENDED_PROMPT_PREFIX}\n\n{FEEDBACK_INSTRUCTIONS}",
        "tools": tools,
    }

    # Add model_settings only for gpt-5* models
    if SPECIALIZED_MODEL.startswith("gpt-5"):
        agent_kwargs["model_settings"] = ModelSettings(reasoning=Reasoning(effort=REASONING_EFFORT))

    agent = Agent(**agent_kwargs)

    return agent

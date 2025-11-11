"""Monthly Taxes Agent - Expert in Formulario 29 (F29) tax declarations."""

from __future__ import annotations

from agents import Agent, FileSearchTool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SPECIALIZED_MODEL, REASONING_EFFORT
from app.agents.instructions import MONTHLY_TAXES_INSTRUCTIONS
from ..tools.widgets import (
    show_f29_detail_widget,
    show_f29_summary_widget,
)
from ..tools.memory import (
    search_user_memory,
    search_company_memory,
)


def create_monthly_taxes_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    vector_store_ids: list[str] | None = None,
) -> Agent:
    """
    Create the Monthly Taxes Agent.

    This agent is specialized in Chilean F29 (Formulario 29) tax declarations.
    It has access to F29 widgets and memory tools.

    Args:
        db: Database session
        openai_client: OpenAI client
        vector_store_ids: Optional list of vector store IDs for FileSearchTool

    Examples of queries it handles:
    - "Muéstrame el F29 de septiembre"
    - "¿Qué significa el código 077?"
    - "¿Por qué tengo remanente a favor?"
    - "Explícame mi F29 del mes pasado"
    """

    tools = [
        # F29 widget tools - visual display of F29 data
        show_f29_summary_widget,  # Show F29 summary widget
        show_f29_detail_widget,   # Show detailed F29 breakdown widget
        # Memory tools - dual system for user and company memory (read-only)
        search_user_memory,       # Search personal user preferences and history
        search_company_memory,    # Search company-wide knowledge and settings
    ]

    # Add FileSearchTool if there are vector stores to search
    if vector_store_ids:
        tools.append(
            FileSearchTool(
                max_num_results=5,
                vector_store_ids=vector_store_ids
            )
        )

    # Build agent kwargs
    agent_kwargs = {
        "name": "monthly_taxes_agent",
        "model": SPECIALIZED_MODEL,
        "instructions": f"{RECOMMENDED_PROMPT_PREFIX}\n\n{MONTHLY_TAXES_INSTRUCTIONS}",
        "tools": tools,
    }

    # Add model_settings only for gpt-5* models
    if SPECIALIZED_MODEL.startswith("gpt-5"):
        agent_kwargs["model_settings"] = ModelSettings(reasoning=Reasoning(effort=REASONING_EFFORT))

    agent = Agent(**agent_kwargs)

    return agent

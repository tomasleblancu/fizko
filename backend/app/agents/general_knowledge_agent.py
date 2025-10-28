"""General Knowledge Agent - Expert in Chilean tax concepts and theory."""

from __future__ import annotations

from agents import Agent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.constants import SPECIALIZED_MODEL, GENERAL_KNOWLEDGE_INSTRUCTIONS


def create_general_knowledge_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the General Knowledge Agent.

    This agent handles conceptual and educational questions about Chilean taxation.
    It has NO tools - only knowledge-based responses.

    Examples of queries it handles:
    - "¿Qué es el IVA?"
    - "¿Cuándo se declara el F29?"
    - "¿Qué es el régimen ProPyme?"
    - "¿Cuál es la diferencia entre boleta y factura?"
    """

    agent = Agent(
        name="general_knowledge_agent",
        model=SPECIALIZED_MODEL,  # gpt-5-nano (fast and cheap)
        instructions=GENERAL_KNOWLEDGE_INSTRUCTIONS,
        tools=[],  # No tools - pure knowledge
    )

    return agent

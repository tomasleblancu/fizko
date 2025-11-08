"""General Knowledge Agent - Expert in Chilean tax concepts and theory."""

from __future__ import annotations

from agents import Agent, FileSearchTool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SPECIALIZED_MODEL
from app.agents.instructions import GENERAL_KNOWLEDGE_INSTRUCTIONS


def create_general_knowledge_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    vector_store_ids: list[str] | None = None,
) -> Agent:
    """
    Create the General Knowledge Agent.

    This agent handles conceptual and educational questions about Chilean taxation.

    Args:
        db: Database session
        openai_client: OpenAI client
        vector_store_ids: Optional list of vector store IDs for FileSearchTool

    Capabilities:
    - Answer educational questions about Chilean taxation
    - Search through tax documentation (FileSearchTool)

    Examples of queries it handles:
    - "¿Qué es el IVA?"
    - "¿Cuándo se declara el F29?"
    - "¿Qué es el régimen ProPyme?"
    - "¿Cuál es la diferencia entre boleta y factura?"
    """

    tools = []

    # Add FileSearchTool if there are vector stores to search
    if vector_store_ids:
        tools.append(
            FileSearchTool(
                max_num_results=5,
                vector_store_ids=vector_store_ids
            )
        )

    agent = Agent(
        name="general_knowledge_agent",
        model=SPECIALIZED_MODEL,  # gpt-5-nano (fast and cheap)
        instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n\n{GENERAL_KNOWLEDGE_INSTRUCTIONS}",
        # model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
        tools=tools,
    )

    return agent

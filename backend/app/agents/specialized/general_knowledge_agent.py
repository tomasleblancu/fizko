"""General Knowledge Agent - Expert in Chilean tax concepts and theory."""

from __future__ import annotations

import logging

from agents import Agent, FileSearchTool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SPECIALIZED_MODEL
from app.agents.instructions import GENERAL_KNOWLEDGE_INSTRUCTIONS
from ..tools.widgets import (
    show_f29_detail_widget,
    show_f29_summary_widget,
)
from ..tools.memory import (
    search_user_memory,
    search_company_memory,
)

logger = logging.getLogger(__name__)


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

    tools = [
        # F29 widget tools - available to all plans
        show_f29_detail_widget,  # Show detailed F29 breakdown widget
        show_f29_summary_widget,  # Show F29 summary widget
        # Memory tools - dual system for user and company memory (read-only)
        search_user_memory,      # Search personal user preferences and history
        search_company_memory,   # Search company-wide knowledge and settings
    ]

    # Build vector stores list: SII FAQ (always) + user PDFs (from parameter)
    import os
    final_vector_store_ids = []

    # Add SII FAQ vector store (specific to general_knowledge_agent)
    sii_faq_vector_id = os.getenv("SII_FAQ_VECTOR_STORE_ID")
    if sii_faq_vector_id:
        final_vector_store_ids.append(sii_faq_vector_id)
        logger.info(f"📚 Added SII FAQ vector store: {sii_faq_vector_id}")

    # Add user PDF vector stores (if provided)
    if vector_store_ids:
        final_vector_store_ids.extend(vector_store_ids)
        logger.info(f"📄 Added {len(vector_store_ids)} user PDF vector store(s)")

    # Add FileSearchTool if there are any vector stores
    if final_vector_store_ids:
        logger.info(f"📚 Creating general_knowledge_agent with FileSearchTool ({len(final_vector_store_ids)} total vector store(s))")
        tools.append(
            FileSearchTool(
                max_num_results=5,
                vector_store_ids=final_vector_store_ids
            )
        )
    else:
        logger.info("⚠️  Creating general_knowledge_agent WITHOUT FileSearchTool (no vector stores available)")

    agent = Agent(
        name="general_knowledge_agent",
        model=SPECIALIZED_MODEL,  # gpt-5-nano (fast and cheap)
        instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n\n{GENERAL_KNOWLEDGE_INSTRUCTIONS}",
        # model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
        tools=tools,
    )

    # Log final tool configuration
    tool_names = [t.name if hasattr(t, 'name') else type(t).__name__ for t in tools]
    logger.info(f"✅ general_knowledge_agent created with {len(tools)} tools: {', '.join(tool_names)}")

    return agent

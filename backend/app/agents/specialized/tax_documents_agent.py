"""Tax Documents Agent - Expert in real tax document data and analysis."""

from __future__ import annotations

from agents import Agent, FileSearchTool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SPECIALIZED_MODEL, REASONING_EFFORT
from app.agents.instructions import TAX_DOCUMENTS_INSTRUCTIONS
from ..tools.tax.documentos_tributarios_tools import (
    get_documents,
    get_documents_summary,
)
from ..tools.widgets import (
    show_f29_detail_widget,
    show_f29_summary_widget,
)
from ..tools.memory import (
    search_user_memory,
    search_company_memory,
)


def create_tax_documents_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    vector_store_ids: list[str] | None = None,
) -> Agent:
    """
    Create the Tax Documents Agent.

    This agent has access to tools for querying real tax documents.
    It handles all queries that require actual data from the database.

    Args:
        db: Database session
        openai_client: OpenAI client
        vector_store_ids: Optional list of vector store IDs for FileSearchTool

    Examples of queries it handles:
    - "Dame un resumen de ventas del mes"
    - "Muéstrame las últimas 5 facturas"
    - "Busca la factura folio 12345"
    - "Cuánto vendí en septiembre?"
    """

    tools = [
        # Tax document tools
        get_documents_summary,  # Summary tool - for monthly/yearly aggregations
        get_documents,          # Main search tool - flexible filtering (RUT, folio, dates, type)
        # Memory tools - dual system for user and company memory (read-only)
        search_user_memory,     # Search personal user preferences and history
        search_company_memory,  # Search company-wide knowledge and settings
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
        "name": "tax_documents_agent",
        "model": SPECIALIZED_MODEL,
        "instructions": f"{RECOMMENDED_PROMPT_PREFIX}\n\n{TAX_DOCUMENTS_INSTRUCTIONS}",
        "tools": tools,
    }

    # Add model_settings only for gpt-5* models
    if SPECIALIZED_MODEL.startswith("gpt-5"):
        agent_kwargs["model_settings"] = ModelSettings(reasoning=Reasoning(effort=REASONING_EFFORT))

    agent = Agent(**agent_kwargs)

    return agent

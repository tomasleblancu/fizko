"""Tax Documents Agent - Expert in real tax document data and analysis."""

from __future__ import annotations

from agents import Agent, FileSearchTool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.constants import SPECIALIZED_MODEL, TAX_DOCUMENTS_INSTRUCTIONS
from ..tools.tax.documentos_tributarios_tools import (
    get_documents,
    get_documents_summary,
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
        # Summary tool - for monthly/yearly aggregations
        get_documents_summary,
        # Main search tool - flexible filtering (RUT, folio, dates, type)
        get_documents,
    ]

    # Add FileSearchTool if there are vector stores to search
    if vector_store_ids:
        tools.append(
            FileSearchTool(
                max_num_results=5,
                vector_store_ids=vector_store_ids
            )
        )

    agent = Agent(
        name="tax_documents_agent",
        model=SPECIALIZED_MODEL,  # gpt-5-nano (fast and cheap)
        instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n\n{TAX_DOCUMENTS_INSTRUCTIONS}",
        tools=tools,
    )

    return agent

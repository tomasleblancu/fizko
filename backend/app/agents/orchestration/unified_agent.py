"""Unified Fizko Agent - Single agent with access to all tools."""

from __future__ import annotations

import logging

from agents import Agent, FileSearchTool
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.constants import MODEL, UNIFIED_AGENT_INSTRUCTIONS

# Import all tools
# NOTE: get_company_info removed - company info is now loaded automatically in context
from ..tools.tax.documentos_tributarios_tools import (
    get_documents,
    get_documents_summary,
)
from ..tools.widgets.tax_widget_tools import show_tax_calculation_widget, show_document_detail_widget

logger = logging.getLogger(__name__)


def create_unified_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    vector_store_ids: list[str] | None = None,
    channel: str = "web",  # "web" o "whatsapp"
) -> Agent:
    """
    Create the unified Fizko agent with access to all tools.

    This single agent handles all Chilean tax and accounting queries
    with 9+ specialized tools covering:
    - Tax documents (invoices, receipts, DTE)
    - Visual widgets (tax calculations, document details) - SOLO WEB
    - File search (for uploaded PDFs)

    Args:
        db: Database session
        openai_client: OpenAI client
        vector_store_ids: Optional list of vector store IDs for FileSearchTool
        channel: Canal de comunicación ("web" o "whatsapp")
                 - "web": incluye widgets
                 - "whatsapp": sin widgets (solo texto)

    Note: Company information is now automatically loaded in the agent context,
    so no tool is needed for that.
    """

    # Base tools list - Tax documents (2 simplified tools)
    tools = [
        get_documents_summary,  # Monthly/yearly summaries with IVA
        get_documents,  # Flexible search (RUT, folio, dates, type)
    ]

    # Add widgets ONLY for web channel (not for WhatsApp)
    if channel == "web":
        logger.info("📊 Including widget tools (web channel)")
        tools.extend([
            show_tax_calculation_widget,
            show_document_detail_widget,
        ])
    else:
        logger.info("📱 Excluding widget tools (WhatsApp channel)")


    # Add FileSearchTool if there are vector stores to search
    if vector_store_ids:
        logger.info(f"📄 Adding FileSearchTool with {len(vector_store_ids)} vector store(s)")
        tools.append(
            FileSearchTool(
                max_num_results=5,
                vector_store_ids=vector_store_ids
            )
        )

    # Note: file_search requires reasoning.effort != "minimal"
    # If there are PDFs attached, we need to use at least "low" reasoning effort
    reasoning_effort = "low" if vector_store_ids else "minimal"

    agent = Agent(
        name="fizko_agent",
        model=MODEL,
        instructions=UNIFIED_AGENT_INSTRUCTIONS,
        model_settings=ModelSettings(reasoning=Reasoning(effort=reasoning_effort)),
        tools=tools,
    )

    return agent

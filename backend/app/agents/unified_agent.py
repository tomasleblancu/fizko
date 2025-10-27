"""Unified Fizko Agent - Single agent with access to all tools."""

from __future__ import annotations

import logging

from agents import Agent
from agents.model_settings import ModelSettings, Reasoning
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.constants import MODEL, UNIFIED_AGENT_INSTRUCTIONS

# Import all tools
# NOTE: get_company_info removed - company info is now loaded automatically in context
from .tools.documentos_tributarios_tools import (
    search_documents_by_rut,
    search_document_by_folio,
    get_documents_by_date_range,
    get_purchase_documents,
    get_sales_documents,
    get_document_details,
    get_documents_summary,
)
from .tools.tax_widget_tools import show_tax_calculation_widget, show_document_detail_widget

logger = logging.getLogger(__name__)


def create_unified_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the unified Fizko agent with access to all tools.

    This single agent handles all Chilean tax and accounting queries
    with 9 specialized tools covering:
    - Tax documents (invoices, receipts, DTE)
    - Visual widgets (tax calculations, document details)

    Note: Company information is now automatically loaded in the agent context,
    so no tool is needed for that.
    """

    agent = Agent(
        name="fizko_agent",
        model=MODEL,
        instructions=UNIFIED_AGENT_INSTRUCTIONS,
        # model_settings=ModelSettings(reasoning=Reasoning(effort="minimal")),
        tools=[
            # Tax documents (7)
            search_documents_by_rut,
            search_document_by_folio,
            get_documents_by_date_range,
            get_purchase_documents,
            get_sales_documents,
            get_document_details,
            get_documents_summary,

            # Widgets (2)
            show_tax_calculation_widget,
            show_document_detail_widget,
        ],
    )

    return agent

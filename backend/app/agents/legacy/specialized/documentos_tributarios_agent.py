"""Documentos Tributarios Agent - Expert in Chilean tax documents (DTE)."""

from __future__ import annotations

from agents import Agent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.constants import MODEL, DOCUMENTOS_TRIBUTARIOS_INSTRUCTIONS
from ..tools.documentos_tributarios_tools import (
    get_purchase_documents,
    get_sales_documents,
    get_document_details,
    get_documents_summary,
    search_documents_by_rut,
    search_document_by_folio,
    get_documents_by_date_range,
)


def create_documentos_tributarios_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Documentos Tributarios Agent.

    This agent helps with:
    - Understanding Chilean tax documents (DTE)
    - Querying purchase and sales documents
    - Explaining document types and their tax implications
    - Interpreting document amounts, IVA, and totals
    """

    agent = Agent(
        name="documentos_tributarios_agent",
        model=MODEL,
        instructions=DOCUMENTOS_TRIBUTARIOS_INSTRUCTIONS,
        tools=[
            get_purchase_documents,
            get_sales_documents,
            get_document_details,
            get_documents_summary,
            search_documents_by_rut,
            search_document_by_folio,
            get_documents_by_date_range,
        ],
    )

    return agent

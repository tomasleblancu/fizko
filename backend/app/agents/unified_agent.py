"""Unified Fizko Agent - Single agent with access to all tools."""

from __future__ import annotations

import logging

from agents import Agent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.constants import MODEL, UNIFIED_AGENT_INSTRUCTIONS

# Import all tools
from .tools.sii_general_tools import get_company_info
from .tools.documentos_tributarios_tools import (
    search_documents_by_rut,
    search_document_by_folio,
    get_documents_by_date_range,
    get_purchase_documents,
    get_sales_documents,
    get_document_details,
    get_documents_summary,
)
from .tools.f29_tools import (
    calculate_f29_iva,
    calculate_ppm,
    explain_f29_completion,
    calculate_f29_summary,
)
from .tools.operacion_renta_tools import (
    calculate_annual_income_tax,
    explain_operacion_renta,
    calculate_global_complementario,
)
from .tools.remuneraciones_tools import (
    calculate_salary,
    calculate_employer_contributions,
)

logger = logging.getLogger(__name__)


def create_unified_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the unified Fizko agent with access to all tools.

    This single agent handles all Chilean tax and accounting queries
    with 17 specialized tools covering:
    - Company information
    - Tax documents (invoices, receipts, DTE)
    - F29 monthly tax declarations
    - Annual income tax (Operación Renta)
    - Payroll and salary calculations
    """

    agent = Agent(
        name="fizko_agent",
        model=MODEL,
        instructions=UNIFIED_AGENT_INSTRUCTIONS,
        tools=[
            # Company info (1)
            get_company_info,

            # Tax documents (7)
            search_documents_by_rut,
            search_document_by_folio,
            get_documents_by_date_range,
            get_purchase_documents,
            get_sales_documents,
            get_document_details,
            get_documents_summary,

            # F29 monthly tax (4)
            calculate_f29_iva,
            calculate_ppm,
            explain_f29_completion,
            calculate_f29_summary,

            # Annual tax / Operación Renta (3)
            calculate_annual_income_tax,
            explain_operacion_renta,
            calculate_global_complementario,

            # Payroll / Remuneraciones (2)
            calculate_salary,
            calculate_employer_contributions,
        ],
    )

    logger.info(f"Created unified agent '{agent.name}' with {len(agent.tools)} tools")
    return agent

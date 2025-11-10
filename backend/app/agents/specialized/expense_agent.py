"""Expense Agent - Specialized in manual expense registration and management."""

from __future__ import annotations

from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SPECIALIZED_MODEL
from app.agents.instructions import EXPENSE_INSTRUCTIONS
from app.agents.tools.tax.expense_tools import (
    create_expense,
    get_expenses,
    get_expense_summary,
)
from app.agents.tools.memory import (
    search_user_memory,
    search_company_memory,
)


def create_expense_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Expense Agent for manual expense registration.

    This agent specializes in:
    - Registering manual expenses from receipts (non-DTE documents)
    - Analyzing receipt images/PDFs with vision/OCR
    - Guiding users through expense categorization
    - Providing expense summaries and reports
    - Managing expense approval workflows

    Args:
        db: Database session
        openai_client: OpenAI client

    Examples of queries it handles:
    - "Quiero registrar un gasto"
    - "Muéstrame mis gastos del mes"
    - "¿Cuánto he gastado en transporte?"
    - "Registra este recibo de taxi"

    Types of expenses handled:
    - Taxi/Uber receipts (boletas de taxi)
    - Parking tickets
    - Restaurant meals (boletas de restaurant)
    - Office supplies from small vendors
    - Any expense without electronic DTE
    """

    tools = [
        # Expense management tools
        create_expense,        # Register manual expense (requires receipt upload)
        get_expenses,          # Query and search expenses
        get_expense_summary,   # Get aggregated expense statistics
        # Memory tools - dual system for user and company memory (read-only)
        search_user_memory,    # Search personal user preferences and history
        search_company_memory, # Search company-wide knowledge and settings
    ]

    agent = Agent(
        name="expense_agent",
        model=SPECIALIZED_MODEL,  # gpt-4o-mini (fast and economical)
        instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n\n{EXPENSE_INSTRUCTIONS}",
        tools=tools,
    )

    return agent

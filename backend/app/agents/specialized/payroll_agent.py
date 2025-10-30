"""Payroll Agent - Expert in payroll management and labor law."""

from __future__ import annotations

from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.constants import SPECIALIZED_MODEL, PAYROLL_INSTRUCTIONS
from ..tools.payroll.payroll_tools import (
    get_people,
    get_person,
    create_person,
    update_person,
)
from ..tools.widgets.payroll_widget_tools import (
    show_person_confirmation,
)


def create_payroll_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Payroll Agent.

    This agent handles:
    1. Labor law consultations (contracts, vacations, terminations, etc.)
    2. Employee/collaborator management (CRUD operations)
    3. Payroll slip processing and data extraction

    Args:
        db: Database session
        openai_client: OpenAI client

    Examples of queries it handles:
    - "¿Cuántos días de vacaciones corresponden por ley?"
    - "Muéstrame todos los colaboradores"
    - "Agrega un nuevo colaborador: Juan Pérez..."
    - "Actualiza el sueldo de María a $850.000"
    """

    tools = [
        # Confirmation widget (MUST BE USED FIRST before create/update)
        show_person_confirmation,
        # List all employees
        get_people,
        # Get specific employee details
        get_person,
        # Create new employee (USE ONLY AFTER show_person_confirmation + user confirmation)
        create_person,
        # Update employee information (USE ONLY AFTER show_person_confirmation + user confirmation)
        update_person,
    ]

    agent = Agent(
        name="payroll_agent",
        model=SPECIALIZED_MODEL,  # gpt-4o-mini (fast and cheap)
        instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n\n{PAYROLL_INSTRUCTIONS}",
        tools=tools,
    )

    return agent

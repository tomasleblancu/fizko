"""Payroll Agent - Expert in payroll management and labor law."""

from __future__ import annotations

from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import SPECIALIZED_MODEL
from app.agents.instructions import PAYROLL_INSTRUCTIONS
from ..tools.payroll.payroll_tools import (
    get_people,
    get_person,
    create_person,
    update_person,
)
from ..tools.widgets.payroll_widget_tools import (
    show_person_confirmation,
)
from ..tools.memory import (
    search_user_memory,
    search_company_memory,
)


def create_payroll_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    channel: str = "web",
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
        channel: Communication channel ("web" or "whatsapp")

    Examples of queries it handles:
    - "¿Cuántos días de vacaciones corresponden por ley?"
    - "Muéstrame todos los colaboradores"
    - "Agrega un nuevo colaborador: Juan Pérez..."
    - "Actualiza el sueldo de María a $850.000"
    """
    import logging
    logger = logging.getLogger(__name__)

    tools = [
        # Employee management tools
        get_people,         # List all employees
        get_person,         # Get specific employee details
        create_person,      # Create new employee
        update_person,      # Update employee information
        # Memory tools - dual system for user and company memory (read-only)
        search_user_memory,     # Search personal user preferences and history
        search_company_memory,  # Search company-wide knowledge and settings
    ]

    # Add widgets ONLY for web channel (not for WhatsApp)
    if channel == "web":
        logger.info("📊 Including payroll widget tools (web channel)")
        # Insert confirmation widget at the beginning (MUST BE USED FIRST before create/update)
        tools.insert(0, show_person_confirmation)
    else:
        logger.info("📱 Excluding payroll widget tools (WhatsApp channel)")

    agent = Agent(
        name="payroll_agent",
        model=SPECIALIZED_MODEL,  # gpt-4o-mini (fast and cheap)
        instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n\n{PAYROLL_INSTRUCTIONS}",
        tools=tools,
    )

    return agent

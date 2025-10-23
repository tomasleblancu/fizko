"""SII General Agent - Expert in Chilean tax authority (SII) regulations."""

from __future__ import annotations

import logging

from agents import Agent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ...config.constants import MODEL, SII_GENERAL_INSTRUCTIONS
from ..tools.sii_general_tools import get_company_info

logger = logging.getLogger(__name__)


def create_sii_general_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the SII General Agent.

    This agent provides information about the user's company and
    general Chilean tax authority (SII) knowledge.
    """

    agent = Agent(
        name="sii_general_agent",
        model=MODEL,
        instructions=SII_GENERAL_INSTRUCTIONS,
        tools=[
            get_company_info,
        ],
    )

    return agent

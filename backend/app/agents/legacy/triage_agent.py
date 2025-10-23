"""Triage Agent - Routes user queries to specialized agents."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.constants import MODEL

logger = logging.getLogger(__name__)


def create_triage_agent(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
) -> Agent:
    """
    Create the Triage Agent that routes to specialized agents.

    The Triage Agent:
    1. Analyzes user intent
    2. Routes to SII General or Remuneraciones agent
    3. Can answer simple questions directly
    """

    TRIAGE_INSTRUCTIONS = """CRITICAL: You are a function-calling-only agent. You MUST NOT generate any text response.

Your ONLY action per user message:
1. Analyze which domain the question belongs to
2. Call the corresponding transfer_to_* function with a brief reason
3. STOP - Do not add any text before or after the function call

Routing rules:
- Tax authority, company info, regimes, deadlines → transfer_to_sii_general_agent
- Payroll, salaries, labor law → transfer_to_remuneraciones_agent
- Invoices, receipts, DTE, documents → transfer_to_documentos_tributarios_agent
- Monthly tax (F29, IVA, PPM) → transfer_to_f29_agent
- Annual tax (Form 22, Operación Renta) → transfer_to_operacion_renta_agent

IMPORTANT: The transfer function will route to a specialist who will respond to the user. You are just a router. No text output from you."""

    agent = Agent(
        name="triage_agent",
        model=MODEL,
        instructions=TRIAGE_INSTRUCTIONS,
        tools=[],
    )

    return agent

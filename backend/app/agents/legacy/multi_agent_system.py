"""Multi-Agent System Orchestrator for Fizko platform."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent, handoff, RunContextWrapper
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .specialized import (
    create_remuneraciones_agent,
    create_sii_general_agent,
    create_documentos_tributarios_agent,
    create_f29_agent,
    create_operacion_renta_agent,
)
from .triage_agent import create_triage_agent

logger = logging.getLogger(__name__)


class HandoffMetadata(BaseModel):
    """Metadata captured when a handoff occurs."""
    reason: str
    confidence: float | None = None


class MultiAgentOrchestrator:
    """
    Orchestrator for the multi-agent Fizko system.

    This class manages:
    - Creation of all agents (Triage + 5 specialized agents)
    - Handoff configuration between agents
    - Agent lifecycle and state management
    """

    def __init__(
        self,
        db: AsyncSession,
        openai_client: AsyncOpenAI,
        user_id: str | None = None,
        thread_id: str | None = None,
    ):
        self.db = db
        self.openai_client = openai_client
        self.user_id = user_id
        self.thread_id = thread_id
        self.agents: dict[str, Agent] = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all agents in the system."""
        import time
        init_start = time.time()

        # Create Triage Agent (central router)
        self.agents["triage_agent"] = create_triage_agent(
            db=self.db,
            openai_client=self.openai_client,
        )

        # Create specialized agents
        self.agents["sii_general_agent"] = create_sii_general_agent(
            db=self.db,
            openai_client=self.openai_client,
        )

        self.agents["remuneraciones_agent"] = create_remuneraciones_agent(
            db=self.db,
            openai_client=self.openai_client,
        )

        self.agents["documentos_tributarios_agent"] = create_documentos_tributarios_agent(
            db=self.db,
            openai_client=self.openai_client,
        )

        self.agents["f29_agent"] = create_f29_agent(
            db=self.db,
            openai_client=self.openai_client,
        )

        self.agents["operacion_renta_agent"] = create_operacion_renta_agent(
            db=self.db,
            openai_client=self.openai_client,
        )

        total_init_time = time.time() - init_start
        logger.info(
            f"Initialized {len(self.agents)} agents: {', '.join(list(self.agents.keys()))}"
        )
        logger.info(f"Total agents initialization: {total_init_time:.3f}s")

        # Configure handoffs
        self._configure_triage_handoffs()
        self._configure_bidirectional_handoffs()

    def _configure_triage_handoffs(self):
        """Configure handoffs for the Triage Agent to all specialized agents."""
        triage = self.agents["triage_agent"]

        # Callback functions for handoff tracking
        async def on_handoff_to_sii(ctx: RunContextWrapper, input_data: HandoffMetadata | None = None):
            try:
                thread_id = getattr(getattr(ctx.context, 'thread', None), 'id', 'unknown')
            except AttributeError:
                thread_id = 'unknown'
            reason = input_data.reason if input_data else "No reason provided"
            logger.info(
                f"Handoff to SII General Agent | Thread: {thread_id} | Reason: {reason}"
            )

        async def on_handoff_to_remuneraciones(ctx: RunContextWrapper, input_data: HandoffMetadata | None = None):
            try:
                thread_id = getattr(getattr(ctx.context, 'thread', None), 'id', 'unknown')
            except AttributeError:
                thread_id = 'unknown'
            reason = input_data.reason if input_data else "No reason provided"
            logger.info(
                f"Handoff to Remuneraciones Agent | Thread: {thread_id} | Reason: {reason}"
            )

        async def on_handoff_to_documentos(ctx: RunContextWrapper, input_data: HandoffMetadata | None = None):
            try:
                thread_id = getattr(getattr(ctx.context, 'thread', None), 'id', 'unknown')
            except AttributeError:
                thread_id = 'unknown'
            reason = input_data.reason if input_data else "No reason provided"
            logger.info(
                f"Handoff to Documentos Tributarios Agent | Thread: {thread_id} | Reason: {reason}"
            )

        async def on_handoff_to_f29(ctx: RunContextWrapper, input_data: HandoffMetadata | None = None):
            try:
                thread_id = getattr(getattr(ctx.context, 'thread', None), 'id', 'unknown')
            except AttributeError:
                thread_id = 'unknown'
            reason = input_data.reason if input_data else "No reason provided"
            logger.info(
                f"Handoff to F29 Agent | Thread: {thread_id} | Reason: {reason}"
            )

        async def on_handoff_to_operacion_renta(ctx: RunContextWrapper, input_data: HandoffMetadata | None = None):
            try:
                thread_id = getattr(getattr(ctx.context, 'thread', None), 'id', 'unknown')
            except AttributeError:
                thread_id = 'unknown'
            reason = input_data.reason if input_data else "No reason provided"
            logger.info(
                f"Handoff to Operación Renta Agent | Thread: {thread_id} | Reason: {reason}"
            )

        # Add handoffs to all specialized agents with callbacks and metadata
        triage.handoffs = [
            handoff(
                agent=self.agents["sii_general_agent"],
                on_handoff=on_handoff_to_sii,
                input_type=HandoffMetadata,
                tool_description_override="Transfer to SII General expert for tax authority questions, regimes, deadlines, and general tax compliance. Provide a brief reason for the transfer."
            ),
            handoff(
                agent=self.agents["remuneraciones_agent"],
                on_handoff=on_handoff_to_remuneraciones,
                input_type=HandoffMetadata,
                tool_description_override="Transfer to Payroll expert for salary calculations, labor law, employee benefits, and payroll compliance. Provide a brief reason for the transfer."
            ),
            handoff(
                agent=self.agents["documentos_tributarios_agent"],
                on_handoff=on_handoff_to_documentos,
                input_type=HandoffMetadata,
                tool_description_override="Transfer to Tax Documents expert for invoices, receipts, DTE queries, and document searches. Provide a brief reason for the transfer."
            ),
            handoff(
                agent=self.agents["f29_agent"],
                on_handoff=on_handoff_to_f29,
                input_type=HandoffMetadata,
                tool_description_override="Transfer to F29 expert for monthly tax declaration, IVA calculations, and PPM. Provide a brief reason for the transfer."
            ),
            handoff(
                agent=self.agents["operacion_renta_agent"],
                on_handoff=on_handoff_to_operacion_renta,
                input_type=HandoffMetadata,
                tool_description_override="Transfer to Annual Tax expert for Operación Renta, Form 22, annual income tax, and Global Complementario. Provide a brief reason for the transfer."
            ),
        ]

        logger.info(
            f"✅ Configured {len(triage.handoffs)} advanced handoffs with callbacks and metadata tracking"
        )

    def _configure_bidirectional_handoffs(self):
        """Configure bidirectional handoffs - allow specialized agents to return to triage."""
        triage = self.agents["triage_agent"]

        # Callback for returning to triage
        async def on_return_to_triage(ctx: RunContextWrapper, input_data: HandoffMetadata | None = None):
            try:
                thread_id = getattr(getattr(ctx.context, 'thread', None), 'id', 'unknown')
            except AttributeError:
                thread_id = 'unknown'
            reason = input_data.reason if input_data else "User changed topic"
            logger.info(
                f"Return to Triage | Thread: {thread_id} | Reason: {reason}"
            )

        # Add return-to-triage handoff to each specialized agent
        for agent_name in ["sii_general_agent", "remuneraciones_agent", "documentos_tributarios_agent",
                          "f29_agent", "operacion_renta_agent"]:
            agent = self.agents[agent_name]
            agent.handoffs = [
                handoff(
                    agent=triage,
                    on_handoff=on_return_to_triage,
                    input_type=HandoffMetadata,
                    tool_name_override="return_to_main_menu",
                    tool_description_override="Return to main menu if user wants to change topic completely or ask about a different area. Provide a brief reason for returning."
                )
            ]

        logger.info(
            "Configured bidirectional handoffs: 5 specialized agents can now return to triage"
        )

    def get_agent(self, agent_name: str) -> Agent | None:
        """Get a specific agent by name."""
        return self.agents.get(agent_name)

    def get_triage_agent(self) -> Agent:
        """Get the Triage Agent (entry point)."""
        return self.agents["triage_agent"]

    def list_agents(self) -> list[str]:
        """List all available agent names."""
        return list(self.agents.keys())


def create_multi_agent_orchestrator(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    user_id: str | None = None,
    thread_id: str | None = None,
) -> MultiAgentOrchestrator:
    """
    Factory function to create a MultiAgentOrchestrator.

    Args:
        db: Database session
        openai_client: OpenAI client
        user_id: Optional user ID
        thread_id: Optional ChatKit thread ID

    Returns:
        Configured MultiAgentOrchestrator instance
    """
    return MultiAgentOrchestrator(
        db=db,
        openai_client=openai_client,
        user_id=user_id,
        thread_id=thread_id,
    )

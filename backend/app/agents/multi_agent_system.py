"""Multi-Agent System Orchestrator for Fizko platform."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from .specialized import (
    create_remuneraciones_agent,
    create_sii_general_agent,
    create_documentos_tributarios_agent,
    create_importaciones_agent,
    create_contabilidad_agent,
    create_f29_agent,
    create_operacion_renta_agent,
)
from .triage_agent import create_triage_agent

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """
    Orchestrator for the multi-agent Fizko system.

    This class manages:
    - Creation of all agents (Triage + 7 specialized agents)
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

        self.agents["importaciones_agent"] = create_importaciones_agent(
            db=self.db,
            openai_client=self.openai_client,
        )

        self.agents["contabilidad_agent"] = create_contabilidad_agent(
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

        # Configure handoffs for Triage Agent
        self._configure_triage_handoffs()

    def _configure_triage_handoffs(self):
        """Configure handoffs for the Triage Agent to all specialized agents."""
        triage = self.agents["triage_agent"]

        # Add handoffs to all specialized agents
        triage.handoffs = [
            self.agents["sii_general_agent"],
            self.agents["remuneraciones_agent"],
            self.agents["documentos_tributarios_agent"],
            self.agents["importaciones_agent"],
            self.agents["contabilidad_agent"],
            self.agents["f29_agent"],
            self.agents["operacion_renta_agent"],
        ]

        logger.info(
            f"Configured {len(triage.handoffs)} handoffs: "
            f"{', '.join([a.name for a in triage.handoffs])}"
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

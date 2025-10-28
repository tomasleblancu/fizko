"""Multi-Agent System Orchestrator for Fizko platform."""

from __future__ import annotations

import logging
from typing import Any

from agents import Agent, handoff, RunContextWrapper
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..general_knowledge_agent import create_general_knowledge_agent
from ..specialized import create_tax_documents_agent
from ..supervisor_agent import create_supervisor_agent

logger = logging.getLogger(__name__)


class HandoffMetadata(BaseModel):
    """Metadata captured when a handoff occurs."""
    reason: str
    confidence: float | None = None


class MultiAgentOrchestrator:
    """
    Orchestrator for the multi-agent Fizko system.

    This class manages:
    - Creation of all agents (Supervisor + 2 specialized agents)
    - Handoff configuration between agents
    - Agent lifecycle and state management

    Architecture:
        Supervisor (gpt-4o-mini) → General Knowledge (gpt-5-nano)
                                 → Tax Documents (gpt-5-nano)
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

        # Create all agents
        self.agents["supervisor_agent"] = create_supervisor_agent(
            db=self.db, openai_client=self.openai_client
        )
        self.agents["general_knowledge_agent"] = create_general_knowledge_agent(
            db=self.db, openai_client=self.openai_client
        )
        self.agents["tax_documents_agent"] = create_tax_documents_agent(
            db=self.db, openai_client=self.openai_client
        )

        # Configure handoffs
        self._configure_supervisor_handoffs()
        self._configure_bidirectional_handoffs()

        total_init_time = time.time() - init_start
        logger.info(f"🏗️  Orchestrator init: {total_init_time:.3f}s (3 agents + handoffs)")

    def _configure_supervisor_handoffs(self):
        """Configure handoffs for the Supervisor Agent to all specialized agents."""
        supervisor = self.agents["supervisor_agent"]

        # Callback functions for handoff tracking
        async def on_handoff_to_general_knowledge(
            ctx: RunContextWrapper, input_data: HandoffMetadata | None = None
        ):
            reason = input_data.reason if input_data else "No reason"
            logger.info(f"🧠 → General Knowledge | {reason}")

        async def on_handoff_to_tax_documents(
            ctx: RunContextWrapper, input_data: HandoffMetadata | None = None
        ):
            reason = input_data.reason if input_data else "No reason"
            logger.info(f"📄 → Tax Documents | {reason}")

        # Add handoffs to specialized agents with callbacks and metadata
        supervisor.handoffs = [
            handoff(
                agent=self.agents["general_knowledge_agent"],
                on_handoff=on_handoff_to_general_knowledge,
                input_type=HandoffMetadata,
                tool_description_override=(
                    "Transfer to General Knowledge expert for conceptual questions, "
                    "tax theory, definitions, deadlines, and educational queries. "
                    "Provide a brief reason for the transfer."
                ),
            ),
            handoff(
                agent=self.agents["tax_documents_agent"],
                on_handoff=on_handoff_to_tax_documents,
                input_type=HandoffMetadata,
                tool_description_override=(
                    "Transfer to Tax Documents expert for real document data, "
                    "invoices, receipts, summaries, and document searches. "
                    "Provide a brief reason for the transfer."
                ),
            ),
        ]

    def _configure_bidirectional_handoffs(self):
        """
        Configure bidirectional handoffs - allow specialized agents to return to supervisor.

        This enables agents to hand back control if the user changes topic completely.
        """
        supervisor = self.agents["supervisor_agent"]

        # Callback for returning to supervisor
        async def on_return_to_supervisor(
            ctx: RunContextWrapper, input_data: HandoffMetadata | None = None
        ):
            reason = input_data.reason if input_data else "Topic change"
            logger.info(f"🔄 → Supervisor | {reason}")

        # Add return-to-supervisor handoff to each specialized agent
        for agent_name in ["general_knowledge_agent", "tax_documents_agent"]:
            agent = self.agents[agent_name]
            agent.handoffs = [
                handoff(
                    agent=supervisor,
                    on_handoff=on_return_to_supervisor,
                    input_type=HandoffMetadata,
                    tool_name_override="return_to_main_menu",
                    tool_description_override=(
                        "Return to main menu if user wants to change topic completely "
                        "or ask about a different area. Provide a brief reason for returning."
                    ),
                )
            ]

    def get_agent(self, agent_name: str) -> Agent | None:
        """Get a specific agent by name."""
        return self.agents.get(agent_name)

    def get_supervisor_agent(self) -> Agent:
        """Get the Supervisor Agent (entry point)."""
        return self.agents["supervisor_agent"]

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

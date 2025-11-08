"""Multi-Agent System Orchestrator for Fizko platform."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from agents import Agent, handoff, RunContextWrapper
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..specialized import (
    create_general_knowledge_agent,
    create_tax_documents_agent,
    create_payroll_agent,
    create_settings_agent,
)
from ..supervisor_agent import create_supervisor_agent
from ..core.subscription_guard import SubscriptionGuard
from ..core.subscription_responses import create_agent_block_response

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
                                 → Payroll (gpt-5-nano)
                                 → Settings (gpt-5-nano)
    """

    def __init__(
        self,
        db: AsyncSession,
        openai_client: AsyncOpenAI,
        available_agents: list[str],
        user_id: str | None = None,
        thread_id: str | None = None,
        company_id: UUID | None = None,
        vector_store_ids: list[str] | None = None,
        channel: str = "web",
    ):
        self.db = db
        self.openai_client = openai_client
        self.user_id = user_id
        self.thread_id = thread_id
        self.company_id = company_id
        self.vector_store_ids = vector_store_ids
        self.channel = channel
        self.agents: dict[str, Agent] = {}
        self._available_agents = available_agents
        self._initialize_agents()

    async def _get_available_agents_for_company(self) -> list[str]:
        """
        Get list of agents available based on company subscription.

        Returns:
            List of agent names that company has access to
        """
        if not self.company_id:
            # No company_id: allow all agents (e.g., anonymous users, testing)
            logger.info("⚠️  No company_id provided, allowing access to all agents")
            return ["general_knowledge", "tax_documents", "payroll", "settings"]

        # Check subscription access
        guard = SubscriptionGuard(self.db)
        available = await guard.get_available_agents(self.company_id)

        logger.info(
            f"🔐 Subscription check | Company: {self.company_id} | "
            f"Available agents: {', '.join(available) if available else 'none'}"
        )

        return available

    def _initialize_agents(self):
        """Initialize all agents based on subscription access (pre-validated)."""
        import time
        init_start = time.time()

        # _available_agents is now passed from factory function (already validated)
        logger.info(
            f"🔐 Initializing agents | Company: {self.company_id} | "
            f"Available: {', '.join(self._available_agents) if self._available_agents else 'none'}"
        )

        # Always create supervisor
        self.agents["supervisor_agent"] = create_supervisor_agent(
            db=self.db, openai_client=self.openai_client
        )

        # Create only available agents
        if "general_knowledge" in self._available_agents:
            self.agents["general_knowledge_agent"] = create_general_knowledge_agent(
                db=self.db, openai_client=self.openai_client,
                vector_store_ids=self.vector_store_ids
            )
            logger.debug("✅ Created general_knowledge_agent")

        if "tax_documents" in self._available_agents:
            self.agents["tax_documents_agent"] = create_tax_documents_agent(
                db=self.db, openai_client=self.openai_client,
                vector_store_ids=self.vector_store_ids
            )
            logger.debug("✅ Created tax_documents_agent")

        if "payroll" in self._available_agents:
            self.agents["payroll_agent"] = create_payroll_agent(
                db=self.db, openai_client=self.openai_client, channel=self.channel
            )
            logger.debug("✅ Created payroll_agent")
        else:
            logger.info("🔒 Payroll agent blocked by subscription")

        if "settings" in self._available_agents:
            self.agents["settings_agent"] = create_settings_agent(
                db=self.db, openai_client=self.openai_client
            )
            logger.debug("✅ Created settings_agent")

        # Configure handoffs (only for available agents)
        self._configure_supervisor_handoffs()
        self._configure_bidirectional_handoffs()

        total_init_time = time.time() - init_start
        agent_count = len(self.agents)
        logger.info(
            f"🏗️  Orchestrator init: {total_init_time:.3f}s "
            f"({agent_count} agents + handoffs) | Available: {', '.join(self._available_agents)}"
        )

    def _configure_supervisor_handoffs(self):
        """Configure handoffs for the Supervisor Agent with subscription validation."""
        supervisor = self.agents["supervisor_agent"]
        handoffs_list = []

        # Helper to create handoff with subscription check
        def create_handoff_with_check(
            agent_name: str,
            agent_key: str,
            display_name: str,
            icon: str,
            description: str
        ):
            """Create a handoff that validates subscription before transferring."""

            async def on_handoff(
                ctx: RunContextWrapper, input_data: HandoffMetadata | None = None
            ):
                reason = input_data.reason if input_data else "No reason"

                # Check if agent is available (was created)
                if agent_key not in self.agents:
                    # Agent not created = blocked by subscription
                    logger.info(
                        f"🔒 Handoff blocked: {agent_name} | Reason: {reason}"
                    )

                    # Return block response for supervisor to process
                    block_response = create_agent_block_response(agent_name)
                    return block_response

                # Agent available - proceed with handoff
                agent = self.agents[agent_key]
                logger.info(
                    f"{icon} → {display_name} | {reason} | "
                    f"Tools: {len(agent.tools)}"
                )

            # Only add handoff if agent exists
            if agent_key in self.agents:
                return handoff(
                    agent=self.agents[agent_key],
                    on_handoff=on_handoff,
                    input_type=HandoffMetadata,
                    tool_description_override=description,
                )
            else:
                # Agent blocked - create dummy handoff that always returns block response
                # This allows supervisor to attempt handoff and receive structured error
                logger.debug(f"Creating block-only handoff for {agent_name}")
                return None  # We'll filter None values

        # Configure handoffs for all agents (available or not)
        # General Knowledge
        gk_handoff = create_handoff_with_check(
            agent_name="general_knowledge",
            agent_key="general_knowledge_agent",
            display_name="General Knowledge",
            icon="🧠",
            description=(
                "Transfer to General Knowledge expert for conceptual questions, "
                "tax theory, definitions, deadlines, and educational queries. "
                "Provide a brief reason for the transfer."
            ),
        )
        if gk_handoff:
            handoffs_list.append(gk_handoff)

        # Tax Documents
        td_handoff = create_handoff_with_check(
            agent_name="tax_documents",
            agent_key="tax_documents_agent",
            display_name="Tax Documents",
            icon="📄",
            description=(
                "Transfer to Tax Documents expert for real document data, "
                "invoices, receipts, summaries, and document searches. "
                "Provide a brief reason for the transfer."
            ),
        )
        if td_handoff:
            handoffs_list.append(td_handoff)

        # Payroll (may be blocked)
        payroll_handoff = create_handoff_with_check(
            agent_name="payroll",
            agent_key="payroll_agent",
            display_name="Payroll",
            icon="💼",
            description=(
                "Transfer to Payroll expert for labor law questions, "
                "employee management, payroll processing, and work contracts. "
                "Provide a brief reason for the transfer."
            ),
        )
        if payroll_handoff:
            handoffs_list.append(payroll_handoff)

        # Settings
        settings_handoff = create_handoff_with_check(
            agent_name="settings",
            agent_key="settings_agent",
            display_name="Settings",
            icon="⚙️",
            description=(
                "Transfer to Settings expert for managing user preferences, "
                "notification settings, and account configuration. "
                "Provide a brief reason for the transfer."
            ),
        )
        if settings_handoff:
            handoffs_list.append(settings_handoff)

        supervisor.handoffs = handoffs_list
        logger.debug(f"Configured {len(handoffs_list)} handoffs for supervisor")

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

        # Add return-to-supervisor handoff to each specialized agent (only if created)
        # Disabled by default to prevent unnecessary handoffs
        for agent_name in ["general_knowledge_agent", "tax_documents_agent", "payroll_agent", "settings_agent"]:
            # Skip if agent was not created (blocked by subscription)
            if agent_name not in self.agents:
                continue

            agent = self.agents[agent_name]
            agent.handoffs = [
                handoff(
                    agent=supervisor,
                    on_handoff=on_return_to_supervisor,
                    input_type=HandoffMetadata,
                    tool_name_override="return_to_main_menu",
                    tool_description_override=(
                        "Return to main menu ONLY if user explicitly requests a completely different topic "
                        "(e.g., switching from documents to tax concepts, or vice versa). "
                        "Do NOT use for simple acknowledgments like 'thanks', 'ok', 'got it'. "
                        "Stay in current conversation for follow-up questions."
                    ),
                    is_enabled=False,  # Disabled to prevent unnecessary handoffs
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


async def create_multi_agent_orchestrator(
    db: AsyncSession,
    openai_client: AsyncOpenAI,
    user_id: str | None = None,
    thread_id: str | None = None,
    company_id: UUID | None = None,
    vector_store_ids: list[str] | None = None,
    channel: str = "web",
) -> MultiAgentOrchestrator:
    """
    Factory function to create a MultiAgentOrchestrator (async).

    This function validates subscription access BEFORE creating the orchestrator,
    ensuring only allowed agents are initialized.

    Args:
        db: Database session
        openai_client: OpenAI client
        user_id: Optional user ID
        thread_id: Optional ChatKit thread ID
        company_id: Optional company ID (for subscription validation)
        vector_store_ids: Optional list of vector store IDs for FileSearchTool
        channel: Communication channel ("web" or "whatsapp")

    Returns:
        Configured MultiAgentOrchestrator instance with only allowed agents
    """
    # Validate subscription access BEFORE creating orchestrator
    if company_id:
        guard = SubscriptionGuard(db)
        available_agents = await guard.get_available_agents(company_id)
        logger.info(
            f"🔐 Pre-init subscription check | Company: {company_id} | "
            f"Available agents: {', '.join(available_agents) if available_agents else 'none'}"
        )
    else:
        # No company_id: allow all agents (anonymous, testing)
        available_agents = ["general_knowledge", "tax_documents", "payroll", "settings"]
        logger.info("⚠️  No company_id provided, allowing all agents")

    return MultiAgentOrchestrator(
        db=db,
        openai_client=openai_client,
        available_agents=available_agents,
        user_id=user_id,
        thread_id=thread_id,
        company_id=company_id,
        vector_store_ids=vector_store_ids,
        channel=channel,
    )

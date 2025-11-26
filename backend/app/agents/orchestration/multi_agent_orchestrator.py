"""Multi-Agent System Orchestrator for Fizko platform."""

from __future__ import annotations

import logging
from uuid import UUID

from agents import Agent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from .subscription_validator import SubscriptionValidator
from .agent_factory import AgentFactory
from .handoff_factory import HandoffFactory
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """
    Orchestrator for the multi-agent Fizko system.

    This class manages:
    - Creation of all agents (Classifier + specialized agents)
    - Handoff configuration between agents
    - Agent lifecycle and state management
    - Agent persistence across conversation turns

    Architecture:
        User Query → Classifier (gpt-4o-mini) → Analyzes → Classifies → Handoff
                                                                           ↓
                     Specialized Agents (gpt-5-nano) ← ← ← ← ← ← ← ← ← ← ┘
                       - General Knowledge (NON-STICKY)
                       - Tax Documents (NON-STICKY)
                       - Monthly Taxes F29 (NON-STICKY)
                       - Payroll (STICKY)
                       - Settings (STICKY)
                       - Expense (STICKY)
                       - Feedback (STICKY)

    The Classifier is NOT conversational - it only routes queries to specialists.

    Sticky vs Non-Sticky:
    - STICKY: Persists across messages (expense, feedback, payroll, settings)
    - NON-STICKY: Always returns to classifier (general_knowledge, tax_documents, monthly_taxes)
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
        self._available_agents = available_agents

        # Initialize managers
        self.session_manager = SessionManager()

        # Initialize agents
        self.agents: dict[str, Agent] = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all agents and configure handoffs."""
        import time
        init_start = time.time()

        logger.info(
            f"🔐 Initializing agents | Company: {self.company_id} | "
            f"Available: {', '.join(self._available_agents) if self._available_agents else 'none'}"
        )

        # Create agents using factory
        agent_factory = AgentFactory(
            db=self.db,
            openai_client=self.openai_client,
            vector_store_ids=self.vector_store_ids,
            channel=self.channel
        )
        self.agents = agent_factory.create_available_agents(self._available_agents)

        # Configure handoffs
        self._configure_supervisor_handoffs()

        total_init_time = time.time() - init_start
        agent_count = len(self.agents)
        logger.info(
            f"🏗️  Orchestrator init: {total_init_time:.3f}s "
            f"({agent_count} agents + handoffs) | Available: {', '.join(self._available_agents)}"
        )

    def _configure_supervisor_handoffs(self):
        """Configure handoffs for the Classifier Agent with subscription validation."""
        classifier = self.agents["supervisor_agent"]  # Keep key name for compatibility

        # Create handoff factory with session manager for persistence
        handoff_factory = HandoffFactory(self.agents, self.session_manager)

        # Get standard handoff configurations
        configs = handoff_factory.get_standard_configs()

        # Create handoffs for available agents only
        handoffs_list = []
        for config in configs:
            handoff_obj = handoff_factory.create_validated_handoff(config)
            if handoff_obj:
                handoffs_list.append(handoff_obj)

        classifier.handoffs = handoffs_list
        logger.debug(f"Configured {len(handoffs_list)} handoffs for classifier")

    def get_agent(self, agent_name: str) -> Agent | None:
        """Get a specific agent by name."""
        return self.agents.get(agent_name)

    def get_supervisor_agent(self) -> Agent:
        """Get the Classifier Agent (entry point for classification and routing)."""
        return self.agents["supervisor_agent"]

    def list_agents(self) -> list[str]:
        """List all available agent names."""
        return list(self.agents.keys())

    async def get_active_agent(self) -> Agent | None:
        """
        Get the currently active agent from session state.

        Returns:
            Active agent if one is set, None otherwise
        """
        if not self.thread_id:
            return None

        active_agent_key = await self.session_manager.get_active_agent(self.thread_id)
        if active_agent_key:
            return self.get_agent(active_agent_key)

        return None

    async def set_active_agent(self, agent_key: str) -> bool:
        """
        Set the active agent for the current session.

        Args:
            agent_key: Agent key to set as active

        Returns:
            True if successful
        """
        if not self.thread_id:
            logger.warning("Cannot set active agent: no thread_id")
            return False

        return await self.session_manager.set_active_agent(self.thread_id, agent_key)

    async def clear_active_agent(self) -> bool:
        """
        Clear the active agent (return to supervisor).

        Returns:
            True if successful
        """
        if not self.thread_id:
            logger.warning("Cannot clear active agent: no thread_id")
            return False

        return await self.session_manager.clear_active_agent(self.thread_id)


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
    # Validate subscription access using validator
    # For channels without DB (expo), allow all agents
    if db is None:
        logger.info(f"⚠️  No DB provided (channel={channel}), allowing all agents")
        available_agents = [
            "general_knowledge",
            "tax_documents",
            "f29",
            "payroll",
            "settings",
            "expense",
            "feedback"
        ]
    else:
        validator = SubscriptionValidator(db)
        available_agents = await validator.get_available_agents(company_id)

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

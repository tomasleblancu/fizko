"""Agent factory module for creating specialized agents."""

from __future__ import annotations

import logging

from agents import Agent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ..specialized import (
    create_general_knowledge_agent,
    create_tax_documents_agent,
    create_monthly_taxes_agent,
    create_payroll_agent,
    create_settings_agent,
    create_expense_agent,
    create_feedback_agent,
)
from ..supervisor_agent import create_supervisor_agent

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating agents based on subscription access.

    This class handles conditional agent creation and initialization,
    separating agent instantiation logic from orchestration.
    """

    def __init__(
        self,
        db: AsyncSession,
        openai_client: AsyncOpenAI,
        vector_store_ids: list[str] | None = None,
        channel: str = "web",
    ):
        self.db = db
        self.openai_client = openai_client
        self.vector_store_ids = vector_store_ids
        self.channel = channel

    def create_supervisor(self) -> Agent:
        """
        Create the supervisor agent (always created).

        Returns:
            Supervisor agent instance
        """
        return create_supervisor_agent(
            db=self.db,
            openai_client=self.openai_client
        )

    def create_available_agents(self, available_agent_names: list[str]) -> dict[str, Agent]:
        """
        Create all available agents based on subscription access.

        Args:
            available_agent_names: List of agent names to create

        Returns:
            Dictionary mapping agent keys to Agent instances
        """
        agents: dict[str, Agent] = {}

        # Always create supervisor
        agents["supervisor_agent"] = self.create_supervisor()

        # Create only available agents
        if "general_knowledge" in available_agent_names:
            agents["general_knowledge_agent"] = create_general_knowledge_agent(
                db=self.db,
                openai_client=self.openai_client,
                vector_store_ids=self.vector_store_ids
            )
            logger.debug("✅ Created general_knowledge_agent")

        if "tax_documents" in available_agent_names:
            agents["tax_documents_agent"] = create_tax_documents_agent(
                db=self.db,
                openai_client=self.openai_client,
                vector_store_ids=self.vector_store_ids
            )
            logger.debug("✅ Created tax_documents_agent")

        if "f29" in available_agent_names:
            agents["monthly_taxes_agent"] = create_monthly_taxes_agent(
                db=self.db,
                openai_client=self.openai_client,
                vector_store_ids=self.vector_store_ids
            )
            logger.debug("✅ Created monthly_taxes_agent")

        if "payroll" in available_agent_names:
            agents["payroll_agent"] = create_payroll_agent(
                db=self.db,
                openai_client=self.openai_client,
                channel=self.channel
            )
            logger.debug("✅ Created payroll_agent")
        else:
            logger.info("🔒 Payroll agent blocked by subscription")

        if "settings" in available_agent_names:
            agents["settings_agent"] = create_settings_agent(
                db=self.db,
                openai_client=self.openai_client
            )
            logger.debug("✅ Created settings_agent")

        if "expense" in available_agent_names:
            agents["expense_agent"] = create_expense_agent(
                db=self.db,
                openai_client=self.openai_client
            )
            logger.debug("✅ Created expense_agent")

        if "feedback" in available_agent_names:
            agents["feedback_agent"] = create_feedback_agent(
                db=self.db,
                openai_client=self.openai_client
            )
            logger.debug("✅ Created feedback_agent")

        return agents

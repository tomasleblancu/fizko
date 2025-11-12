"""Subscription validation module for multi-agent orchestration."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.subscription_guard import SubscriptionGuard

logger = logging.getLogger(__name__)


class SubscriptionValidator:
    """
    Validates company subscription access to agents.

    This class centralizes all subscription validation logic,
    making it easier to test and maintain.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.guard = SubscriptionGuard(db)

    async def get_available_agents(self, company_id: UUID | None) -> list[str]:
        """
        Get list of agents available based on company subscription.

        Args:
            company_id: Company UUID (None allows all agents)

        Returns:
            List of agent names that company has access to
        """
        if not company_id:
            # No company_id: allow all agents (e.g., anonymous users, testing)
            logger.info("⚠️  No company_id provided, allowing access to all agents")
            return self._get_all_agent_names()

        # Check subscription access
        available = await self.guard.get_available_agents(company_id)

        logger.info(
            f"🔐 Subscription check | Company: {company_id} | "
            f"Available agents: {', '.join(available) if available else 'none'}"
        )

        return available

    def is_agent_available(self, agent_name: str, available_agents: list[str]) -> bool:
        """
        Check if a specific agent is available.

        Args:
            agent_name: Name of the agent to check
            available_agents: List of available agent names

        Returns:
            True if agent is available, False otherwise
        """
        return agent_name in available_agents

    @staticmethod
    def _get_all_agent_names() -> list[str]:
        """Get list of all possible agent names."""
        return [
            "general_knowledge",
            "tax_documents",
            "f29",
            "payroll",
            "settings",
            "expense",
            "feedback"
        ]

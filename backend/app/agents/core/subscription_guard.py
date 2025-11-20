"""
Subscription Guard - Stub for Backend V2 (no database).

This is a simplified version that always allows all agents and tools.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class SubscriptionGuard:
    """
    Stub subscription guard for backend-v2 (no database).

    This version always allows access to all agents and tools since backend-v2
    doesn't have a subscription system.
    """

    def __init__(self, db=None):
        """Initialize the subscription guard stub (db parameter ignored)."""
        pass

    async def can_use_agent(
        self, company_id: UUID, agent_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a company can use a specific agent (always True in backend-v2).

        Args:
            company_id: Company UUID (ignored)
            agent_name: Agent name (ignored)

        Returns:
            Tuple of (True, None) - always allows access
        """
        return True, None

    async def can_use_tool(
        self, company_id: UUID, tool_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a company can use a specific tool (always True in backend-v2).

        Args:
            company_id: Company UUID (ignored)
            tool_name: Tool name (ignored)

        Returns:
            Tuple of (True, None) - always allows access
        """
        return True, None

    async def get_available_agents(self, company_id: UUID) -> list[str]:
        """
        Get list of all available agents (backend-v2 allows all).

        Args:
            company_id: Company UUID (ignored)

        Returns:
            List of all agent names
        """
        all_agents = [
            "general_knowledge",
            "tax_documents",
            "f29",
            "payroll",
            "settings",
            "expense",
            "feedback",
        ]
        logger.debug(f"📋 Available agents (backend-v2): {', '.join(all_agents)}")
        return all_agents

    async def get_available_tools(
        self, company_id: UUID, tool_names: list[str]
    ) -> list[str]:
        """
        Get list of available tools (backend-v2 allows all).

        Args:
            company_id: Company UUID (ignored)
            tool_names: List of tool names to check

        Returns:
            All provided tool names (all allowed)
        """
        return tool_names

"""
Subscription Guard - Validates agent and tool access based on subscription plan.

This module provides a guard system for checking whether a company has access
to specific agents or tools based on their subscription plan.

Usage:
    guard = SubscriptionGuard(db)
    can_use, error_msg = await guard.can_use_agent(company_id, "payroll")
    if not can_use:
        # Handle blocked access
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.subscriptions import SubscriptionService

logger = logging.getLogger(__name__)


class SubscriptionGuard:
    """
    Guard for validating access to agents and tools based on subscription.

    This class wraps the SubscriptionService to provide agent/tool-specific
    validation logic. It checks the subscription plan's features to determine
    if a company has access to specific agents or tools.

    Features are stored in subscription plans as:
    {
        "agents": {
            "general_knowledge": true,
            "tax_documents": true,
            "payroll": false,  // Requires Pro+
            "settings": true
        },
        "tools": {
            "get_documents": true,
            "get_f29_data": false,  // Requires Pro+
            "calculate_payroll": false  // Requires Enterprise
        }
    }
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the subscription guard.

        Args:
            db: Database session
        """
        self.service = SubscriptionService(db)

    async def can_use_agent(
        self, company_id: UUID, agent_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a company can use a specific agent.

        Args:
            company_id: Company UUID
            agent_name: Agent name (e.g., "payroll", "tax_documents")

        Returns:
            Tuple of (can_use, error_message)
            - can_use: True if company has access
            - error_message: None if access granted, error string if denied

        Example:
            >>> guard = SubscriptionGuard(db)
            >>> can_use, msg = await guard.can_use_agent(company_id, "payroll")
            >>> if not can_use:
            >>>     print(msg)  # "Agent 'payroll' requires Pro+ plan"
        """
        # Check feature access
        feature_key = f"agents.{agent_name}"
        has_access = await self._check_nested_feature(company_id, feature_key)

        if not has_access:
            # Get plan name for better error message
            subscription = await self.service.get_company_subscription(company_id)
            current_plan = (
                subscription.plan.name if subscription and subscription.plan else "Free"
            )

            error_msg = (
                f"Agent '{agent_name}' is not available in your current plan ({current_plan})"
            )
            logger.info(
                f"🔒 Agent blocked: {agent_name} | Company: {company_id} | Current plan: {current_plan}"
            )
            return False, error_msg

        logger.debug(f"✅ Agent access granted: {agent_name} | Company: {company_id}")
        return True, None

    async def can_use_tool(
        self, company_id: UUID, tool_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a company can use a specific tool.

        Args:
            company_id: Company UUID
            tool_name: Tool name (e.g., "get_f29_data", "calculate_payroll")

        Returns:
            Tuple of (can_use, error_message)
            - can_use: True if company has access
            - error_message: None if access granted, error string if denied

        Example:
            >>> guard = SubscriptionGuard(db)
            >>> can_use, msg = await guard.can_use_tool(company_id, "get_f29_data")
            >>> if not can_use:
            >>>     return {"error": msg}
        """
        # Check feature access
        feature_key = f"tools.{tool_name}"
        has_access = await self._check_nested_feature(company_id, feature_key)

        if not has_access:
            # Get plan name for better error message
            subscription = await self.service.get_company_subscription(company_id)
            current_plan = (
                subscription.plan.name if subscription and subscription.plan else "Free"
            )

            error_msg = (
                f"Tool '{tool_name}' is not available in your current plan ({current_plan})"
            )
            logger.info(
                f"🔒 Tool blocked: {tool_name} | Company: {company_id} | Current plan: {current_plan}"
            )
            return False, error_msg

        logger.debug(f"✅ Tool access granted: {tool_name} | Company: {company_id}")
        return True, None

    async def get_available_agents(self, company_id: UUID) -> list[str]:
        """
        Get list of agent names available to a company based on subscription.

        Args:
            company_id: Company UUID

        Returns:
            List of agent names (e.g., ["general_knowledge", "tax_documents"])

        Example:
            >>> guard = SubscriptionGuard(db)
            >>> agents = await guard.get_available_agents(company_id)
            >>> print(agents)  # ["general_knowledge", "tax_documents", "settings"]
        """
        # All possible agents
        all_agents = ["general_knowledge", "tax_documents", "payroll", "settings"]

        available = []
        for agent_name in all_agents:
            can_use, _ = await self.can_use_agent(company_id, agent_name)
            if can_use:
                available.append(agent_name)

        logger.info(
            f"📋 Available agents for company {company_id}: {', '.join(available)}"
        )
        return available

    async def get_available_tools(
        self, company_id: UUID, tool_names: list[str]
    ) -> list[str]:
        """
        Get list of tool names available to a company from a given set.

        Args:
            company_id: Company UUID
            tool_names: List of tool names to check

        Returns:
            List of available tool names

        Example:
            >>> guard = SubscriptionGuard(db)
            >>> all_tools = ["get_documents", "get_f29_data", "calculate_payroll"]
            >>> available = await guard.get_available_tools(company_id, all_tools)
            >>> print(available)  # ["get_documents"]
        """
        available = []
        for tool_name in tool_names:
            can_use, _ = await self.can_use_tool(company_id, tool_name)
            if can_use:
                available.append(tool_name)

        return available

    async def _check_nested_feature(self, company_id: UUID, feature_key: str) -> bool:
        """
        Check nested feature access (e.g., "agents.payroll" or "tools.get_f29_data").

        Supports both flat and nested feature structures:
        - Flat: {"has_whatsapp": true}
        - Nested: {"agents": {"payroll": true}}

        Args:
            company_id: Company UUID
            feature_key: Dot-separated feature path (e.g., "agents.payroll")

        Returns:
            True if feature is available, False otherwise
        """
        subscription = await self.service.get_company_subscription(company_id)

        if not subscription:
            logger.debug(f"No subscription found for company {company_id}")
            return False

        # Check if subscription is active
        if subscription.status not in ["trialing", "active"]:
            logger.debug(
                f"Subscription not active for company {company_id}: {subscription.status}"
            )
            return False

        # Parse nested key
        features = subscription.plan.features
        keys = feature_key.split(".")

        # Navigate nested structure
        current = features
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                # Feature not found in plan
                logger.debug(f"Feature '{feature_key}' not found in plan features")
                return False

        # Check if final value is True
        return current is True


async def check_agent_access(
    db: AsyncSession, company_id: UUID, agent_name: str
) -> bool:
    """
    Helper function to quickly check agent access.

    Args:
        db: Database session
        company_id: Company UUID
        agent_name: Agent name

    Returns:
        True if company has access, False otherwise

    Example:
        >>> has_access = await check_agent_access(db, company_id, "payroll")
        >>> if not has_access:
        >>>     return {"error": "Access denied"}
    """
    guard = SubscriptionGuard(db)
    can_use, _ = await guard.can_use_agent(company_id, agent_name)
    return can_use


async def check_tool_access(
    db: AsyncSession, company_id: UUID, tool_name: str
) -> bool:
    """
    Helper function to quickly check tool access.

    Args:
        db: Database session
        company_id: Company UUID
        tool_name: Tool name

    Returns:
        True if company has access, False otherwise

    Example:
        >>> has_access = await check_tool_access(db, company_id, "get_f29_data")
        >>> if not has_access:
        >>>     return {"error": "Feature not available"}
    """
    guard = SubscriptionGuard(db)
    can_use, _ = await guard.can_use_tool(company_id, tool_name)
    return can_use

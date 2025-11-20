"""
Subscription Response Builders - Stub for Backend V2.

This is a simplified version that doesn't block any tools (no subscription system).
"""

from __future__ import annotations

from typing import Literal, TypedDict


class SubscriptionBlockResponse(TypedDict):
    """Structured response when an agent or tool is blocked."""

    blocked: Literal[True]
    blocked_type: Literal["agent", "tool"]
    blocked_item: str
    display_name: str
    plan_required: str
    user_message: str
    benefits: list[str]
    upgrade_url: str
    alternative_message: str | None


def create_agent_block_response(agent_name: str) -> SubscriptionBlockResponse:
    """
    Generate a structured response when an agent is blocked (stub - never blocks).

    Args:
        agent_name: Name of the blocked agent

    Returns:
        SubscriptionBlockResponse (not used in backend-v2)
    """
    return {
        "blocked": True,
        "blocked_type": "agent",
        "blocked_item": agent_name,
        "display_name": agent_name,
        "plan_required": "pro",
        "user_message": f"Agent '{agent_name}' is not available.",
        "benefits": [],
        "upgrade_url": "",
        "alternative_message": None,
    }


def create_tool_block_response(tool_name: str) -> SubscriptionBlockResponse:
    """
    Generate a structured response when a tool is blocked (stub - never blocks).

    Args:
        tool_name: Name of the blocked tool

    Returns:
        SubscriptionBlockResponse (not used in backend-v2)
    """
    return {
        "blocked": True,
        "blocked_type": "tool",
        "blocked_item": tool_name,
        "display_name": tool_name,
        "plan_required": "pro",
        "user_message": f"Tool '{tool_name}' is not available.",
        "benefits": [],
        "upgrade_url": "",
        "alternative_message": None,
    }

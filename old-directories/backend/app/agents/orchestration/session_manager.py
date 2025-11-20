"""Session manager for tracking active agent state and persistence."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages agent session state for persistence.

    This class tracks which specialized agent is currently active for a given
    conversation thread, enabling agent persistence across multiple messages.

    Key responsibilities:
    1. Track active agent in-memory per thread
    2. Persist agent state across message turns within the same orchestrator instance
    3. Clear agent state when returning to supervisor

    Implementation:
    - Uses in-memory dictionary for simplicity and speed
    - Thread-safe within same orchestrator instance (cached per thread_id)
    - Cleared when orchestrator cache is cleared
    """

    def __init__(self):
        """Initialize session manager with in-memory storage."""
        self._active_agents: dict[str, str] = {}

    async def get_active_agent(self, thread_id: str) -> str | None:
        """
        Get the currently active agent for a thread.

        Args:
            thread_id: ChatKit thread ID

        Returns:
            Agent key (e.g., "payroll_agent") or None if no active agent
        """
        active_agent = self._active_agents.get(thread_id)

        if active_agent:
            logger.info(
                f"🎯 [STICKY AGENT] Active: {active_agent} | "
                f"Thread: {thread_id[:12]}... | "
                f"Total tracked: {len(self._active_agents)}"
            )
        else:
            logger.info(
                f"👔 [STICKY AGENT] No active (using supervisor) | "
                f"Thread: {thread_id[:12]}... | "
                f"Total tracked: {len(self._active_agents)}"
            )

        return active_agent

    async def set_active_agent(self, thread_id: str, agent_key: str) -> bool:
        """
        Set the active agent for a thread.

        Args:
            thread_id: ChatKit thread ID
            agent_key: Agent key to set as active (e.g., "payroll_agent")

        Returns:
            True if successful
        """
        was_new = thread_id not in self._active_agents
        self._active_agents[thread_id] = agent_key

        logger.info(
            f"✅ [STICKY AGENT] {'New' if was_new else 'Updated'}: {agent_key} | "
            f"Thread: {thread_id[:12]}... | "
            f"Total tracked: {len(self._active_agents)}"
        )
        return True

    async def clear_active_agent(self, thread_id: str) -> bool:
        """
        Clear the active agent for a thread (return to supervisor).

        Args:
            thread_id: ChatKit thread ID

        Returns:
            True if successful
        """
        if thread_id in self._active_agents:
            agent_key = self._active_agents[thread_id]
            del self._active_agents[thread_id]
            logger.info(
                f"🧹 [STICKY AGENT] Cleared: {agent_key} → supervisor | "
                f"Thread: {thread_id[:12]}... | "
                f"Total tracked: {len(self._active_agents)}"
            )
        else:
            logger.info(
                f"⚪ [STICKY AGENT] Nothing to clear (already supervisor) | "
                f"Thread: {thread_id[:12]}..."
            )

        return True

    def get_all_active_agents(self) -> dict[str, str]:
        """
        Get all active agents across all threads.

        Returns:
            Dictionary mapping thread_id to agent_key
        """
        return self._active_agents.copy()

    def clear_all(self):
        """Clear all active agent state."""
        self._active_agents.clear()
        logger.info("🗑️  Cleared all active agent state")

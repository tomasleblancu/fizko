"""Session manager for tracking active agent state and persistence."""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages agent session state for persistence.

    This class tracks which specialized agent is currently active for a given
    conversation thread, enabling agent persistence across multiple messages.

    Key responsibilities:
    1. Track active agent in thread metadata
    2. Persist agent state across message turns
    3. Clear agent state when returning to supervisor
    """

    def __init__(self, openai_client: AsyncOpenAI):
        """
        Initialize session manager.

        Args:
            openai_client: OpenAI client for thread metadata operations
        """
        self.openai_client = openai_client
        self._metadata_key = "active_agent"

    async def get_active_agent(self, thread_id: str) -> str | None:
        """
        Get the currently active agent for a thread.

        Args:
            thread_id: ChatKit thread ID

        Returns:
            Agent key (e.g., "payroll_agent") or None if no active agent
        """
        try:
            thread = await self.openai_client.beta.threads.retrieve(thread_id)
            metadata = thread.metadata or {}
            active_agent = metadata.get(self._metadata_key)

            if active_agent:
                logger.info(f"📌 Active agent: {active_agent} (thread: {thread_id})")
            else:
                logger.debug(f"No active agent (thread: {thread_id})")

            return active_agent

        except Exception as e:
            logger.error(f"Failed to get active agent: {e}")
            return None

    async def set_active_agent(self, thread_id: str, agent_key: str) -> bool:
        """
        Set the active agent for a thread.

        Args:
            thread_id: ChatKit thread ID
            agent_key: Agent key to set as active (e.g., "payroll_agent")

        Returns:
            True if successful, False otherwise
        """
        try:
            thread = await self.openai_client.beta.threads.retrieve(thread_id)
            current_metadata = thread.metadata or {}

            # Update metadata with active agent
            updated_metadata = {**current_metadata, self._metadata_key: agent_key}

            await self.openai_client.beta.threads.update(
                thread_id=thread_id,
                metadata=updated_metadata
            )

            logger.info(f"✅ Set active agent: {agent_key} (thread: {thread_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to set active agent: {e}")
            return False

    async def clear_active_agent(self, thread_id: str) -> bool:
        """
        Clear the active agent for a thread (return to supervisor).

        Args:
            thread_id: ChatKit thread ID

        Returns:
            True if successful, False otherwise
        """
        try:
            thread = await self.openai_client.beta.threads.retrieve(thread_id)
            current_metadata = thread.metadata or {}

            # Remove active agent from metadata
            if self._metadata_key in current_metadata:
                updated_metadata = {
                    k: v for k, v in current_metadata.items()
                    if k != self._metadata_key
                }

                await self.openai_client.beta.threads.update(
                    thread_id=thread_id,
                    metadata=updated_metadata
                )

                logger.info(f"🧹 Cleared active agent (thread: {thread_id})")
            else:
                logger.debug(f"No active agent to clear (thread: {thread_id})")

            return True

        except Exception as e:
            logger.error(f"Failed to clear active agent: {e}")
            return False

    async def get_thread_metadata(self, thread_id: str) -> dict[str, Any]:
        """
        Get full thread metadata.

        Args:
            thread_id: ChatKit thread ID

        Returns:
            Dictionary of metadata
        """
        try:
            thread = await self.openai_client.beta.threads.retrieve(thread_id)
            return thread.metadata or {}
        except Exception as e:
            logger.error(f"Failed to get thread metadata: {e}")
            return {}

"""Handoffs Manager - Request-scoped multi-agent orchestration."""

from __future__ import annotations

import logging
import os
from typing import Any
from agents import Agent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from .multi_agent_orchestrator import create_multi_agent_orchestrator

logger = logging.getLogger(__name__)


class HandoffsManager:
    """
    Manager for lazy-initialized multi-agent orchestrators.

    This solves the problem of needing DB + OpenAI client context
    which is only available per-request, not at server initialization.

    Key features:
    - Creates orchestrators on-demand per thread
    - Caches orchestrators to maintain agent state across requests
    - Handles handoffs between specialized agents

    Design:
        - Supervisor Agent (gpt-4o-mini) routes to:
          - General Knowledge Agent (gpt-5-nano) for conceptual questions
          - Tax Documents Agent (gpt-5-nano) for real data queries
    """

    def __init__(self):
        self._orchestrator_cache: dict[str, Any] = {}
        self._openai_client: AsyncOpenAI | None = None

    def _get_openai_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client (singleton)."""
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._openai_client = AsyncOpenAI(api_key=api_key)
        return self._openai_client

    async def get_orchestrator(
        self,
        thread_id: str,
        db: AsyncSession,
        user_id: str | None = None,
    ) -> Any:
        """
        Get or create a multi-agent orchestrator for a thread.

        IMPORTANT: Caches orchestrator per thread_id to maintain agent state.
        This is CRITICAL for handoffs to work across multiple requests.

        Args:
            thread_id: ChatKit thread ID
            db: Database session (scoped to this request)
            user_id: Optional user ID for context

        Returns:
            MultiAgentOrchestrator instance
        """
        # Check cache first
        if thread_id in self._orchestrator_cache:
            return self._orchestrator_cache[thread_id]

        # Create new orchestrator
        import time
        create_start = time.time()

        try:
            openai_client = self._get_openai_client()
            orchestrator = create_multi_agent_orchestrator(
                db=db,
                openai_client=openai_client,
                user_id=user_id,
                thread_id=thread_id,
            )

            # Cache for future requests
            self._orchestrator_cache[thread_id] = orchestrator

            total_time = time.time() - create_start
            logger.info(f"🔀 New orchestrator cached: {total_time:.3f}s | thread={thread_id[:8]}")

            return orchestrator

        except Exception as e:
            logger.error(f"❌ Failed to create orchestrator: {e}")
            raise

    async def get_supervisor_agent(
        self,
        thread_id: str,
        db: AsyncSession,
        user_id: str | None = None,
    ) -> Agent:
        """
        Get the Supervisor Agent for a thread (entry point for multi-agent system).

        Args:
            thread_id: ChatKit thread ID
            db: Database session
            user_id: Optional user ID

        Returns:
            Supervisor Agent instance
        """
        orchestrator = await self.get_orchestrator(
            thread_id=thread_id,
            db=db,
            user_id=user_id,
        )

        return orchestrator.get_supervisor_agent()

    async def get_all_agents(
        self,
        thread_id: str,
        db: AsyncSession,
        user_id: str | None = None,
    ) -> list[Agent]:
        """
        Get all agents for handoff support.

        This is used by the Runner to enable handoffs between agents.

        Args:
            thread_id: ChatKit thread ID
            db: Database session
            user_id: Optional user ID

        Returns:
            List of all agent instances
        """
        orchestrator = await self.get_orchestrator(
            thread_id=thread_id,
            db=db,
            user_id=user_id,
        )

        return list(orchestrator.agents.values())

    def clear_cache(self, thread_id: str | None = None):
        """
        Clear orchestrator cache.

        Args:
            thread_id: If provided, clears only this thread's cache.
                      If None, clears entire cache.
        """
        if thread_id:
            if thread_id in self._orchestrator_cache:
                del self._orchestrator_cache[thread_id]
                logger.info(f"🗑️  [HandoffsManager] Cleared cache for thread: {thread_id}")
        else:
            self._orchestrator_cache.clear()
            logger.info("🗑️  [HandoffsManager] Cleared entire orchestrator cache")

    def get_cache_size(self) -> int:
        """Get number of cached orchestrators."""
        return len(self._orchestrator_cache)

    def get_cached_threads(self) -> list[str]:
        """Get list of thread IDs with cached orchestrators."""
        return list(self._orchestrator_cache.keys())


# Global handoffs manager instance
handoffs_manager = HandoffsManager()

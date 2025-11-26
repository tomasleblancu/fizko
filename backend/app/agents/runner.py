"""
Agent Runner - Abstraction over OpenAI Agents SDK.

This module provides a clean abstraction layer over the Agents SDK,
allowing agent execution from multiple channels (ChatKit, WhatsApp, etc.)
without coupling to specific SDK implementations.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID

from agents import Runner
from openai import AsyncOpenAI

from .core import FizkoContext
from .orchestration import handoffs_manager

logger = logging.getLogger(__name__)


@dataclass
class AgentExecutionRequest:
    """
    Request to execute an agent.

    This is a channel-agnostic representation of an agent execution request,
    used by ChatKit, WhatsApp, and any other future channels.
    """
    user_id: str
    company_id: str
    thread_id: str
    message: str | List[Dict[str, Any]]  # Text string or content_parts

    # Optional context
    attachments: Optional[List[Dict[str, Any]]] = None
    ui_context: Optional[str] = None
    company_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    # Execution options
    max_turns: int = 10
    channel: str = "unknown"  # "web", "expo", "whatsapp", etc.


@dataclass
class AgentExecutionResult:
    """
    Result from agent execution (non-streaming).
    """
    response_text: str
    new_items: List[Any]
    thread_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentRunner:
    """
    Generic agent runner that abstracts Agents SDK execution.

    This class provides a unified interface for executing agents regardless
    of the channel (ChatKit web, Expo mobile, WhatsApp, etc.). It handles:
    - Multi-agent orchestration with supervisor and specialized agents
    - Session management
    - Context building
    - Execution (streaming and non-streaming)

    Does NOT handle:
    - Loading company context (done by AgentService)
    - Processing UI tools (done by AgentService)
    - Channel-specific logic (done by adapters)
    """

    def __init__(
        self,
        sessions_dir: Optional[str] = None
    ):
        """
        Initialize agent runner.

        Args:
            sessions_dir: Directory for SQLite session storage
        """
        # Setup sessions directory
        if sessions_dir is None:
            sessions_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "sessions"
            )
        self.sessions_dir = sessions_dir
        os.makedirs(self.sessions_dir, exist_ok=True)

        self.session_file = os.path.join(self.sessions_dir, "agent_sessions.db")

        logger.info("🤖 AgentRunner initialized (multi-agent mode)")

    async def execute(
        self,
        request: AgentExecutionRequest,
        db,  # AsyncSession
        stream: bool = False,
        run_config = None,
    ) -> AgentExecutionResult | AsyncIterator[Any]:
        """
        Execute agent with given request.

        Args:
            request: Execution request with all necessary context
            db: Database session (for agent creation)
            stream: Whether to stream results
            run_config: Optional RunConfig for session_input_callback

        Returns:
            AgentExecutionResult (if stream=False) or AsyncIterator of events
        """

        # 1. Get agent based on mode (creates session internally for active agent detection)
        agent, all_agents, session = await self._get_agent(request, db)

        # 2. Build agent context
        context = await self._build_context(request, db)

        # 3. Prepare agent input
        # When using session memory with simple text, pass string directly
        # Otherwise prepare full message format
        if session and isinstance(request.message, str):
            agent_input = request.message
        else:
            agent_input = self._prepare_input(request)

        # 5. Execute agent
        if stream:
            result = Runner.run_streamed(
                agent,
                agent_input,
                context=context,
                session=session,
                max_turns=request.max_turns,
                run_config=run_config,
            )
            return result
        else:
            result = await Runner.run(
                agent,
                agent_input,
                context=context,
                session=session,
                max_turns=request.max_turns,
                run_config=run_config,
            )

            # Store usage data for AdvancedSQLiteSession tracking
            if session:
                try:
                    await session.store_run_usage(result)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to store run usage: {e}")

            return self._parse_result(result, request.thread_id)

    async def _get_agent(
        self,
        request: AgentExecutionRequest,
        db,
    ) -> tuple[Any, Optional[List[Any]], Any]:
        """
        Get agent(s) based on execution mode.

        Returns:
            (agent, all_agents, session) tuple with active/supervisor agent, all specialized agents, and session
        """
        # Extract vector_store_ids from attachments (for PDF FileSearch)
        vector_store_ids = []
        if request.attachments:
            for att in request.attachments:
                if "vector_store_id" in att:
                    vector_store_ids.append(att["vector_store_id"])

        # Parse company_id (may be string from request)
        from uuid import UUID
        company_id_uuid = None
        if request.company_id:
            try:
                company_id_uuid = UUID(request.company_id) if isinstance(request.company_id, str) else request.company_id
            except (ValueError, AttributeError):
                logger.warning(f"⚠️  Invalid company_id format: {request.company_id}")

        # Create session
        session = self._create_session(request.thread_id)

        # Get orchestrator (contains all agents and session manager)
        orchestrator = await handoffs_manager.get_orchestrator(
            thread_id=request.thread_id,
            db=db,
            user_id=request.user_id,
            company_id=company_id_uuid,
            vector_store_ids=vector_store_ids if vector_store_ids else None,
            channel=request.channel,
        )

        # Check if there's an active agent (agent persistence)
        active_agent = await orchestrator.get_active_agent()
        if active_agent and active_agent != orchestrator.get_supervisor_agent():
            agent_name = getattr(active_agent, 'name', 'unknown')
            logger.info(
                f"🔄 [STICKY AGENT] Using active agent: {agent_name} | "
                f"Thread: {request.thread_id[:12]}... | "
                f"Channel: {request.channel}"
            )
            agent = active_agent
        else:
            # No active agent - start with supervisor
            logger.info(
                f"👔 [STICKY AGENT] Using supervisor (no active agent) | "
                f"Thread: {request.thread_id[:12]}... | "
                f"Channel: {request.channel}"
            )
            agent = orchestrator.get_supervisor_agent()

        # Get all agents for handoffs
        all_agents = list(orchestrator.agents.values())

        return (agent, all_agents, session)

    async def _build_context(
        self,
        request: AgentExecutionRequest,
        db,
        store = None,
    ) -> FizkoContext:
        """
        Build FizkoContext for agent execution.

        Note: company_info should already be loaded by AgentService

        Args:
            request: Agent execution request
            db: Database session
            store: ChatKit store (optional, needed for widget streaming in tools)
        """
        from chatkit.types import ThreadMetadata
        from datetime import datetime, timezone

        # Create minimal thread metadata
        thread_metadata = ThreadMetadata(
            id=request.thread_id,
            created_at=datetime.now(timezone.utc),
            metadata={"channel": request.channel},
        )

        context = FizkoContext(
            thread=thread_metadata,
            store=store,  # Pass store for widget streaming in tools
            request_context={
                "user_id": request.user_id,
                "company_id": request.company_id,
                "thread_id": request.thread_id,  # Add thread_id for handoff tracking
                **(request.metadata or {}),
            },
            current_agent_type="fizko_agent",
        )

        # Set company_info if provided
        if request.company_info:
            context.company_info = request.company_info

        return context

    def _prepare_input(
        self,
        request: AgentExecutionRequest,
    ) -> List[Dict[str, Any]]:
        """
        Prepare agent input in OpenAI Agents format.

        Handles both simple text and complex content_parts.
        """
        if isinstance(request.message, str):
            # Simple text message
            content_parts = [{"type": "input_text", "text": request.message}]
        else:
            # Already in content_parts format
            content_parts = request.message

        # Add UI context if provided (prepend to first text part)
        if request.ui_context:
            for i, part in enumerate(content_parts):
                if part.get("type") == "input_text":
                    content_parts[i]["text"] = request.ui_context + part["text"]
                    break

        # Wrap in message format
        agent_input = [{"role": "user", "content": content_parts}]

        return agent_input

    def _create_session(self, thread_id: str):
        """
        Create Advanced SQLite session for conversation history.

        Uses AdvancedSQLiteSession for better conversation management:
        - Natural message-by-message presentation
        - Branch support (if needed later)
        - Better usage tracking
        """
        from agents.extensions.memory import AdvancedSQLiteSession

        session = AdvancedSQLiteSession(
            session_id=thread_id,
            db_path=self.session_file,
            create_tables=True
        )
        return session

    def _parse_result(
        self,
        result: Any,
        thread_id: str,
    ) -> AgentExecutionResult:
        """
        Parse non-streaming result into AgentExecutionResult.
        """
        # Extract text from result.new_items
        text_parts = []

        for item in result.new_items:
            item_type = type(item).__name__

            if item_type == "MessageOutputItem":
                if hasattr(item, "raw_item") and hasattr(item.raw_item, "content"):
                    for content_part in item.raw_item.content:
                        if hasattr(content_part, "text") and content_part.text:
                            text_parts.append(content_part.text)

        response_text = "".join(text_parts).strip()

        if not response_text:
            response_text = "Lo siento, no pude procesar tu mensaje."

        return AgentExecutionResult(
            response_text=response_text,
            new_items=result.new_items,
            thread_id=thread_id,
            metadata={},
        )

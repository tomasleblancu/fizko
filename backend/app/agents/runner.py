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

from agents import Runner, SQLiteSession
from openai import AsyncOpenAI

from .core import FizkoContext
from .orchestration import handoffs_manager, create_unified_agent

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
    mode: str = "multi_agent"  # "multi_agent" or "unified"
    max_turns: int = 10
    channel: str = "unknown"  # "web", "whatsapp", etc.


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
    of the channel (ChatKit web, WhatsApp, etc.). It handles:
    - Agent selection (supervisor vs unified)
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
        mode: str = "multi_agent",
        sessions_dir: Optional[str] = None
    ):
        """
        Initialize agent runner.

        Args:
            mode: "multi_agent" (default) or "unified"
            sessions_dir: Directory for SQLite session storage
        """
        self.mode = mode

        # Setup sessions directory
        if sessions_dir is None:
            sessions_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "sessions"
            )
        self.sessions_dir = sessions_dir
        os.makedirs(self.sessions_dir, exist_ok=True)

        self.session_file = os.path.join(self.sessions_dir, "agent_sessions.db")

        logger.info(f"🤖 AgentRunner initialized (mode: {mode})")

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
        logger.info(f"🚀 AgentRunner.execute() | mode={self.mode} | stream={stream}")
        logger.info(f"   thread_id={request.thread_id} | channel={request.channel}")

        # 1. Get agent based on mode
        agent, all_agents = await self._get_agent(request, db)

        # 2. Build agent context
        context = await self._build_context(request, db)

        # 3. Prepare agent input
        agent_input = self._prepare_input(request)

        # 4. Create session for conversation history
        session = self._create_session(request.thread_id)

        # 5. Execute agent
        if stream:
            logger.info(f"🔄 Starting streaming execution...")
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
            logger.info(f"⚡ Starting non-streaming execution...")
            result = await Runner.run(
                agent,
                agent_input,
                context=context,
                session=session,
                max_turns=request.max_turns,
                run_config=run_config,
            )
            return self._parse_result(result, request.thread_id)

    async def _get_agent(
        self,
        request: AgentExecutionRequest,
        db,
    ) -> tuple[Any, Optional[List[Any]]]:
        """
        Get agent(s) based on execution mode.

        Returns:
            (agent, all_agents) tuple
            - For multi_agent: (supervisor, [all_agents])
            - For unified: (unified_agent, None)
        """
        # Extract vector_store_ids from attachments (for PDF FileSearch)
        vector_store_ids = []
        if request.attachments:
            for att in request.attachments:
                if "vector_store_id" in att:
                    vector_store_ids.append(att["vector_store_id"])

        if self.mode == "multi_agent":
            logger.info("🔀 Creating multi-agent system...")

            # Get supervisor agent
            # Parse company_id (may be string from request)
            from uuid import UUID
            company_id_uuid = None
            if request.company_id:
                try:
                    company_id_uuid = UUID(request.company_id) if isinstance(request.company_id, str) else request.company_id
                except (ValueError, AttributeError):
                    logger.warning(f"⚠️  Invalid company_id format: {request.company_id}")

            agent = await handoffs_manager.get_supervisor_agent(
                thread_id=request.thread_id,
                db=db,
                user_id=request.user_id,
                company_id=company_id_uuid,  # ⭐ Pass company_id for subscription validation
                vector_store_ids=vector_store_ids if vector_store_ids else None,
            )

            # Get all agents for handoffs
            all_agents = await handoffs_manager.get_all_agents(
                thread_id=request.thread_id,
                db=db,
                user_id=request.user_id,
                company_id=company_id_uuid,  # ⭐ Pass company_id
                vector_store_ids=vector_store_ids if vector_store_ids else None,
            )

            logger.info(f"✅ Multi-agent system ready: {len(all_agents)} agents")
            return (agent, all_agents)

        else:  # unified mode
            logger.info("📦 Creating unified agent...")

            # Create OpenAI client
            openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            agent = create_unified_agent(
                db=db,
                openai_client=openai_client,
                vector_store_ids=vector_store_ids if vector_store_ids else None,
                channel=request.channel,
            )

            logger.info("✅ Unified agent ready")
            return (agent, None)

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

        logger.info(f"📝 Agent input: {len(content_parts)} content parts")

        return agent_input

    def _create_session(self, thread_id: str) -> SQLiteSession:
        """
        Create SQLite session for conversation history.
        """
        session = SQLiteSession(thread_id, self.session_file)
        logger.info(f"💾 Session created: {thread_id}")
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

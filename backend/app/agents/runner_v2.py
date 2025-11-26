"""
Agent Runner V2 - Simplified Classification-Based Routing.

This is a NEW implementation that eliminates handoffs and sticky agents.
Instead, it uses a simple two-step process:

1. Classifier Agent → Returns {"agent_name": "..."}
2. Specialized Agent → Processes with full thread history

NO handoffs, NO "For context..." messages, NO sticky/non-sticky complexity.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID

from agents import Runner
from openai import AsyncOpenAI

from .core import FizkoContext
from .classifier_agent import create_classifier_agent

logger = logging.getLogger(__name__)


# Map agent names to agent keys in orchestrator
AGENT_NAME_TO_KEY = {
    "general_knowledge": "general_knowledge_agent",
    "tax_documents": "tax_documents_agent",
    "monthly_taxes": "monthly_taxes_agent",
    "payroll": "payroll_agent",
    "settings": "settings_agent",
    "expense": "expense_agent",
    "feedback": "feedback_agent",
}


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


class AgentRunnerV2:
    """
    Simplified agent runner using classification-based routing.

    This runner implements a two-step process:
    1. Classifier Agent analyzes the query and returns agent_name
    2. Specialized Agent processes the query with full thread history

    Benefits:
    - No handoffs (eliminates "For context..." messages)
    - All agents see full thread history (no context summarization)
    - No sticky/non-sticky complexity
    - Simpler, more predictable behavior
    """

    def __init__(
        self,
        sessions_dir: Optional[str] = None,
        openai_client: Optional[AsyncOpenAI] = None,
    ):
        """
        Initialize agent runner v2.

        Args:
            sessions_dir: Directory for SQLite session storage
            openai_client: OpenAI client (optional)
        """
        # Setup sessions directory
        if sessions_dir is None:
            sessions_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "sessions"
            )
        self.sessions_dir = sessions_dir
        os.makedirs(self.sessions_dir, exist_ok=True)

        self.session_file = os.path.join(self.sessions_dir, "agent_sessions.db")

        # OpenAI client
        self._openai_client = openai_client

        logger.info("🤖 AgentRunnerV2 initialized (classification-based routing)")

    def _get_openai_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._openai_client = AsyncOpenAI(api_key=api_key)
        return self._openai_client

    async def execute(
        self,
        request: AgentExecutionRequest,
        orchestrator: Any,  # MultiAgentOrchestrator
        stream: bool = False,
        run_config = None,
    ) -> AgentExecutionResult | AsyncIterator[Any]:
        """
        Execute agent with classification-based routing.

        Flow:
        1. Create session
        2. Run classifier agent → get agent_name
        3. Map agent_name to specialized agent
        4. Run specialized agent with full history

        Args:
            request: Execution request with all necessary context
            orchestrator: MultiAgentOrchestrator instance (for getting specialized agents)
            stream: Whether to stream results
            run_config: Optional RunConfig for session_input_callback

        Returns:
            AgentExecutionResult (if stream=False) or AsyncIterator of events
        """

        # 1. Create session (manages conversation history)
        session = self._create_session(request.thread_id)

        # 2. Build context
        context = await self._build_context(request, None)

        # 3. Prepare message (same format for both classifier and specialized agent)
        if isinstance(request.message, str):
            agent_input = request.message
        else:
            # Convert content_parts to simple text for session memory
            agent_input = self._extract_text_from_content(request.message)

        # 4. STEP 1: Run classifier to get agent_name
        agent_name = await self._classify_query(
            agent_input=agent_input,
            context=context,
            session=session,
        )

        logger.info(
            f"🎯 [CLASSIFICATION] thread={request.thread_id[:12]}... → {agent_name}"
        )

        # 5. STEP 2: Map agent_name to specialized agent
        agent_key = AGENT_NAME_TO_KEY.get(agent_name)
        if not agent_key:
            logger.warning(f"⚠️ Unknown agent_name: {agent_name}, defaulting to general_knowledge")
            agent_key = "general_knowledge_agent"

        specialized_agent = orchestrator.get_agent(agent_key)
        if not specialized_agent:
            logger.error(f"❌ Agent not found: {agent_key}")
            raise ValueError(f"Specialized agent not available: {agent_key}")

        logger.info(
            f"🔀 [ROUTING] {agent_name} → {agent_key} | "
            f"thread={request.thread_id[:12]}... | tools={len(specialized_agent.tools)}"
        )

        # 6. STEP 3: Execute specialized agent with full history
        if stream:
            result = Runner.run_streamed(
                specialized_agent,
                agent_input,  # Same message (session has full history)
                context=context,
                session=session,  # Session contains full conversation history
                max_turns=request.max_turns,
                run_config=run_config,
            )
            return result
        else:
            result = await Runner.run(
                specialized_agent,
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

    async def _classify_query(
        self,
        agent_input: str,
        context: FizkoContext,
        session: Any,
    ) -> str:
        """
        Run classifier agent to get agent_name.

        Args:
            agent_input: User message
            context: Fizko context
            session: SQLite session (contains full history)

        Returns:
            agent_name (e.g., "tax_documents", "general_knowledge")
        """
        # Create classifier agent
        classifier = create_classifier_agent()

        # Run classifier (max_turns=1, only one classification)
        result = await Runner.run(
            classifier,
            agent_input,
            context=context,
            session=session,  # Classifier sees full history
            max_turns=1,  # Only one turn for classification
        )

        # Parse structured output from classifier
        agent_name = self._extract_agent_name(result)

        return agent_name

    def _extract_agent_name(self, result: Any) -> str:
        """
        Extract agent_name from classifier result.

        The classifier uses structured output (ClassificationAgentSchema),
        so the result should contain the parsed Pydantic object.

        Args:
            result: Result from Runner.run()

        Returns:
            agent_name string
        """
        # Try to extract from structured output
        if hasattr(result, "output") and result.output is not None:
            # Structured output is a Pydantic model
            if hasattr(result.output, "agent_name"):
                agent_name = result.output.agent_name
                logger.info(f"🎯 [CLASSIFIER] Extracted from structured output: {agent_name}")
                return agent_name

        # Fallback: try to extract from new_items (text-based parsing)
        for item in result.new_items:
            if hasattr(item, "raw_item"):
                raw = item.raw_item
                # Check for content in response
                if hasattr(raw, "content"):
                    for content_part in raw.content:
                        if hasattr(content_part, "text"):
                            text = content_part.text.strip()

                            # Try to parse JSON
                            try:
                                # Handle potential markdown code blocks
                                if "```json" in text:
                                    json_start = text.find("```json") + 7
                                    json_end = text.find("```", json_start)
                                    text = text[json_start:json_end].strip()
                                elif "```" in text:
                                    json_start = text.find("```") + 3
                                    json_end = text.find("```", json_start)
                                    text = text[json_start:json_end].strip()

                                data = json.loads(text)
                                if "agent_name" in data:
                                    agent_name = data["agent_name"]
                                    logger.info(f"🎯 [CLASSIFIER] Extracted from JSON: {agent_name}")
                                    return agent_name
                            except json.JSONDecodeError:
                                # Fallback: check if text is a direct agent name
                                text_lower = text.lower().strip()
                                if text_lower in AGENT_NAME_TO_KEY:
                                    logger.info(f"🎯 [CLASSIFIER] Using direct agent name: {text_lower}")
                                    return text_lower

        # Default fallback
        logger.warning("⚠️ Could not extract agent_name from classifier, using general_knowledge")
        return "general_knowledge"

    def _extract_text_from_content(self, content_parts: List[Dict[str, Any]]) -> str:
        """Extract plain text from content_parts format."""
        texts = []
        for part in content_parts:
            if part.get("type") == "input_text" and "text" in part:
                texts.append(part["text"])
        return " ".join(texts)

    async def _build_context(
        self,
        request: AgentExecutionRequest,
        db,
        store = None,
    ) -> FizkoContext:
        """
        Build FizkoContext for agent execution.

        Args:
            request: Agent execution request
            db: Database session
            store: ChatKit store (optional)
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
            store=store,
            request_context={
                "user_id": request.user_id,
                "company_id": request.company_id,
                "thread_id": request.thread_id,
                **(request.metadata or {}),
            },
            current_agent_type="fizko_agent",
        )

        # Set company_info if provided
        if request.company_info:
            context.company_info = request.company_info

        return context

    def _create_session(self, thread_id: str):
        """
        Create Advanced SQLite session for conversation history.

        Uses AdvancedSQLiteSession for better conversation management.
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

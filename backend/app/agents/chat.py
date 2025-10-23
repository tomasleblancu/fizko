"""ChatKit server integration for Fizko backend - Unified Agent System."""

from __future__ import annotations

import logging
import os
from typing import Any, AsyncIterator
from uuid import uuid4

from agents import Runner, SQLiteSession
from chatkit.agents import stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.types import ThreadItem, ThreadMetadata, ThreadStreamEvent, UserMessageItem

from ..config.database import AsyncSessionLocal
from ..stores import MemoryStore
from .context import FizkoContext
from .unified_agent import create_unified_agent

try:
    from ..stores import SupabaseStore

    SUPABASE_AVAILABLE = True
except (ImportError, ValueError):
    SUPABASE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _user_message_text(item: UserMessageItem) -> str:
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


class FizkoChatKitServer(ChatKitServer):
    """ChatKit server with unified Fizko agent."""

    def __init__(self):
        if SUPABASE_AVAILABLE:
            logger.info("Using SupabaseStore for thread persistence")
            self.store = SupabaseStore()
        else:
            logger.info("Supabase not available, using MemoryStore")
            self.store = MemoryStore()

        # Initialize attachment store
        from .memory_attachment_store import MemoryAttachmentStore

        self.attachment_store = MemoryAttachmentStore()

        # Initialize ChatKitServer with both stores
        super().__init__(self.store, attachment_store=self.attachment_store)

        logger.info("Unified agent system ENABLED")

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        import time

        request_start = time.time()
        user_id = context.get("user_id", "unknown")
        logger.info(f"Request - Thread: {thread.id} | User: {user_id}")

        # Get database session for this request
        async with AsyncSessionLocal() as db:
            # Create OpenAI client (required by create_unified_agent)
            from openai import AsyncOpenAI
            import os

            openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Create the unified agent for this request
            agent = create_unified_agent(db=db, openai_client=openai_client)

        agent_context = FizkoContext(
            thread=thread,
            store=self.store,
            request_context=context,
            current_agent_type="fizko_agent",
        )

        target_item: ThreadItem | None = item
        if target_item is None:
            target_item = await self._latest_thread_item(thread, context)

        if target_item is None:
            return

        # Extract text from user message
        user_message = _user_message_text(target_item) if isinstance(target_item, UserMessageItem) else ""
        logger.info(f"User: {user_message[:100]}")

        # Create session for conversation history
        sessions_dir = os.path.join(os.path.dirname(__file__), "..", "..", "sessions")
        os.makedirs(sessions_dir, exist_ok=True)

        session_file = os.path.join(sessions_dir, "agent_sessions.db")
        session = SQLiteSession(thread.id, session_file)

        # Run the agent with streaming
        result = Runner.run_streamed(
            agent,
            user_message,
            context=agent_context,
            session=session,
            max_turns=10,  # Allow multiple turns if needed
        )

        # Stream response
        response_text_parts = []

        async for event in stream_agent_response(agent_context, result):
            # Capture text content
            if hasattr(event, "item") and hasattr(event.item, "content"):
                for content in event.item.content:
                    if hasattr(content, "text") and content.text:
                        response_text_parts.append(content.text)

            yield event

        # Log final response
        if response_text_parts:
            full_response = "".join(response_text_parts)
            preview = full_response[:150] + ("..." if len(full_response) > 150 else "")
            logger.info(f"Agent '{agent.name}' completed: {preview}")

        return

    async def _latest_thread_item(
        self, thread: ThreadMetadata, context: dict[str, Any]
    ) -> ThreadItem | None:
        try:
            async for event in self.store.load_thread(thread.id, context=context):
                if hasattr(event, "item") and isinstance(event.item, UserMessageItem):
                    return event.item
        except Exception as e:
            logger.error(f"Error loading latest thread item: {e}")

        return None

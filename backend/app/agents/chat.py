"""ChatKit server integration for Fizko backend."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, AsyncIterator
from uuid import uuid4

from agents import Runner, SQLiteSession
from chatkit.agents import stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.types import ThreadItem, ThreadMetadata, ThreadStreamEvent, UserMessageItem

from ..config.database import AsyncSessionLocal
from ..stores import MemoryStore
from .context import FizkoContext

try:
    from ..stores import SupabaseStore

    SUPABASE_AVAILABLE = True
except (ImportError, ValueError):
    SUPABASE_AVAILABLE = False

try:
    from .lazy_handoffs import lazy_handoffs_manager

    MULTI_AGENT_AVAILABLE = True
except (ImportError, ValueError) as e:
    MULTI_AGENT_AVAILABLE = False
    logging.warning(f"Multi-agent system not available: {e}")

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


class FizkoServer(ChatKitServer[dict[str, Any]]):
    """ChatKit server for Fizko tax/accounting assistant."""

    def __init__(self) -> None:
        # Use SupabaseStore if available, otherwise fall back to MemoryStore
        if SUPABASE_AVAILABLE:
            try:
                self.store = SupabaseStore()
                logger.info("Using SupabaseStore for thread persistence")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize SupabaseStore: {e}. Falling back to MemoryStore"
                )
                self.store = MemoryStore()
        else:
            logger.info("Using MemoryStore (in-memory only)")
            self.store = MemoryStore()

        # Initialize AttachmentStore
        from .memory_attachment_store import MemoryAttachmentStore

        self.attachment_store = MemoryAttachmentStore()

        # Initialize ChatKitServer with both stores
        super().__init__(self.store, attachment_store=self.attachment_store)

        # Multi-agent handoffs system
        if not MULTI_AGENT_AVAILABLE:
            raise RuntimeError(
                "Multi-agent system is required but LazyHandoffsManager is not available."
            )

        logger.info("Multi-agent handoffs system ENABLED")

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        import time
        import os

        request_start = time.time()
        user_id = context.get("user_id", "unknown")
        logger.info(f"Request - Thread: {thread.id} | User: {user_id}")

        # Get database session for this request
        async with AsyncSessionLocal() as db:
            # Get Triage Agent from lazy manager
            selected_agent = await lazy_handoffs_manager.get_triage_agent(
                thread_id=thread.id,
                db=db,
                user_id=user_id,
            )

            logger.info("Using Triage Agent as entry point")

        agent_context = FizkoContext(
            thread=thread,
            store=self.store,
            request_context=context,
            current_agent_type="triage_agent",
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
            selected_agent,
            user_message,
            context=agent_context,
            session=session,
        )

        # Stream response
        response_text_parts = []
        current_agent = selected_agent.name

        async for event in stream_agent_response(agent_context, result):
            # Capture text content
            if hasattr(event, "item") and hasattr(event.item, "content"):
                for content in event.item.content:
                    if hasattr(content, "text") and content.text:
                        response_text_parts.append(content.text)

            # Check if agent changed (handoff)
            if hasattr(event, "item") and hasattr(event.item, "agent_name"):
                if event.item.agent_name and event.item.agent_name != current_agent:
                    logger.info(f"Handoff: {current_agent} → {event.item.agent_name}")
                    current_agent = event.item.agent_name

            yield event

        # Log final response
        if response_text_parts:
            full_response = "".join(response_text_parts)
            preview = full_response[:150] + ("..." if len(full_response) > 150 else "")
            logger.info(f"Agent '{current_agent}' completed: {preview}")

        return

    async def _latest_thread_item(
        self, thread: ThreadMetadata, context: dict[str, Any]
    ) -> ThreadItem | None:
        try:
            items = await self.store.load_thread_items(thread.id, None, 1, "desc", context)
        except Exception:
            return None

        return items.data[0] if getattr(items, "data", None) else None


def create_chatkit_server() -> FizkoServer | None:
    """Return a configured Fizko server instance."""
    return FizkoServer()

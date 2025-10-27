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
            self.store = SupabaseStore()
        else:
            logger.warning("Supabase not available, using MemoryStore")
            self.store = MemoryStore()

        # Initialize attachment store
        from .memory_attachment_store import MemoryAttachmentStore

        self.attachment_store = MemoryAttachmentStore()

        # Initialize ChatKitServer with both stores
        super().__init__(self.store, attachment_store=self.attachment_store)

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        import time

        # Get request start time from context (set in main.py)
        request_start = context.get("request_start_time", time.time())
        respond_start = time.time()

        # Create OpenAI client (required by create_unified_agent)
        from openai import AsyncOpenAI
        import os

        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Get database session for this request (mantener abierto durante todo el request)
        async with AsyncSessionLocal() as db:
            # Create the unified agent for this request
            agent = create_unified_agent(db=db, openai_client=openai_client)

            agent_context = FizkoContext(
                thread=thread,
                store=self.store,
                request_context=context,
                current_agent_type="fizko_agent",
            )

            # Load company info automatically at thread start (usando la misma sesión db)
            company_id = context.get("company_id")
            if company_id:
                from .context_loader import load_company_info
                company_info = await load_company_info(db, company_id)

                agent_context.company_info = company_info
                if company_info and "company" in company_info:
                    logger.info(f"📋 Company: {company_info['company'].get('business_name', 'Unknown')}")
                elif company_info and "error" in company_info:
                    logger.warning(f"⚠️ Failed to load company info: {company_info['error']}")

        target_item: ThreadItem | None = item
        if target_item is None:
            target_item = await self._latest_thread_item(thread, context)

        if target_item is None:
            return

        # Extract text from user message
        user_message = _user_message_text(target_item) if isinstance(target_item, UserMessageItem) else ""
        logger.info(f"💬 User: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")

        # Stream widget immediately if available (before agent processing)
        ui_tool_result = context.get("ui_tool_result")
        if ui_tool_result and ui_tool_result.widget:
            try:
                await agent_context.stream_widget(
                    ui_tool_result.widget,
                    copy_text=ui_tool_result.widget_copy_text
                )
                logger.info(f"📊 Widget streamed")
            except Exception as e:
                logger.error(f"❌ Error streaming widget: {e}", exc_info=True)

        # Prepend company info to user message if available
        if agent_context.company_info:
            from .context_loader import format_company_context
            company_context = format_company_context(agent_context.company_info)
            user_message = f"{company_context}{user_message}"

        # Prepend UI context if available (from UI Tools system)
        ui_context_text = context.get("ui_context_text", "")
        if ui_context_text:
            user_message = f"{ui_context_text}\n\n{user_message}"

        # Create session for conversation history
        sessions_dir = os.path.join(os.path.dirname(__file__), "..", "..", "sessions")
        os.makedirs(sessions_dir, exist_ok=True)

        session_file = os.path.join(sessions_dir, "agent_sessions.db")
        session = SQLiteSession(thread.id, session_file)

        result = Runner.run_streamed(
            agent,
            user_message,
            context=agent_context,
            session=session,
            max_turns=10,  # Allow multiple turns if needed
        )

        # Stream response
        response_text_parts = []
        first_token_time = None

        async for event in stream_agent_response(agent_context, result):
            # Log first token time (Time To First Token - TTFT)
            if first_token_time is None and hasattr(event, "item") and hasattr(event.item, "content"):
                for content in event.item.content:
                    if hasattr(content, "text") and content.text:
                        first_token_time = time.time()
                        ttft = first_token_time - request_start
                        logger.info(f"⏱️  🎯 TTFT: {ttft:.3f}s")
                        break

            # Capture text content
            if hasattr(event, "item") and hasattr(event.item, "content"):
                for content in event.item.content:
                    if hasattr(content, "text") and content.text:
                        response_text_parts.append(content.text)

            yield event

        # Log final response
        if response_text_parts:
            full_response = "".join(response_text_parts)
            preview = full_response[:100] + ("..." if len(full_response) > 100 else "")
            logger.info(f"✅ Agent: {preview}")
        else:
            logger.warning("⚠️ No response text generated")

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


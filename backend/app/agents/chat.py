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
from app.stores import MemoryStore, HybridStore
from .core import FizkoContext
from .orchestration import create_unified_agent, handoffs_manager

try:
    from app.stores import SupabaseStore

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


async def _convert_attachments_to_content(item: UserMessageItem, attachment_store) -> list[dict[str, Any]]:
    """
    Convert UserMessageItem content (text + attachments) to OpenAI Agents framework format.

    Returns a list of content items that can include:
    - {"type": "input_text", "text": "..."}
    - {"type": "input_image", "image_url": "data:image/png;base64,..."}
    """
    from .core import get_attachment_content
    from ..services.storage.attachment_storage import get_attachment_storage
    import mimetypes

    content_parts = []

    # First, process text content
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            content_parts.append({
                "type": "input_text",
                "text": text
            })

    # Then, check if item has attachments attribute (ChatKit sends this separately)
    attachment_ids = []
    attachment_objects = []

    # Method 1: Check for attachments attribute directly on item
    if hasattr(item, 'attachments') and item.attachments:
        logger.info(f"📦 Found attachments attribute: {item.attachments}")
        attachments_list = item.attachments if isinstance(item.attachments, list) else [item.attachments]

        for att in attachments_list:
            # If it's already an Attachment object, extract the ID
            if hasattr(att, 'id'):
                attachment_ids.append(att.id)
                attachment_objects.append(att)
            # If it's just a string ID
            elif isinstance(att, str):
                attachment_ids.append(att)

    # Method 2: Check for attachment references in content parts
    for part in item.content:
        attachment_ref = getattr(part, "attachment", None)
        if attachment_ref:
            attachment_id = getattr(attachment_ref, "id", None) or getattr(attachment_ref, "attachment_id", None)
            if attachment_id and attachment_id not in attachment_ids:
                attachment_ids.append(attachment_id)
                if hasattr(attachment_ref, 'mime_type'):
                    attachment_objects.append(attachment_ref)

    # Process all found attachments
    if attachment_ids:
        logger.info(f"🔗 Processing {len(attachment_ids)} attachment(s): {attachment_ids}")
        storage = get_attachment_storage()

        for i, attachment_id in enumerate(attachment_ids):
            logger.info(f"🔗 Processing attachment {i+1}/{len(attachment_ids)}: {attachment_id}")

            # Try to get full attachment object first (has all metadata)
            attachment_obj = attachment_objects[i] if i < len(attachment_objects) else None

            if attachment_obj:
                # We have the full Attachment object from ChatKit
                mime_type = getattr(attachment_obj, 'mime_type', '')
                filename = getattr(attachment_obj, 'name', 'unknown')

                logger.info(f"📎 Using attachment object: {mime_type}, {filename}")
            else:
                # Fallback: Get metadata from store
                metadata = attachment_store.get_attachment_metadata(attachment_id)
                if metadata:
                    mime_type = metadata.get("mime_type", "")
                    filename = metadata.get("name", "")
                    logger.info(f"📎 Using attachment metadata: {mime_type}, {filename}")
                else:
                    logger.warning(f"⚠️ No metadata found for {attachment_id}, skipping")
                    continue

            # For images, ALWAYS use base64 (agents framework has issues with external URLs)
            if mime_type.startswith("image/"):
                base64_content = get_attachment_content(attachment_id)

                if base64_content:
                    # Create data URL - agents framework expects this format
                    data_url = f"data:{mime_type};base64,{base64_content}"
                    content_parts.append({
                        "type": "input_image",
                        "image_url": data_url
                    })
                    logger.info(f"📸 Added image to content: {filename} (base64, {len(base64_content)} chars)")
                else:
                    logger.warning(f"⚠️ Image content not found in memory for {attachment_id}")
                    # If base64 not available, skip the image
                    content_parts.append({
                        "type": "input_text",
                        "text": f"[Imagen no disponible: {filename}]"
                    })
            else:
                # For non-image files (PDFs, etc.)
                # Check if this PDF has been uploaded to OpenAI (has vector_store_id)
                openai_metadata = await attachment_store.get_openai_metadata(attachment_id)

                if openai_metadata and 'vector_store_id' in openai_metadata:
                    # PDF is available via FileSearchTool - inform the agent
                    content_parts.append({
                        "type": "input_text",
                        "text": f"El usuario ha adjuntado el documento PDF '{filename}'. Usa la herramienta file_search para leer y analizar su contenido."
                    })
                    logger.info(f"📄 PDF with vector_store available: {filename}")
                else:
                    # PDF not in OpenAI - just add reference
                    content_parts.append({
                        "type": "input_text",
                        "text": f"[Archivo adjunto: {filename}]"
                    })
                    logger.info(f"📄 Added file reference: {filename}")

    return content_parts


class FizkoChatKitServer(ChatKitServer):
    """
    ChatKit server for Fizko platform.

    Supports two modes:
    - unified: Single agent with all tools (legacy)
    - multi_agent: Supervisor with handoffs to specialized agents (new)
    """

    def __init__(self, mode: str = "multi_agent"):
        """
        Initialize ChatKit server.

        Args:
            mode: "unified" (single agent) or "multi_agent" (handoffs system)
        """
        self.mode = mode
        logger.info(f"🤖 FizkoChatKitServer initialized in '{mode}' mode")

        # Use HybridStore: Fast in-memory reads + background Supabase sync
        # This eliminates network latency (3s per query) while keeping persistence
        if SUPABASE_AVAILABLE:
            supabase_store = SupabaseStore()
            self.store = HybridStore(supabase_store=supabase_store)
            logger.info("Using HybridStore (memory cache + background Supabase sync)")
        else:
            logger.warning("Supabase not available, using MemoryStore")
            self.store = MemoryStore()

        # Initialize attachment store
        from .core import MemoryAttachmentStore

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
        logger.info(f"⏱️  [+{(respond_start - request_start):.3f}s] respond() started")

        # Create OpenAI client (required by create_unified_agent)
        from openai import AsyncOpenAI
        import os

        client_start = time.time()
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] OpenAI client created ({(time.time() - client_start):.3f}s)")

        # Get database session for this request (mantener abierto durante todo el request)
        db_start = time.time()
        async with AsyncSessionLocal() as db:
            logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] DB session opened ({(time.time() - db_start):.3f}s)")

            # Extract vector_store_ids from PDF attachments (if any)
            vector_store_ids = []
            if isinstance(item, UserMessageItem) and hasattr(item, 'attachments') and item.attachments:
                for attachment in item.attachments:
                    attachment_id = attachment.id if hasattr(attachment, 'id') else attachment
                    openai_metadata = await self.attachment_store.get_openai_metadata(attachment_id)
                    if openai_metadata and 'vector_store_id' in openai_metadata:
                        vector_store_ids.append(openai_metadata['vector_store_id'])
                        logger.info(f"📄 Found PDF attachment with vector_store_id: {openai_metadata['vector_store_id']}")

            # Create agent according to mode (unified or multi_agent)
            agent_start = time.time()

            if self.mode == "multi_agent":
                # Multi-agent system with handoffs
                logger.info("=" * 60)
                logger.info("🔀 [MULTI-AGENT MODE]")

                # Get supervisor agent from handoffs_manager
                supervisor_fetch_start = time.time()
                agent = await handoffs_manager.get_supervisor_agent(
                    thread_id=thread.id,
                    db=db,
                    user_id=context.get("user_id"),
                )
                supervisor_fetch_time = time.time() - supervisor_fetch_start
                logger.info(f"⏱️  Supervisor agent fetch: {supervisor_fetch_time:.3f}s")

                # Get all agents for handoffs
                agents_fetch_start = time.time()
                all_agents = await handoffs_manager.get_all_agents(
                    thread_id=thread.id,
                    db=db,
                    user_id=context.get("user_id"),
                )
                agents_fetch_time = time.time() - agents_fetch_start
                logger.info(f"⏱️  All agents fetch: {agents_fetch_time:.3f}s")

                logger.info(f"✅ Multi-agent system ready: {len(all_agents)} agents available")
                logger.info("=" * 60)

                if vector_store_ids:
                    logger.warning(f"⚠️  PDFs detected but multi-agent mode doesn't support FileSearch yet")

            else:
                # Unified agent (legacy) with all tools
                logger.info("📦 Using unified agent (legacy mode)")

                agent = create_unified_agent(
                    db=db,
                    openai_client=openai_client,
                    vector_store_ids=vector_store_ids if vector_store_ids else None
                )

                all_agents = None  # Unified mode doesn't use multiple agents

            logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] Agent created ({(time.time() - agent_start):.3f}s)")

            context_start = time.time()
            agent_context = FizkoContext(
                thread=thread,
                store=self.store,
                request_context=context,
                current_agent_type="fizko_agent",
            )
            logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] Agent context created ({(time.time() - context_start):.3f}s)")

            # Load company info (from thread metadata if available, otherwise from DB)
            company_id = context.get("company_id")
            company_info = None

            if company_id:
                # Check if company_info is already in thread metadata (from previous messages)
                if thread.metadata and "company_info" in thread.metadata:
                    company_info = thread.metadata["company_info"]
                    logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] Company info loaded from thread cache (0.000s)")
                else:
                    # First message in thread - load from DB and cache in thread metadata
                    from .core import load_company_info
                    company_load_start = time.time()
                    logger.info(f"⏱️  [+{(company_load_start - request_start):.3f}s] Company info fetch started (first message)")
                    company_info = await load_company_info(db, company_id)
                    company_load_end = time.time()
                    logger.info(f"⏱️  [+{(company_load_end - request_start):.3f}s] Company info loaded from DB ({(company_load_end - company_load_start):.3f}s)")

                    # Store in thread metadata for future messages
                    if not thread.metadata:
                        thread.metadata = {}
                    thread.metadata["company_info"] = company_info

                agent_context.company_info = company_info
                if company_info and "company" in company_info:
                    logger.info(f"📋 Company: {company_info['company'].get('business_name', 'Unknown')}")
                elif company_info and "error" in company_info:
                    logger.warning(f"⚠️ Failed to load company info: {company_info['error']}")

        item_start = time.time()
        target_item: ThreadItem | None = item
        if target_item is None:
            target_item = await self._latest_thread_item(thread, context)
        logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] Target item retrieved ({(time.time() - item_start):.3f}s)")

        if target_item is None:
            return

        # Extract text from user message (for logging)
        extract_start = time.time()
        user_message_text = _user_message_text(target_item) if isinstance(target_item, UserMessageItem) else ""
        logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] Message extracted ({(time.time() - extract_start):.3f}s)")
        logger.info(f"💬 User: {user_message_text[:100]}{'...' if len(user_message_text) > 100 else ''}")

        # DEBUG: Log the structure of target_item to understand how attachments are passed
        if isinstance(target_item, UserMessageItem):
            logger.info(f"🔍 DEBUG - UserMessageItem structure:")
            logger.info(f"  - content: {target_item.content}")
            logger.info(f"  - has attachments attr: {hasattr(target_item, 'attachments')}")
            if hasattr(target_item, 'attachments'):
                logger.info(f"  - attachments: {target_item.attachments}")
            logger.info(f"  - content parts count: {len(target_item.content)}")
            for i, part in enumerate(target_item.content):
                logger.info(f"  - part {i}: type={type(part)}, attrs={dir(part)}")
                logger.info(f"  - part {i} dict: {part.__dict__ if hasattr(part, '__dict__') else 'no __dict__'}")

        # Stream widget immediately if available (before agent processing)
        ui_tool_result = context.get("ui_tool_result")
        if ui_tool_result and ui_tool_result.widget:
            widget_start = time.time()
            try:
                await agent_context.stream_widget(
                    ui_tool_result.widget,
                    copy_text=ui_tool_result.widget_copy_text
                )
                logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] Widget streamed ({(time.time() - widget_start):.3f}s)")
                logger.info(f"📊 Widget streamed")
            except Exception as e:
                logger.error(f"❌ Error streaming widget: {e}", exc_info=True)

        # Convert message content (text + attachments) to OpenAI format
        convert_start = time.time()
        if isinstance(target_item, UserMessageItem):
            content_parts = await _convert_attachments_to_content(target_item, self.attachment_store)
            logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] Content converted: {len(content_parts)} parts ({(time.time() - convert_start):.3f}s)")
        else:
            # Fallback to simple text
            content_parts = [{"type": "input_text", "text": user_message_text}]

        # Prepend company info and UI context to the first text part
        context_prep_start = time.time()
        context_prefix = ""
        if agent_context.company_info:
            from .core import format_company_context
            company_context = format_company_context(agent_context.company_info)
            context_prefix += company_context

        # Prepend UI context if available (from UI Tools system)
        ui_context_text = context.get("ui_context_text", "")
        if ui_context_text:
            context_prefix += f"{ui_context_text}\n\n"

        # Add context prefix to the first text part
        if context_prefix and content_parts:
            for i, part in enumerate(content_parts):
                if part.get("type") == "input_text":
                    content_parts[i]["text"] = context_prefix + part["text"]
                    break

        logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] Context prepared ({(time.time() - context_prep_start):.3f}s)")

        # Wrap in message format (like impai pattern)
        agent_input = [{"role": "user", "content": content_parts}]
        logger.info(f"🔄 Agent input: list of {len(agent_input)} messages with {len(content_parts)} content parts")

        # Create session for conversation history
        session_start = time.time()
        sessions_dir = os.path.join(os.path.dirname(__file__), "..", "..", "sessions")
        os.makedirs(sessions_dir, exist_ok=True)

        session_file = os.path.join(sessions_dir, "agent_sessions.db")
        session = SQLiteSession(thread.id, session_file)
        logger.info(f"⏱️  [+{(time.time() - request_start):.3f}s] Session created ({(time.time() - session_start):.3f}s)")

        runner_start = time.time()
        logger.info(f"⏱️  [+{(runner_start - request_start):.3f}s] Runner.run_streamed() started")

        # Define session_input_callback (like impai pattern)
        from agents import RunConfig

        def session_input_callback(history, new_input):
            """
            Merge conversation history with new input.

            On first message, inject company_context as system-level context
            that persists across handoffs.
            """
            # Inject company context on first message (empty history)
            if len(history) == 0 and company_context:
                # Add company info as a persistent system message
                history = [{
                    "role": "user",
                    "content": [{"type": "input_text", "text": company_context}]
                }]
                logger.debug(f"📋 Injected company_context into session history ({len(company_context)} chars)")

            if isinstance(new_input, list) and len(new_input) > 0:
                if isinstance(new_input[0], dict) and 'role' in new_input[0]:
                    return history + new_input
                else:
                    return history + [{"role": "user", "content": new_input}]
            elif isinstance(new_input, str):
                return history + [{"role": "user", "content": [{"type": "input_text", "text": new_input}]}]
            else:
                return history + [{"role": "user", "content": [{"type": "input_text", "text": str(new_input)}]}]

        run_config = RunConfig(session_input_callback=session_input_callback)

        # Handoffs are configured in the agent itself (via agent.handoffs)
        # No need to pass agents parameter - the SDK handles it automatically
        result = Runner.run_streamed(
            agent,
            agent_input,
            context=agent_context,
            session=session,
            max_turns=10,
            run_config=run_config,
        )

        # Stream response
        stream_loop_start = time.time()
        logger.info(f"⏱️  [+{(stream_loop_start - request_start):.3f}s] Event stream loop started")

        response_text_parts = []
        first_token_time = None
        event_count = 0

        async for event in stream_agent_response(agent_context, result):
            event_count += 1

            # Log first token time (Time To First Token - TTFT)
            if first_token_time is None and hasattr(event, "item") and hasattr(event.item, "content"):
                for content in event.item.content:
                    if hasattr(content, "text") and content.text:
                        first_token_time = time.time()
                        ttft = first_token_time - request_start
                        time_since_runner = first_token_time - runner_start
                        logger.info(f"⏱️  🎯 FIRST TOKEN (TTFT: {ttft:.3f}s, since Runner: {time_since_runner:.3f}s)")
                        break

            # Capture text content
            if hasattr(event, "item") and hasattr(event.item, "content"):
                for content in event.item.content:
                    if hasattr(content, "text") and content.text:
                        response_text_parts.append(content.text)

            yield event

        # Log stream completion
        stream_end = time.time()
        stream_duration = stream_end - stream_loop_start
        logger.info(f"⏱️  [+{(stream_end - request_start):.3f}s] Stream completed: {event_count} events in {stream_duration:.3f}s")

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


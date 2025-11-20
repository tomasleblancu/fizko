"""
ChatKit Server Adapter - Minimal version for Backend V2 with Supabase.

Simplified version that uses Supabase instead of SQLAlchemy.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, AsyncIterator

from chatkit.server import ChatKitServer
from chatkit.store import Store, NotFoundError
from chatkit.types import (
    ThreadMetadata,
    ThreadItem,
    Attachment,
    Page,
    UserMessageItem,
    ThreadStreamEvent,
)

from app.services.agents import AgentService
from app.agents.core import MemoryAttachmentStore

logger = logging.getLogger(__name__)


class SimpleMemoryStore(Store[Dict[str, Any]]):
    """Simple in-memory store for ChatKit threads and items."""

    def __init__(self):
        """Initialize empty in-memory storage."""
        self.threads: Dict[str, ThreadMetadata] = {}
        self.items: Dict[str, list[ThreadItem]] = {}
        self.attachments: Dict[str, Attachment] = {}

    async def load_thread(
        self, thread_id: str, context: Dict[str, Any]
    ) -> ThreadMetadata:
        """Load thread metadata."""
        if thread_id not in self.threads:
            # Create new thread if not exists
            from datetime import datetime, timezone
            thread = ThreadMetadata(
                id=thread_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                metadata={}
            )
            self.threads[thread_id] = thread
            self.items[thread_id] = []
            return thread
        return self.threads[thread_id]

    async def save_thread(
        self, thread: ThreadMetadata, context: Dict[str, Any]
    ) -> None:
        """Save thread metadata."""
        self.threads[thread.id] = thread
        if thread.id not in self.items:
            self.items[thread.id] = []

    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: Dict[str, Any],
    ) -> Page[ThreadItem]:
        """Load thread items with pagination."""
        if thread_id not in self.items:
            return Page(data=[], next_cursor=None)

        items = self.items[thread_id]

        # Simple pagination - find index of 'after' item
        start_idx = 0
        if after:
            for idx, item in enumerate(items):
                if item.id == after:
                    start_idx = idx + 1
                    break

        # Get page of items
        page_items = items[start_idx : start_idx + limit]

        # Determine next cursor
        next_cursor = None
        if start_idx + limit < len(items):
            next_cursor = page_items[-1].id if page_items else None

        return Page(data=page_items, next_cursor=next_cursor)

    async def save_attachment(
        self, attachment: Attachment, context: Dict[str, Any]
    ) -> None:
        """Save attachment metadata."""
        self.attachments[attachment.id] = attachment

    async def load_attachment(
        self, attachment_id: str, context: Dict[str, Any]
    ) -> Attachment:
        """Load attachment metadata."""
        if attachment_id not in self.attachments:
            raise NotFoundError(f"Attachment {attachment_id} not found")
        return self.attachments[attachment_id]

    async def delete_attachment(
        self, attachment_id: str, context: Dict[str, Any]
    ) -> None:
        """Delete attachment."""
        if attachment_id in self.attachments:
            del self.attachments[attachment_id]

    async def load_threads(
        self,
        limit: int,
        order: str,
        after: str | None,
        context: Dict[str, Any],
    ) -> Page[ThreadMetadata]:
        """Load all threads with pagination."""
        threads = list(self.threads.values())

        # Simple pagination
        start_idx = 0
        if after:
            for idx, thread in enumerate(threads):
                if thread.id == after:
                    start_idx = idx + 1
                    break

        page_threads = threads[start_idx : start_idx + limit]

        next_cursor = None
        if start_idx + limit < len(threads):
            next_cursor = page_threads[-1].id if page_threads else None

        return Page(data=page_threads, next_cursor=next_cursor)

    async def save_thread_item(
        self, thread_id: str, item: ThreadItem, context: Dict[str, Any]
    ) -> None:
        """Save a thread item."""
        if thread_id not in self.items:
            self.items[thread_id] = []
        self.items[thread_id].append(item)

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: Dict[str, Any]
    ) -> None:
        """Add a thread item (alias for save_thread_item)."""
        await self.save_thread_item(thread_id, item, context)

    async def delete_thread(
        self, thread_id: str, context: Dict[str, Any]
    ) -> None:
        """Delete a thread."""
        if thread_id in self.threads:
            del self.threads[thread_id]
        if thread_id in self.items:
            del self.items[thread_id]

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: Dict[str, Any]
    ) -> None:
        """Delete a thread item."""
        if thread_id in self.items:
            self.items[thread_id] = [
                item for item in self.items[thread_id] if item.id != item_id
            ]

    async def load_item(
        self, thread_id: str, item_id: str, context: Dict[str, Any]
    ) -> ThreadItem | None:
        """Load a specific thread item."""
        if thread_id not in self.items:
            return None
        for item in self.items[thread_id]:
            if item.id == item_id:
                return item
        return None

    async def save_item(
        self, thread_id: str, item: ThreadItem, context: Dict[str, Any]
    ) -> None:
        """Save/update a thread item."""
        if thread_id not in self.items:
            self.items[thread_id] = []

        # Update existing item or append new one
        for i, existing_item in enumerate(self.items[thread_id]):
            if existing_item.id == item.id:
                self.items[thread_id][i] = item
                return

        # Item doesn't exist, append it
        self.items[thread_id].append(item)


class ChatKitServerAdapter(ChatKitServer):
    """
    Minimal adapter between ChatKit SDK and backend-v2 agent system.

    This is a simplified version for backend-v2's Supabase-based architecture.
    Unlike the full backend version, this:
    - Uses SimpleMemoryStore (in-memory)
    - Uses MemoryAttachmentStore
    - No database integration in adapter (AgentService handles Supabase)
    - Delegates execution to AgentService
    """

    def __init__(self):
        """Initialize ChatKit server adapter with minimal configuration."""
        self.agent_service = AgentService()

        # Initialize attachment store
        self.attachment_store = MemoryAttachmentStore()

        # Use simple in-memory store
        store = SimpleMemoryStore()

        # Initialize ChatKitServer with store and attachment store
        super().__init__(store, attachment_store=self.attachment_store)

        logger.info("🤖 ChatKitServerAdapter initialized (minimal mode - Supabase)")

    def get_store(self):
        """Get the thread store."""
        return self.store

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: Dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Respond to user message.

        This delegates to AgentService.execute_from_chatkit() and streams the response
        using ChatKit's stream_agent_response helper.
        """
        # Import ChatKit streaming helper
        from chatkit.agents import stream_agent_response

        # Extract basic message text
        if item is None:
            logger.warning("No item provided to respond method")
            return

        # Get message text from item
        message_text = ""
        for content in item.content:
            if hasattr(content, "text"):
                message_text = content.text
                break

        if not message_text:
            logger.warning("No message text found in item")
            return

        # Get context
        user_id = context.get("user_id", "anonymous")
        company_id = context.get("company_id")
        ui_context_text = context.get("ui_context_text", "")
        ui_tool_result = context.get("ui_tool_result")

        logger.info(
            f"📨 ChatKit respond: thread={thread.id[:8]}, "
            f"user={user_id}, message='{message_text[:50]}...'"
        )

        # Build message text (prepend UI context if available)
        full_message = ui_context_text + message_text if ui_context_text else message_text

        # Execute agent
        try:
            agent_stream, agent_context = await self.agent_service.execute_from_chatkit(
                user_id=user_id,
                company_id=company_id or "unknown",
                thread_id=thread.id,
                message=full_message,  # Pass string instead of list for session memory
                attachments=None,
                ui_context=ui_context_text if ui_context_text else None,
                company_info=None,  # TODO: Load company info from Supabase
                metadata=None,
                run_config=None,  # TODO: Add RunConfig with session_input_callback if needed
                store=self.store,  # Pass store for widget streaming
            )

            # Stream widget IMMEDIATELY if present (before agent response)
            if ui_tool_result and ui_tool_result.widget:
                try:
                    logger.info(f"🎨 Streaming UI widget via agent_context")
                    await agent_context.stream_widget(
                        ui_tool_result.widget,
                        copy_text=ui_tool_result.widget_copy_text
                    )
                except Exception as e:
                    logger.error(f"❌ Failed to stream widget: {e}", exc_info=True)

            # Stream response using ChatKit helper
            async for event in stream_agent_response(agent_context, agent_stream):
                yield event

        except Exception as e:
            logger.error(f"❌ Error in respond: {e}", exc_info=True)
            # Return error message
            from datetime import datetime, timezone
            from chatkit.types import AssistantMessageItem, AssistantMessageContent

            error_item = AssistantMessageItem(
                id=f"msg_error_{thread.id[:8]}",
                thread_id=thread.id,
                created_at=datetime.now(timezone.utc).isoformat(),
                content=[
                    AssistantMessageContent(
                        text="Lo siento, hubo un problema al procesar tu solicitud. "
                        "Por favor, intenta reformular tu pregunta.",
                        annotations=[]
                    )
                ],
            )
            yield error_item

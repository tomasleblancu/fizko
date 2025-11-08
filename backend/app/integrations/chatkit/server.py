"""
ChatKit Server Adapter - Integration with OpenAI ChatKit SDK.

This module adapts ChatKit SDK to work with our agent system,
keeping ChatKit-specific logic separate from core agent functionality.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, AsyncIterator, Dict
from uuid import uuid4

from chatkit.actions import Action
from chatkit.agents import stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.types import (
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
    UserMessageTextContent,
    InferenceOptions,
)

from app.config.database import AsyncSessionLocal
from app.services.agents import AgentService
from app.agents.core import MemoryAttachmentStore, FizkoContext
from .attachment_processor import convert_attachments_to_content
from .types import extract_user_message_text

logger = logging.getLogger(__name__)


def _gen_id(prefix: str) -> str:
    """Generate unique ID with prefix."""
    return f"{prefix}_{uuid4().hex[:8]}"


class ChatKitServerAdapter(ChatKitServer):
    """
    Adapter between ChatKit SDK and Fizko agent system.

    Responsibilities:
    - Implement ChatKitServer interface
    - Convert ChatKit types to AgentService requests
    - Stream agent responses back to ChatKit
    - Handle ChatKit-specific features (widgets, actions)

    Does NOT:
    - Contain agent execution logic (delegated to AgentService)
    - Access database directly (uses AgentService)
    - Know about Agents SDK internals
    """

    def __init__(self):
        """Initialize ChatKit server adapter with multi-agent system."""
        self.agent_service = AgentService()

        # Initialize attachment store
        self.attachment_store = MemoryAttachmentStore()

        # Initialize ChatKitServer with store from AgentService
        store = self.agent_service.get_store()
        super().__init__(store, attachment_store=self.attachment_store)

        logger.info("🤖 ChatKitServerAdapter initialized (multi-agent mode)")

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: Dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Respond to user message from ChatKit.

        This is the main entry point called by ChatKit when a user sends a message.

        Args:
            thread: ChatKit thread metadata
            item: User message item
            context: Request context (includes user_id, company_id, etc.)

        Yields:
            ThreadStreamEvent for streaming response
        """
        request_start = context.get("request_start_time", time.time())
        logger.info(f"⏱️  ChatKitServerAdapter.respond() started")

        async with AsyncSessionLocal() as db:
            # Get target item
            target_item: ThreadItem | None = item
            if target_item is None:
                target_item = await self._latest_thread_item(thread, context)

            if target_item is None:
                return

            # Extract message text
            user_message_text = (
                extract_user_message_text(target_item)
                if isinstance(target_item, UserMessageItem)
                else ""
            )
            logger.info(f"💬 User: {user_message_text[:100]}{'...' if len(user_message_text) > 100 else ''}")

            # Convert attachments to content format
            if isinstance(target_item, UserMessageItem):
                content_parts = await convert_attachments_to_content(
                    target_item,
                    self.attachment_store
                )
                logger.info(f"📝 Content: {len(content_parts)} parts")
            else:
                content_parts = [{"type": "input_text", "text": user_message_text}]

            # Get UI component info from context (passed from chatkit.py as query params)
            # Filter out string "null" values (treat as None)
            def get_value(key):
                val = context.get(key)
                return None if val in ("null", "undefined", "") else val

            ui_component = get_value("ui_component")
            entity_id = get_value("entity_id")
            entity_type = get_value("entity_type")

            logger.info(f"📊 UI Context: component={ui_component}, entity_id={entity_id}, entity_type={entity_type}")

            # Prepare company context injection
            company_id = context.get("company_id")
            company_context = ""
            is_first_message = thread.metadata is None or not thread.metadata.get("company_context_sent", False)

            if company_id and is_first_message:
                # Load company context for first message
                from app.agents.core import load_company_info, format_company_context
                company_info = await self.agent_service.context_builder.load_company_context(
                    db=db,
                    company_id=company_id,
                    use_cache=True,
                )
                company_context = format_company_context(company_info)

                # Mark as sent
                if thread.metadata is None:
                    thread.metadata = {}
                thread.metadata["company_context_sent"] = True
                logger.info("📋 Company context will be injected (first message)")

            # Add UI context if available
            ui_context_text = context.get("ui_context_text", "")

            # Prepare RunConfig with session_input_callback
            from agents import RunConfig

            def session_input_callback(history, new_input):
                """
                Merge conversation history with new input.
                Inject company_context on first message.
                """
                # Inject company context on first message (empty history)
                if len(history) == 0 and company_context:
                    history = [{
                        "role": "user",
                        "content": [{"type": "input_text", "text": company_context}]
                    }]
                    logger.debug(f"📋 Injected company_context into session ({len(company_context)} chars)")

                # Merge new input
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

            # Execute agent via AgentService (streaming)
            logger.info(f"🚀 Executing agent via AgentService...")

            agent_stream, agent_context = await self.agent_service.execute_from_chatkit(
                db=db,
                user_id=context.get("user_id", "unknown"),
                company_id=company_id or "unknown",
                thread_id=thread.id,
                message=content_parts,
                attachments=None,  # Attachments already in content_parts
                ui_component=ui_component,
                entity_id=entity_id,
                entity_type=entity_type,
                metadata=None,  # Metadata not used (passed via URL params instead)
                run_config=run_config,
                store=self.store,  # Pass store for widget streaming in tools
            )

            # Use the agent_context returned from execute_from_chatkit
            # This is the same context that was used to execute the agent,
            # so it will contain any widgets streamed by tools during execution

            # Stream widget immediately if available (before agent processing)
            ui_tool_result = context.get("ui_tool_result")
            if ui_tool_result and ui_tool_result.widget:
                widget_start = time.time()
                try:
                    logger.info(f"📊 Attempting to stream widget:")
                    logger.info(f"   - Widget type: {type(ui_tool_result.widget)}")
                    logger.info(f"   - Widget content length: {len(str(ui_tool_result.widget))} chars")
                    logger.info(f"   - Copy text: {ui_tool_result.widget_copy_text}")

                    # Stream widget using the agent_context (which is connected to response stream)
                    await agent_context.stream_widget(
                        ui_tool_result.widget,
                        copy_text=ui_tool_result.widget_copy_text
                    )
                    logger.info(f"⏱️  Widget streamed ({(time.time() - widget_start):.3f}s)")
                    logger.info(f"📊 Widget streaming completed")
                except Exception as e:
                    logger.error(f"❌ Error streaming widget: {e}", exc_info=True)

            # Stream response
            stream_loop_start = time.time()
            event_count = 0
            first_token_time = None

            async for event in stream_agent_response(agent_context, agent_stream):
                event_count += 1

                # Log event type for debugging
                event_type = type(event).__name__
                if hasattr(event, "item"):
                    item_type = type(event.item).__name__
                    logger.debug(f"📤 Event #{event_count}: {event_type} with item {item_type}")

                    # Check if this is a widget event
                    if item_type == "WidgetItem":
                        logger.info(f"🎨 Widget event detected in stream!")
                else:
                    logger.debug(f"📤 Event #{event_count}: {event_type} (no item)")

                # Log first token time
                if first_token_time is None and hasattr(event, "item") and hasattr(event.item, "content"):
                    for content in event.item.content:
                        if hasattr(content, "text") and content.text:
                            first_token_time = time.time()
                            ttft = first_token_time - request_start
                            logger.info(f"⏱️  🎯 FIRST TOKEN (TTFT: {ttft:.3f}s)")
                            break

                yield event

            # Log completion
            stream_duration = time.time() - stream_loop_start
            total_time = time.time() - request_start
            logger.info(f"⏱️  Stream completed: {event_count} events in {stream_duration:.3f}s")
            logger.info(f"⏱️  TOTAL TIME: {total_time:.3f}s")

    async def action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: Dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle custom actions from widget buttons.

        Converts actions into synthetic user messages and processes them.
        """
        logger.info(f"🎬 Custom action: type={action.type}, thread={thread.id}")

        if sender:
            logger.info(f"🎬 Sender widget item ID: {sender.id}")

            # Add sender widget item to store if not exists
            try:
                await self.store.load_item(thread.id, sender.id, context)
                logger.info(f"✅ Sender item already in store")
            except Exception:
                logger.info(f"📝 Adding sender widget item to store: {sender.id}")
                await self.store.add_thread_item(thread.id, sender, context)

        # Determine message text based on action type
        action_type = getattr(action, "type", None) or str(action)

        if action_type == "confirm":
            message_text = "Confirmar"
            logger.info("✅ User confirmed via button")
        elif action_type == "cancel":
            message_text = "Rechazar"
            logger.info("❌ User cancelled via button")
        else:
            logger.warning(f"⚠️ Unknown action type: {action_type}")
            return

        # Create UserMessageItem and add to store
        user_item = UserMessageItem(
            id=_gen_id("msg"),
            thread_id=thread.id,
            created_at=datetime.now(),
            content=[UserMessageTextContent(text=message_text)],
            attachments=[],
            inference_options=InferenceOptions(),
        )

        await self.store.add_thread_item(thread.id, user_item, context)
        logger.info(f"💾 Added user message item: {user_item.id}")

        # Process through respond()
        async for event in self.respond(thread=thread, item=user_item, context=context):
            yield event

    async def _latest_thread_item(
        self,
        thread: ThreadMetadata,
        context: Dict[str, Any]
    ) -> ThreadItem | None:
        """Get latest user message item from thread."""
        try:
            async for event in self.store.load_thread(thread.id, context=context):
                if hasattr(event, "item") and isinstance(event.item, UserMessageItem):
                    return event.item
        except Exception as e:
            logger.error(f"Error loading latest thread item: {e}")

        return None

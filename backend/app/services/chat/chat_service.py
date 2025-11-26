"""
Chat Service - Business logic for simple chat endpoint.

Handles agent execution for custom frontends (Expo, etc).
"""
from __future__ import annotations

import logging
import time
from typing import Dict, Any
from uuid import UUID

from app.agents.runner import AgentRunner, AgentExecutionRequest

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for executing chat agents.

    This service provides a simplified chat interface without ChatKit dependency,
    suitable for custom frontends like React Native Expo.
    """

    def __init__(self):
        """Initialize chat service."""
        self.runner = AgentRunner()

    async def execute(
        self,
        message: str,
        thread_id: str,
        user_id: str,
        company_id: str | None = None,
        required_context: Any | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Execute agent without streaming (blocking).

        Args:
            message: User message
            thread_id: Thread/conversation ID
            user_id: User ID
            company_id: Optional company ID
            required_context: Required context to load (identifier + entity_id + entity_type)
            metadata: Optional metadata

        Returns:
            Dict with response and metadata

        Example:
            ```python
            service = ChatService()
            result = await service.execute(
                message="¿Cuáles son mis documentos?",
                thread_id="thread_123",
                user_id="user_456",
                company_id="company_789",
                required_context={"identifier": "contact_card", "entity_id": "123"}
            )
            print(result["response"])
            ```
        """
        request_start = time.time()

        try:
            # Process required context if provided
            ui_context_text = ""
            if required_context:
                from app.agents.ui_tools import UIToolDispatcher
                from app.config.supabase import get_supabase_client

                supabase = get_supabase_client()

                # Build additional_data from required_context
                additional_data = {}
                if required_context.entity_id:
                    additional_data["entity_id"] = required_context.entity_id
                if required_context.entity_type:
                    additional_data["entity_type"] = required_context.entity_type

                logger.info(
                    f"📋 Loading context | identifier={required_context.identifier} | "
                    f"entity_id={required_context.entity_id or 'none'} | "
                    f"entity_type={required_context.entity_type or 'none'}"
                )

                ui_tool_result = await UIToolDispatcher.dispatch(
                    ui_component=required_context.identifier,
                    user_message=message,
                    company_id=company_id,
                    user_id=user_id,
                    supabase=supabase,
                    additional_data=additional_data if additional_data else None,
                )

                if ui_tool_result and ui_tool_result.success:
                    ui_context_text = ui_tool_result.context_text
                    logger.info(f"✅ Context loaded | chars={len(ui_context_text)}")
                elif ui_tool_result and not ui_tool_result.success:
                    logger.warning(f"⚠️ Context loading failed: {ui_tool_result.error}")

            # Format context to survive agent transfers
            if ui_context_text:
                full_message = f"""📋 CONTEXTO DE INTERFAZ (UI Context):
{ui_context_text}

---

Pregunta del usuario: {message}"""
            else:
                full_message = message

            # Build execution request
            request = AgentExecutionRequest(
                user_id=user_id,
                company_id=company_id or "unknown",
                thread_id=thread_id,
                message=full_message,
                attachments=None,
                ui_context=ui_context_text if ui_context_text else None,
                company_info=metadata or {},
                metadata=metadata or {},
                max_turns=10,
                channel="expo",
            )

            # Execute using AgentRunner (handles context, session, handoffs)
            result = await self.runner.execute(
                request=request,
                db=None,  # No database for expo channel
                stream=False,
            )

            elapsed = time.time() - request_start

            logger.info(
                f"✅ Chat completed | thread={thread_id[:16]} | "
                f"elapsed={elapsed:.2f}s | chars={len(result.response_text)}"
            )

            return {
                "response": result.response_text,
                "thread_id": thread_id,
                "metadata": {
                    "elapsed_ms": int(elapsed * 1000),
                    "char_count": len(result.response_text),
                }
            }

        except Exception as e:
            logger.error(f"❌ Chat error: {e}", exc_info=True)
            raise

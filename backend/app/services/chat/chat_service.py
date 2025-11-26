"""
Chat Service - Business logic for simple chat endpoint.

Handles agent execution for custom frontends (Expo, etc).

NOW USES: AgentRunnerV2 with classification-based routing (NO handoffs).
"""
from __future__ import annotations

import logging
import os
import time
from typing import Dict, Any
from uuid import UUID

from openai import AsyncOpenAI

from app.agents.runner_v2 import AgentRunnerV2, AgentExecutionRequest

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for executing chat agents using classification-based routing.

    This service uses the NEW AgentRunnerV2 system:
    - NO handoffs (eliminates "For context..." messages)
    - Classification-based routing (Classifier → Specialized Agent)
    - All agents see full thread history
    - NO sticky/non-sticky complexity
    """

    def __init__(self):
        """Initialize chat service with v2 runner."""
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.openai_client = AsyncOpenAI(api_key=api_key)

        # Initialize AgentRunnerV2
        self.runner = AgentRunnerV2(openai_client=self.openai_client)

        # Cache for orchestrators (by thread_id)
        self._orchestrator_cache: Dict[str, Any] = {}

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
        Execute agent using classification-based routing.

        Flow:
        1. Load UI context if needed
        2. Get/create orchestrator (contains all specialized agents)
        3. Run classifier → get agent_name
        4. Run specialized agent with full history

        Args:
            message: User message
            thread_id: Thread/conversation ID
            user_id: User ID
            company_id: Optional company ID
            required_context: Required context to load (identifier + entity_id + entity_type)
            metadata: Optional metadata

        Returns:
            Dict with response and metadata
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

            # Format context
            if ui_context_text:
                full_message = f"""📋 CONTEXTO DE INTERFAZ (UI Context):
{ui_context_text}

---

Pregunta del usuario: {message}"""
            else:
                full_message = message

            # Load company info if company_id is provided
            company_info_dict = {}
            if company_id:
                company_info_dict = await self._load_company_info(company_id)

            # Build execution request
            request = AgentExecutionRequest(
                user_id=user_id,
                company_id=company_id or "unknown",
                thread_id=thread_id,
                message=full_message,
                attachments=None,
                ui_context=ui_context_text if ui_context_text else None,
                company_info=company_info_dict,  # Load from Supabase
                metadata=metadata or {},
                max_turns=10,
                channel="expo",
            )

            # Get orchestrator (creates all specialized agents)
            orchestrator = await self._get_orchestrator(
                thread_id=thread_id,
                user_id=user_id,
                company_id=company_id,
            )

            # Execute using AgentRunnerV2 (classification-based routing)
            result = await self.runner.execute(
                request=request,
                orchestrator=orchestrator,  # NEW: orchestrator provides specialized agents
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

    async def _get_orchestrator(
        self,
        thread_id: str,
        user_id: str | None = None,
        company_id: str | None = None,
    ) -> Any:
        """
        Get or create orchestrator for a thread.

        Orchestrator is cached per thread_id to maintain agent instances.

        Args:
            thread_id: Thread ID
            user_id: Optional user ID
            company_id: Optional company ID

        Returns:
            MultiAgentOrchestrator instance
        """
        # Check cache first
        if thread_id in self._orchestrator_cache:
            return self._orchestrator_cache[thread_id]

        # Create new orchestrator
        from app.agents.orchestration.multi_agent_orchestrator import (
            create_multi_agent_orchestrator,
        )

        # Parse company_id to UUID if needed
        company_id_uuid = None
        if company_id:
            try:
                company_id_uuid = UUID(company_id) if isinstance(company_id, str) else company_id
            except (ValueError, AttributeError):
                logger.warning(f"⚠️ Invalid company_id format: {company_id}")

        orchestrator = await create_multi_agent_orchestrator(
            db=None,  # No DB for expo channel
            openai_client=self.openai_client,
            user_id=user_id,
            thread_id=thread_id,
            company_id=company_id_uuid,
            vector_store_ids=None,
            channel="expo",
        )

        # Cache for future requests
        self._orchestrator_cache[thread_id] = orchestrator

        logger.info(
            f"🔀 New orchestrator cached | thread={thread_id[:8]}... | "
            f"agents={len(orchestrator.agents)}"
        )

        return orchestrator

    async def _load_company_info(self, company_id: str) -> Dict[str, Any]:
        """
        Load company information from Supabase.

        Args:
            company_id: Company UUID

        Returns:
            Dict with company information (rut, razon_social, etc.)
        """
        try:
            from app.config.supabase import get_supabase_client

            supabase = get_supabase_client()

            # Query company_tax_info (Python Supabase uses .from_() not .table())
            response = supabase.from_("company_tax_info").select("*").eq("company_id", company_id).single().execute()

            if response.data:
                company_info = response.data
                logger.info(f"✅ Loaded company info | RUT: {company_info.get('rut', 'N/A')}")
                return company_info
            else:
                logger.warning(f"⚠️ No company info found for company_id: {company_id}")
                return {}

        except Exception as e:
            logger.warning(f"⚠️ Failed to load company info: {e}")
            return {}

    def clear_cache(self, thread_id: str | None = None):
        """
        Clear orchestrator cache.

        Args:
            thread_id: If provided, clears only this thread's cache.
                      If None, clears entire cache.
        """
        if thread_id:
            if thread_id in self._orchestrator_cache:
                del self._orchestrator_cache[thread_id]
                logger.info(f"🗑️ Cleared cache for thread: {thread_id}")
        else:
            self._orchestrator_cache.clear()
            logger.info("🗑️ Cleared entire orchestrator cache")

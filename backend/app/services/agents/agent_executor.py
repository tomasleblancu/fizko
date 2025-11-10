"""
Agent Executor Service - Business logic for agent execution.

Coordinates between database, UI tools, attachments, and agent runner.
Used by both ChatKit (web) and WhatsApp channels.
"""
from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.runner import AgentRunner, AgentExecutionRequest, AgentExecutionResult
from .context_builder import ContextBuilder

logger = logging.getLogger(__name__)


class AgentService:
    """
    Business logic service for agent execution.

    This service orchestrates the execution of agents across different channels
    (ChatKit web, WhatsApp, etc.) by:
    - Loading company context
    - Processing UI tools
    - Handling attachments
    - Coordinating with AgentRunner
    - Managing database operations

    This is the main entry point for executing agents from any channel.
    """

    def __init__(self):
        """Initialize agent service with multi-agent system."""
        self.runner = AgentRunner()
        self.context_builder = ContextBuilder()
        logger.info("🎯 AgentService initialized (multi-agent mode)")

    async def execute_from_chatkit(
        self,
        db: AsyncSession,
        user_id: str,
        company_id: str,
        thread_id: str,
        message: str | List[Dict[str, Any]],
        attachments: Optional[List[Dict[str, Any]]] = None,
        ui_component: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        run_config = None,
        store = None,
    ) -> Any:
        """
        Execute agent from ChatKit request (streaming).

        Args:
            db: Database session
            user_id: User UUID
            company_id: Company UUID
            thread_id: Thread/conversation ID
            message: Message text or content_parts
            attachments: List of processed attachments
            ui_component: UI component name (from metadata)
            entity_id: Entity ID (from metadata)
            entity_type: Entity type (from metadata)
            metadata: Additional metadata
            run_config: RunConfig for session_input_callback

        Returns:
            StreamedRunResult object with .stream_events() method
            (used by ChatKit's stream_agent_response)
        """
        logger.info("=" * 60)
        logger.info("🌐 AgentService.execute_from_chatkit()")
        logger.info(f"   user_id={user_id}")
        logger.info(f"   company_id={company_id}")
        logger.info(f"   thread_id={thread_id}")
        logger.info(f"   ui_component={ui_component}")
        logger.info("=" * 60)

        # 1. Load company context
        company_info = await self.context_builder.load_company_context(
            db=db,
            company_id=company_id,
            use_cache=True,
        )

        # 2. Load UI Tool context if ui_component provided
        ui_context = None
        if ui_component:
            message_text = message if isinstance(message, str) else ""
            ui_context = await self.context_builder.load_ui_tool_context(
                db=db,
                ui_component=ui_component,
                entity_id=entity_id,
                entity_type=entity_type,
                user_id=user_id,
                company_id=company_id,
                user_message=message_text,
            )

        # 3. Build execution request
        request = AgentExecutionRequest(
            user_id=user_id,
            company_id=company_id,
            thread_id=thread_id,
            message=message,
            attachments=attachments,
            ui_context=ui_context,
            company_info=company_info,
            metadata=metadata or {},
            channel="web",
        )

        # 4. Execute via runner (streaming)
        # IMPORTANT: We need to call the async parts first, then return the sync streaming result
        logger.info("🚀 Starting agent execution (streaming)...")

        # Get agent (async) - also creates/returns session for active agent detection
        agent, _, session = await self.runner._get_agent(request, db)

        # Build context (async) - pass store for widget streaming in tools
        context = await self.runner._build_context(request, db, store=store)

        # Prepare input (sync)
        agent_input = self.runner._prepare_input(request)

        # Execute agent (sync - returns StreamedRunResult immediately)
        from agents import Runner
        result = Runner.run_streamed(
            agent,
            agent_input,
            context=context,
            session=session,
            max_turns=request.max_turns,
            run_config=run_config,
        )

        # Return both the result and context (context is needed for stream_agent_response to capture tool widgets)
        return (result, context)

    async def execute_from_whatsapp(
        self,
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        conversation_id: str,
        message: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        ui_context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        run_config = None,
    ) -> tuple[str, str]:
        """
        Execute agent from WhatsApp request (non-streaming).

        Args:
            db: Database session
            user_id: User UUID
            company_id: Company UUID
            conversation_id: Conversation ID (used as thread_id)
            message: Message text
            attachments: List of processed attachments
            ui_context: Pre-loaded UI context (from notification detection)
            metadata: Additional metadata
            run_config: RunConfig for session_input_callback

        Returns:
            (response_text, conversation_id) tuple
        """
        logger.info("=" * 60)
        logger.info("📱 AgentService.execute_from_whatsapp()")
        logger.info(f"   user_id={user_id}")
        logger.info(f"   company_id={company_id}")
        logger.info(f"   conversation_id={conversation_id}")
        logger.info("=" * 60)

        # 1. Load company context
        company_info = await self.context_builder.load_company_context(
            db=db,
            company_id=str(company_id),
            use_cache=True,
        )

        # 2. Build execution request
        request = AgentExecutionRequest(
            user_id=str(user_id),
            company_id=str(company_id),
            thread_id=conversation_id,
            message=message,
            attachments=attachments,
            ui_context=ui_context,  # Already loaded by WhatsApp webhook
            company_info=company_info,
            metadata=metadata or {},
            channel="whatsapp",
        )

        # 3. Execute via runner (non-streaming)
        logger.info("🚀 Starting agent execution (non-streaming)...")
        result: AgentExecutionResult = await self.runner.execute(
            request=request,
            db=db,
            stream=False,
            run_config=run_config,
        )

        logger.info(f"✅ Agent execution complete: {len(result.response_text)} chars")

        return (result.response_text, conversation_id)

    def get_store(self):
        """
        Get store instance for ChatKit integration.

        This is used by ChatKitServerAdapter to initialize ChatKitServer.
        """
        try:
            from app.stores import HybridStore, SupabaseStore
            supabase_store = SupabaseStore()
            return HybridStore(supabase_store=supabase_store)
        except Exception as e:
            logger.warning(f"Supabase not available, using MemoryStore: {e}")
            from app.stores import MemoryStore
            return MemoryStore()

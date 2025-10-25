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

        # Load company info automatically at thread start
        company_id = context.get("company_id")
        if company_id:
            company_info = await self._load_company_info(company_id)
            agent_context.company_info = company_info
            if company_info and "company" in company_info:
                logger.info(f"📋 Loaded company info for: {company_info['company'].get('business_name', 'Unknown')}")
            elif company_info and "error" in company_info:
                logger.warning(f"⚠️ Failed to load company info: {company_info['error']}")
        else:
            logger.warning("⚠️ No company_id in context, skipping company info load")

        target_item: ThreadItem | None = item
        if target_item is None:
            target_item = await self._latest_thread_item(thread, context)

        if target_item is None:
            return

        # Extract text from user message
        user_message = _user_message_text(target_item) if isinstance(target_item, UserMessageItem) else ""
        logger.info(f"User: {user_message[:100]}")

        # Stream widget immediately if available (before agent processing)
        ui_tool_result = context.get("ui_tool_result")
        if ui_tool_result and ui_tool_result.widget:
            logger.info("📊 Streaming widget immediately before agent processing")
            try:
                await agent_context.stream_widget(
                    ui_tool_result.widget,
                    copy_text=ui_tool_result.widget_copy_text
                )
                logger.info("✅ Widget streamed successfully")
            except Exception as e:
                logger.error(f"❌ Error streaming widget: {e}", exc_info=True)

        # Prepend company info to user message if available
        if agent_context.company_info and "company" in agent_context.company_info:
            company_data = agent_context.company_info["company"]
            company_context = f"""<company_info>
RUT: {company_data.get('rut', 'N/A')}
Razón Social: {company_data.get('business_name', 'N/A')}
Nombre Fantasía: {company_data.get('trade_name', 'N/A')}"""

            if "tax_info" in company_data:
                tax_info = company_data["tax_info"]
                company_context += f"""
Régimen Tributario: {tax_info.get('tax_regime', 'N/A')}
Código Actividad: {tax_info.get('sii_activity_code', 'N/A')} - {tax_info.get('sii_activity_name', 'N/A')}
Representante Legal: {tax_info.get('legal_representative_name', 'N/A')} (RUT: {tax_info.get('legal_representative_rut', 'N/A')})"""

            company_context += "\n</company_info>\n\n"
            user_message = f"{company_context}{user_message}"
            logger.info(f"📋 Prepended company info to user message")

        # Prepend UI context if available (from UI Tools system)
        ui_context_text = context.get("ui_context_text", "")
        if ui_context_text:
            logger.info(f"📍 Prepending UI context ({len(ui_context_text)} chars) to user message")
            user_message = f"{ui_context_text}\n\n{user_message}"

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

    async def _load_company_info(self, company_id: str) -> dict[str, Any]:
        """
        Load company information from database.

        This is the same logic as get_company_info tool, but called automatically
        at thread initialization instead of being a tool.
        """
        from uuid import UUID
        from sqlalchemy import select
        from ..db.models import Company, CompanyTaxInfo

        try:
            async with AsyncSessionLocal() as db:
                # Get company basic info
                stmt = select(Company).where(Company.id == UUID(company_id))
                result = await db.execute(stmt)
                company = result.scalar_one_or_none()

                if not company:
                    return {"error": "Empresa no encontrada"}

                # Get tax info
                tax_stmt = select(CompanyTaxInfo).where(CompanyTaxInfo.company_id == UUID(company_id))
                tax_result = await db.execute(tax_stmt)
                tax_info = tax_result.scalar_one_or_none()

                # Build complete company info
                company_data = {
                    "id": str(company.id),
                    "rut": company.rut,
                    "business_name": company.business_name,
                    "trade_name": company.trade_name,
                    "address": company.address,
                    "phone": company.phone,
                    "email": company.email,
                    "created_at": company.created_at.isoformat() if company.created_at else None,
                    "updated_at": company.updated_at.isoformat() if company.updated_at else None,
                }

                # Add tax info if available
                if tax_info:
                    company_data["tax_info"] = {
                        "tax_regime": tax_info.tax_regime,
                        "sii_activity_code": tax_info.sii_activity_code,
                        "sii_activity_name": tax_info.sii_activity_name,
                        "legal_representative_rut": tax_info.legal_representative_rut,
                        "legal_representative_name": tax_info.legal_representative_name,
                        "start_of_activities_date": tax_info.start_of_activities_date.isoformat() if tax_info.start_of_activities_date else None,
                        "accounting_start_month": tax_info.accounting_start_month,
                    }

                return {"company": company_data}
        except Exception as e:
            logger.error(f"Error loading company info: {e}")
            return {"error": str(e)}

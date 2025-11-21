"""
WhatsApp Agent Runner - Execute AI agents for WhatsApp conversations.

This module handles agent execution specifically for WhatsApp messages,
integrating with the multi-agent system and formatting responses appropriately
for WhatsApp (plain text, no markdown).
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from supabase import Client

from app.agents.runner import AgentExecutionRequest, AgentRunner

logger = logging.getLogger(__name__)


class WhatsAppAgentRunner:
    """
    Execute AI agents for WhatsApp messages.

    This class:
    1. Loads company context for the user
    2. Executes the multi-agent system (supervisor + specialized agents)
    3. Formats responses for WhatsApp (plain text, no markdown)

    Usage:
        ```python
        runner = WhatsAppAgentRunner(supabase_client)
        response = await runner.run(
            user_id="user-uuid",
            company_id="company-uuid",
            thread_id="thread-uuid",
            message="¿Cuánto IVA tengo que pagar este mes?",
        )
        # response = "Según tus documentos de enero 2025, tu IVA a pagar es $450.000"
        ```
    """

    def __init__(self, supabase, db=None):
        """
        Initialize WhatsApp agent runner.

        Args:
            supabase: Supabase client (SupabaseClient or raw Client)
            db: Optional async database session (for SQLAlchemy operations)
        """
        # Get underlying client if wrapped
        self.client = supabase.client if hasattr(supabase, 'client') else supabase
        self.db = db
        self.agent_runner = AgentRunner()

    async def run(
        self,
        user_id: str,
        company_id: str,
        thread_id: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Execute agent with WhatsApp message and return text response.

        Args:
            user_id: User UUID
            company_id: Company UUID
            thread_id: Thread/conversation UUID
            message: User message text
            metadata: Optional metadata (phone, conversation_id, etc.)

        Returns:
            Agent response text (plain text, no markdown)
        """
        try:
            # 1. Load company context
            company_info = await self._load_company_context(company_id)

            # 2. Build execution request
            request = AgentExecutionRequest(
                user_id=user_id,
                company_id=company_id,
                thread_id=thread_id,
                message=message,
                company_info=company_info,
                metadata=metadata or {},
                channel="whatsapp",  # Important: tells agents to avoid markdown
                max_turns=10,
            )

            # 3. Execute agent (non-streaming for WhatsApp)
            logger.info(
                f"🤖 [WhatsApp Agent] Executing for user {user_id[:8]} | "
                f"company {company_id[:8]} | thread {thread_id[:8]}"
            )

            # For WhatsApp with session memory, we need to pass the message as a string
            # not as a list (which requires a session_input_callback)
            # So we'll create the request with just the text message
            result = await self.agent_runner.execute(
                request=request,
                db=self.db,
                stream=False,
            )

            # 4. Extract and format response text
            response_text = result.response_text

            # Remove markdown formatting for WhatsApp
            response_text = self._format_for_whatsapp(response_text)

            logger.info(
                f"✅ [WhatsApp Agent] Response generated: {len(response_text)} chars | "
                f"thread {thread_id[:8]}"
            )

            return response_text

        except Exception as e:
            logger.error(
                f"❌ [WhatsApp Agent] Error executing agent: {e}",
                exc_info=True
            )
            return "Lo siento, ocurrió un error al procesar tu mensaje. Por favor intenta nuevamente."

    async def _load_company_context(self, company_id: str) -> dict:
        """
        Load company information from database.

        Args:
            company_id: Company UUID string

        Returns:
            Company info dict with RUT, name, tax info, etc.
        """
        try:
            # Use Supabase to load company info
            response = (
                self.client.table("companies")
                .select("id, rut, business_name, trade_name, created_at")
                .eq("id", company_id)
                .execute()
            )

            if not response.data or len(response.data) == 0:
                logger.warning(f"⚠️  Company not found: {company_id}")
                return {}

            company = response.data[0]

            # Try to get tax info
            tax_info = {}
            try:
                tax_response = (
                    self.client.table("company_tax_info")
                    .select("tax_regime, sii_activity_code, sii_activity_name")
                    .eq("company_id", company_id)
                    .execute()
                )
                if tax_response.data and len(tax_response.data) > 0:
                    tax_info = tax_response.data[0]
            except Exception as e:
                logger.warning(f"Could not load tax info: {e}")

            # Format company info similar to AgentService
            company_info = {
                "id": company.get("id"),
                "rut": company.get("rut"),
                "name": company.get("business_name") or company.get("trade_name"),
                "business_name": company.get("business_name"),
                "trade_name": company.get("trade_name"),
                "tax_regime": tax_info.get("tax_regime"),
                "activity_code": tax_info.get("sii_activity_code"),
                "activity_name": tax_info.get("sii_activity_name"),
                "created_at": company.get("created_at"),
            }

            logger.info(
                f"✅ [WhatsApp Agent] Loaded company: {company_info.get('name')} | "
                f"RUT: {company.get('rut')}"
            )

            return company_info

        except Exception as e:
            logger.error(f"❌ Error loading company context: {e}", exc_info=True)
            return {}

    def _format_for_whatsapp(self, text: str) -> str:
        """
        Format text for WhatsApp by removing markdown.

        WhatsApp doesn't support markdown, so we need to clean it up:
        - Remove ** bold markers
        - Remove __ underline markers
        - Remove ` code markers
        - Remove ### headers
        - Keep line breaks

        Args:
            text: Text with potential markdown

        Returns:
            Plain text without markdown
        """
        import re

        # Remove bold markers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)

        # Remove code markers
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Remove headers but keep text
        text = re.sub(r'#{1,6}\s+', '', text)

        # Remove links but keep text [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Clean up multiple line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

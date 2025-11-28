"""
Chat Service - Business logic for simple chat endpoint.

Handles agent execution for custom frontends (Expo, etc).

NOW USES: AgentRunnerV2 with classification-based routing (NO handoffs).
"""
from __future__ import annotations

import base64
import logging
import os
import time
from typing import Dict, Any, List
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

    def _process_attachments(
        self,
        attachment_ids: List[str],
        metadata: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Process attachment IDs and convert to content parts for the agent.

        Args:
            attachment_ids: List of attachment IDs to process
            metadata: Optional metadata containing attachment info

        Returns:
            List of content parts (input_text or input_image)
        """
        from app.agents.core.memory_attachment_store import (
            get_attachment_content,
            _attachment_storage
        )

        content_parts = []

        for attachment_id in attachment_ids:
            try:
                # Get base64 content from memory store
                base64_content = get_attachment_content(attachment_id)

                # Also try to get raw bytes for metadata
                raw_bytes = _attachment_storage.get(attachment_id)

                if not base64_content and not raw_bytes:
                    logger.warning(f"⚠️ Attachment content not found: {attachment_id}")
                    content_parts.append({
                        "type": "input_text",
                        "text": f"[Archivo adjunto no disponible: {attachment_id}]"
                    })
                    continue

                # Try to determine MIME type from metadata or bytes
                mime_type = "application/octet-stream"
                filename = "unknown"

                # Check if metadata contains attachment info
                if metadata and "attachment_metadata" in metadata:
                    att_meta = metadata["attachment_metadata"].get(attachment_id, {})
                    mime_type = att_meta.get("mime_type", mime_type)
                    filename = att_meta.get("filename", filename)
                elif raw_bytes:
                    # Try to guess MIME type from magic bytes
                    if raw_bytes[:2] == b'\xff\xd8':
                        mime_type = "image/jpeg"
                    elif raw_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                        mime_type = "image/png"
                    elif raw_bytes[:4] == b'GIF8':
                        mime_type = "image/gif"
                    elif raw_bytes[:4] == b'%PDF':
                        mime_type = "application/pdf"

                # Handle images
                if mime_type.startswith("image/"):
                    if not base64_content and raw_bytes:
                        # Convert raw bytes to base64
                        base64_content = base64.b64encode(raw_bytes).decode('utf-8')

                    if base64_content:
                        # Clean base64 content
                        base64_content = base64_content.strip().replace('\n', '').replace('\r', '').replace(' ', '')

                        # Validate base64
                        try:
                            decoded = base64.b64decode(base64_content)
                            logger.info(f"✅ Valid image attachment: {filename} ({len(decoded)} bytes)")
                        except Exception as e:
                            logger.error(f"❌ Invalid base64 for {attachment_id}: {e}")
                            content_parts.append({
                                "type": "input_text",
                                "text": f"[Imagen con formato inválido: {filename}]"
                            })
                            continue

                        # Create data URL
                        data_url = f"data:{mime_type};base64,{base64_content}"
                        content_parts.append({
                            "type": "input_image",
                            "image_url": data_url
                        })
                        logger.info(f"📸 Added image to content: {filename}")
                    else:
                        content_parts.append({
                            "type": "input_text",
                            "text": f"[Imagen no disponible: {filename}]"
                        })
                else:
                    # Non-image files
                    content_parts.append({
                        "type": "input_text",
                        "text": f"[Archivo adjunto: {filename} ({mime_type})]"
                    })
                    logger.info(f"📄 Added file reference: {filename}")

            except Exception as e:
                logger.error(f"❌ Error processing attachment {attachment_id}: {e}", exc_info=True)
                content_parts.append({
                    "type": "input_text",
                    "text": f"[Error procesando archivo adjunto: {attachment_id}]"
                })

        return content_parts

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

            # Process attachments if present in metadata
            attachment_content_parts = []
            attachment_ids = []

            if metadata and "attachments" in metadata:
                attachment_ids = metadata["attachments"]
                if isinstance(attachment_ids, list) and attachment_ids:
                    logger.info(f"📎 Processing {len(attachment_ids)} attachment(s)")
                    attachment_content_parts = self._process_attachments(
                        attachment_ids=attachment_ids,
                        metadata=metadata
                    )

            # Format message (convert to content_parts if we have attachments)
            if attachment_content_parts:
                # Build content_parts: [text, image1, image2, ...]
                content_parts = []

                # Add UI context if present
                if ui_context_text:
                    content_parts.append({
                        "type": "input_text",
                        "text": f"""📋 CONTEXTO DE INTERFAZ (UI Context):
{ui_context_text}

---"""
                    })

                # Add user message
                content_parts.append({
                    "type": "input_text",
                    "text": message
                })

                # Add attachment content parts
                content_parts.extend(attachment_content_parts)

                full_message = content_parts

                logger.info(
                    f"📦 Built message with {len(content_parts)} content parts "
                    f"({len([p for p in content_parts if p['type'] == 'input_image'])} images)"
                )
            else:
                # No attachments - use simple text format
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
                attachments=None,  # Content parts include images directly
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

            # Query company using the repository
            company = await supabase.companies.get_by_id(company_id, include_tax_info=True)

            if not company:
                logger.warning(f"⚠️ No company found for company_id: {company_id}")
                return {}

            # Combine company info from both tables
            company_info = {
                "rut": company.get("rut"),
                "business_name": company.get("business_name"),
                "trade_name": company.get("trade_name"),
            }

            # Add tax info if available
            if tax_info := company.get("company_tax_info"):
                company_info.update(tax_info)

            logger.info(f"✅ Loaded company info | RUT: {company_info.get('rut', 'N/A')}")
            return company_info

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

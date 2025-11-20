"""
Agent Executor Service - Simplified for Backend V2.

Stateless version without database dependencies.
Coordinates agent execution with provided context.
"""
from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from app.agents.runner import AgentRunner, AgentExecutionRequest, AgentExecutionResult

logger = logging.getLogger(__name__)


class AgentService:
    """
    Simplified business logic service for agent execution.

    This is a stateless version designed for backend-v2.
    Unlike the full backend, this service:
    - Does NOT connect to database
    - Does NOT load company context from DB
    - Does NOT handle UI tools (no ChatKit integration)
    - Accepts company info as parameter
    - Focuses on SII-related agent tasks

    Used for executing agents with pre-loaded context.
    """

    def __init__(self):
        """Initialize agent service with multi-agent system."""
        self.runner = AgentRunner()
        logger.info("🎯 AgentService initialized (stateless mode)")

    async def execute(
        self,
        user_id: str,
        company_id: str,
        thread_id: str,
        message: str | List[Dict[str, Any]],
        company_info: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        channel: str = "api",
        stream: bool = False,
    ) -> AgentExecutionResult:
        """
        Execute agent with provided context (stateless).

        Args:
            user_id: User identifier
            company_id: Company identifier
            thread_id: Thread/conversation ID
            message: Message text or content_parts
            company_info: Pre-loaded company information (optional)
            attachments: List of processed attachments (optional)
            metadata: Additional metadata (optional)
            channel: Channel name (default: "api")
            stream: Whether to stream response (default: False)

        Returns:
            AgentExecutionResult with response_text and metadata

        Example:
            ```python
            service = AgentService()

            # Minimal execution
            result = await service.execute(
                user_id="user123",
                company_id="77794858-k",
                thread_id="thread_1",
                message="¿Qué documentos tengo pendientes?"
            )
            print(result.response_text)

            # With company context
            company_info = {
                "rut": "77794858-k",
                "razon_social": "EMPRESA DEMO SPA",
                "actividad_economica": "Servicios de software"
            }
            result = await service.execute(
                user_id="user123",
                company_id="77794858-k",
                thread_id="thread_1",
                message="Dame un resumen de mi empresa",
                company_info=company_info
            )
            ```
        """

        # Build execution request
        request = AgentExecutionRequest(
            user_id=user_id,
            company_id=company_id,
            thread_id=thread_id,
            message=message,
            attachments=attachments,
            ui_context=None,  # No UI tools in stateless mode
            company_info=company_info or {},
            metadata=metadata or {},
            channel=channel,
        )

        # Execute via runner
        logger.info(f"🚀 Executing agent for company {company_id}, thread {thread_id}")
        result: AgentExecutionResult = await self.runner.execute(
            request=request,
            db=None,  # No database in stateless mode
            stream=stream,
            run_config=None,
        )

        logger.info(f"✅ Agent execution completed: {len(result.response_text)} chars")
        return result

    async def execute_with_sii_context(
        self,
        user_id: str,
        rut: str,
        thread_id: str,
        message: str,
        contribuyente_info: Dict[str, Any],
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentExecutionResult:
        """
        Execute agent with SII contribuyente context.

        This is a specialized method for backend-v2 that accepts
        contribuyente info from the SII integration and formats it
        as company context for the agent.

        Args:
            user_id: User identifier
            rut: Company RUT (used as company_id)
            thread_id: Thread/conversation ID
            message: User message
            contribuyente_info: Information from SII (from /verify endpoint)
            attachments: Optional attachments
            metadata: Additional metadata

        Returns:
            AgentExecutionResult

        Example:
            ```python
            # After calling /api/sii/verify
            verify_response = requests.post("/api/sii/verify", json={
                "rut": "77794858",
                "dv": "k",
                "password": "******"
            })

            contribuyente_info = verify_response.json()["contribuyente_info"]

            # Execute agent with SII context
            service = AgentService()
            result = await service.execute_with_sii_context(
                user_id="user123",
                rut="77794858-k",
                thread_id="thread_1",
                message="¿Cuál es mi razón social?",
                contribuyente_info=contribuyente_info
            )
            ```
        """

        # Format contribuyente info as company context
        company_info = self._format_contribuyente_as_company_info(
            rut=rut,
            contribuyente_info=contribuyente_info
        )

        # Execute with formatted context
        return await self.execute(
            user_id=user_id,
            company_id=rut,
            thread_id=thread_id,
            message=message,
            company_info=company_info,
            attachments=attachments,
            metadata=metadata,
            channel="sii",
        )

    async def execute_from_chatkit(
        self,
        user_id: str,
        company_id: str,
        thread_id: str,
        message: str | List[Dict[str, Any]],
        attachments: Optional[List[Dict[str, Any]]] = None,
        ui_context: Optional[str] = None,
        company_info: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        run_config = None,
        store = None,
    ) -> Any:
        """
        Execute agent from ChatKit request (streaming).

        This method is designed for ChatKit integration and returns a streaming result
        compatible with chatkit.agents.stream_agent_response().

        Args:
            user_id: User UUID
            company_id: Company UUID
            thread_id: Thread/conversation ID
            message: Message text or content_parts
            attachments: List of processed attachments
            ui_context: UI context text (from UI tools)
            company_info: Pre-loaded company information
            metadata: Additional metadata
            run_config: RunConfig for session_input_callback
            store: ChatKit store (needed for widget streaming in tools)

        Returns:
            Tuple of (StreamedRunResult, FizkoContext) for use with stream_agent_response()
        """

        # Build execution request
        request = AgentExecutionRequest(
            user_id=user_id,
            company_id=company_id,
            thread_id=thread_id,
            message=message,
            attachments=attachments,
            ui_context=ui_context,
            company_info=company_info or {},
            metadata=metadata or {},
            channel="web",
        )

        # Get agent (async) - also creates/returns session for active agent detection
        agent, _, session = await self.runner._get_agent(request, db=None)

        # Build context (async) - pass store for widget streaming in tools
        context = await self.runner._build_context(request, db=None, store=store)

        # For ChatKit with session memory, pass string directly (not list)
        # This avoids the session_input_callback requirement
        if isinstance(message, str):
            agent_input = message
        else:
            # If it's a list, extract the text from first part
            agent_input = message[0].get("text", "") if message else ""

        # Execute agent (sync - returns StreamedRunResult immediately)
        from agents import Runner
        result = Runner.run_streamed(
            agent,
            agent_input,
            context=context,
            session=session,
            max_turns=request.max_turns or 10,
            run_config=run_config,
        )

        # Return both the result and context (context is needed for stream_agent_response to capture tool widgets)
        return (result, context)

    @staticmethod
    def _format_contribuyente_as_company_info(
        rut: str,
        contribuyente_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format contribuyente info from SII as company context.

        Args:
            rut: Company RUT
            contribuyente_info: Raw contribuyente info from SII

        Returns:
            Formatted company info dict
        """
        return {
            "rut": rut,
            "razon_social": contribuyente_info.get("razon_social", ""),
            "nombre_fantasia": contribuyente_info.get("nombre_fantasia", ""),
            "actividad_economica": contribuyente_info.get("actividad_economica", ""),
            "direccion": contribuyente_info.get("direccion", ""),
            "comuna": contribuyente_info.get("comuna", ""),
            "email": contribuyente_info.get("email", ""),
            "telefono": contribuyente_info.get("telefono", ""),
            "actividades": contribuyente_info.get("actividades", []),
            "representante_legal": contribuyente_info.get("representante_legal", {}),
            "tipo_contribuyente": contribuyente_info.get("tipo_contribuyente", ""),
            # Metadata
            "_source": "sii_verification",
            "_raw_data": contribuyente_info,
        }

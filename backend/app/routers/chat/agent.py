"""
Chat Agent Router - Simplified for Backend V2.

Stateless chat endpoint that executes agents with provided context.
Uses Supabase for UIToolDispatcher integration.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.agents import AgentService, ContextBuilder
from app.agents.ui_tools import UIToolDispatcher
from app.config.supabase import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str = Field(..., description="User message")
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="User identifier")
    company_id: Optional[str] = Field(None, description="Company RUT (optional)")
    thread_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Thread ID for conversation continuity")

    # Context (optional)
    company_info: Optional[Dict[str, Any]] = Field(None, description="Company information from SII")
    recent_compras: Optional[List[Dict[str, Any]]] = Field(None, description="Recent purchase documents")
    recent_ventas: Optional[List[Dict[str, Any]]] = Field(None, description="Recent sales documents")
    recent_f29: Optional[Dict[str, Any]] = Field(None, description="Recent F29 form")
    custom_context: Optional[str] = Field(None, description="Additional custom context")

    # Metadata (optional)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "¿Qué documentos tributarios debo emitir este mes?",
                "user_id": "user_123",
                "company_id": "77794858-k",
                "thread_id": "thread_abc123",
                "company_info": {
                    "rut": "77794858-k",
                    "razon_social": "EMPRESA DEMO SPA",
                    "actividad_economica": "Servicios de software"
                }
            }
        }


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str = Field(..., description="Agent response text")
    thread_id: str = Field(..., description="Thread ID for conversation continuity")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Los documentos tributarios que debes emitir este mes incluyen...",
                "thread_id": "thread_abc123",
                "metadata": {
                    "company_id": "77794858-k",
                    "execution_time_ms": 1234
                }
            }
        }


class ChatWithSIIRequest(BaseModel):
    """Request for chat with SII context."""
    message: str = Field(..., description="User message")
    rut: str = Field(..., description="Company RUT")
    contribuyente_info: Dict[str, Any] = Field(..., description="Contribuyente info from /verify endpoint")
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="User identifier")
    thread_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Thread ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Dame un resumen de mi empresa",
                "rut": "77794858-k",
                "user_id": "user_123",
                "contribuyente_info": {
                    "razon_social": "EMPRESA DEMO SPA",
                    "actividad_economica": "Servicios de software",
                    "direccion": "Av. Apoquindo 1234"
                }
            }
        }


# ============================================================================
# Endpoints
# ============================================================================

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    ui_component: Optional[str] = Query(None, description="UI component that triggered the message"),
    entity_id: Optional[str] = Query(None, description="Entity ID for UI context"),
    entity_type: Optional[str] = Query(None, description="Entity type for UI context"),
) -> ChatResponse:
    """
    Chat with AI agent (stateless with UI Tools support).

    Executes agent with provided context. No persistence - each request is independent.

    Features:
    - Stateless execution with Supabase for UI Tools
    - Accepts optional company context
    - Accepts optional document context (compras, ventas, F29)
    - Thread ID for client-side conversation tracking
    - Rich context building
    - **UI Tools**: Auto-loads context from Supabase when ui_component is specified

    Example:
        ```python
        response = requests.post("/api/chat", json={
            "message": "¿Qué es el IVA?",
            "user_id": "user_123",
            "company_id": "demo"
        })
        ```

    Example with UI component context:
        ```python
        response = requests.post(
            "/api/chat?ui_component=contact_card&entity_id=12345678-9",
            json={
                "message": "Dame info de este contacto",
                "user_id": "user_123",
                "company_id": "77794858-k"
            }
        )
        ```

    Example with full context:
        ```python
        response = requests.post("/api/chat", json={
            "message": "Dame un análisis tributario",
            "user_id": "user_123",
            "company_id": "77794858-k",
            "company_info": {"rut": "77794858-k", "razon_social": "DEMO SPA"},
            "recent_compras": [...],
            "recent_ventas": [...],
            "recent_f29": {...}
        })
        ```
    """
    try:
        # Build rich context if documents provided
        context_text = None
        if any([request.recent_compras, request.recent_ventas, request.recent_f29, request.custom_context]):
            context_text = ContextBuilder.build_agent_context(
                company_info=request.company_info,
                recent_compras=request.recent_compras,
                recent_ventas=request.recent_ventas,
                recent_f29=request.recent_f29,
                custom_context=request.custom_context,
            )

        # NEW: Dispatch to UI Tools system if ui_component is present
        ui_context_text = ""
        if ui_component and ui_component != "null":
            supabase = get_supabase_client()

            # Build additional_data dict from query params
            additional_data = {}
            if entity_id:
                additional_data["entity_id"] = entity_id
            if entity_type:
                additional_data["entity_type"] = entity_type

            ui_tool_result = await UIToolDispatcher.dispatch(
                ui_component=ui_component,
                user_message=request.message,
                company_id=request.company_id,
                user_id=request.user_id,
                supabase=supabase,
                additional_data=additional_data if additional_data else None,
            )

            if ui_tool_result and ui_tool_result.success:
                ui_context_text = ui_tool_result.context_text
                logger.info(f"✅ UI Tool context loaded: {len(ui_context_text)} chars")
            elif ui_tool_result and not ui_tool_result.success:
                logger.warning(f"⚠️ UI Tool failed: {ui_tool_result.error}")

        # Combine context texts
        combined_context = None
        if context_text and ui_context_text:
            combined_context = f"{ui_context_text}\n\n---\n\n{context_text}"
        elif ui_context_text:
            combined_context = ui_context_text
        elif context_text:
            combined_context = context_text

        # Add context to metadata if generated
        metadata = request.metadata or {}
        if combined_context:
            metadata["context_text"] = combined_context

        # Execute agent
        service = AgentService()
        result = await service.execute(
            user_id=request.user_id,
            company_id=request.company_id or "demo",
            thread_id=request.thread_id,
            message=request.message,
            company_info=request.company_info,
            metadata=metadata,
            channel="chat_api",
        )

        return ChatResponse(
            response=result.response_text,
            thread_id=request.thread_id,
            metadata={
                "company_id": request.company_id,
                "user_id": request.user_id,
                "ui_component": ui_component,
                **(result.metadata or {}),
            }
        )

    except Exception as e:
        logger.error(f"❌ Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing agent: {str(e)}"
        )


@router.post("/sii", response_model=ChatResponse)
async def chat_with_sii_context(request: ChatWithSIIRequest) -> ChatResponse:
    """
    Chat with AI agent using SII context.

    Specialized endpoint that accepts contribuyente info from the /verify endpoint
    and formats it as company context for the agent.

    This is the recommended way to chat with context from SII.

    Workflow:
    1. Call /api/sii/verify to get contribuyente_info
    2. Call this endpoint with the contribuyente_info
    3. Agent responds with SII context

    Example:
        ```python
        # Step 1: Verify SII credentials
        verify_response = requests.post("/api/sii/verify", json={
            "rut": "77794858",
            "dv": "k",
            "password": "******"
        })
        contribuyente_info = verify_response.json()["contribuyente_info"]

        # Step 2: Chat with SII context
        chat_response = requests.post("/api/chat/sii", json={
            "message": "¿Cuál es mi razón social?",
            "rut": "77794858-k",
            "contribuyente_info": contribuyente_info
        })

        print(chat_response.json()["response"])
        # "Tu razón social es EMPRESA DEMO SPA"
        ```
    """
    try:
        service = AgentService()
        result = await service.execute_with_sii_context(
            user_id=request.user_id,
            rut=request.rut,
            thread_id=request.thread_id,
            message=request.message,
            contribuyente_info=request.contribuyente_info,
            metadata=request.metadata,
        )

        return ChatResponse(
            response=result.response_text,
            thread_id=request.thread_id,
            metadata={
                "rut": request.rut,
                "user_id": request.user_id,
                **(result.metadata or {}),
            }
        )

    except Exception as e:
        logger.error(f"❌ Chat with SII context error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing agent with SII context: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for chat router.

    Returns:
        Status of the chat service
    """
    return {
        "status": "healthy",
        "service": "chat",
        "features": {
            "stateless": True,
            "database": False,
            "chatkit": False,
            "sii_integration": True,
        }
    }

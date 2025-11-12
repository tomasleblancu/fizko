"""ChatKit AI Agent endpoints."""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING

from chatkit.server import StreamingResult
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from starlette.responses import JSONResponse

from ...agents import create_chatkit_server
from app.integrations.chatkit import ChatKitServerAdapter
from ...agents.config.scopes import get_scope_for_plan
from ...agents.ui_tools import UIToolDispatcher
from ...agents.guardrails import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)
from ...config.database import AsyncSessionLocal
from ...core import get_optional_user
from ...dependencies import require_auth, get_subscription_or_none
from ...utils.ui_component_context import (
    extract_ui_component_context,
    format_ui_context_for_agent,
)

if TYPE_CHECKING:
    from ...db.models import Subscription

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["chatkit"],
    dependencies=[
        Depends(require_auth)
    ]
)

# Lazy initialization of ChatKit server (only when first requested)
_chatkit_server: ChatKitServerAdapter | None = None


def get_chatkit_server() -> ChatKitServerAdapter:
    """Get or initialize the ChatKit server instance."""
    global _chatkit_server
    if _chatkit_server is None:
        try:
            logger.info("🤖 Initializing ChatKit server (multi-agent mode)")

            _chatkit_server = create_chatkit_server()
            if _chatkit_server is None:
                raise ValueError("Failed to create ChatKit server")
        except Exception as e:
            logger.error(f"Failed to initialize ChatKit server: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "ChatKit dependencies are missing or failed to initialize. "
                    f"Error: {str(e)}"
                ),
            )
    return _chatkit_server


@router.post("/chatkit/upload/{attachment_id}")
async def chatkit_upload_attachment(
    attachment_id: str,
    request: Request,
    server: ChatKitServerAdapter = Depends(get_chatkit_server),
) -> Response:
    """
    ChatKit attachment upload endpoint (Phase 2 of two-phase upload).

    This endpoint receives the actual file content after ChatKit
    creates the attachment metadata in Phase 1.

    Phase 1: ChatKit client -> attachment tool -> memory attachment store
              (creates metadata, returns upload URL)
    Phase 2: ChatKit client -> this endpoint with multipart/form-data
              (stores file, updates metadata)

    Args:
        attachment_id: The attachment ID from Phase 1
        request: FastAPI request with multipart/form-data
        server: ChatKit server instance

    Returns:
        JSON response with success status
    """
    try:
        from ...agents.core.memory_attachment_store import store_attachment_content

        content_type = request.headers.get("content-type", "")

        # ChatKit sends files as multipart/form-data
        if "multipart/form-data" in content_type:
            # Parse multipart form data manually
            from starlette.datastructures import UploadFile as StarletteUploadFile

            # Get form data
            form = await request.form()

            # The file should be in the form data
            # Try common field names
            file = None
            for key in form.keys():
                value = form[key]
                if isinstance(value, StarletteUploadFile):
                    file = value
                    break

            if file is None:
                # If no UploadFile found, try to get the first value
                if len(form) > 0:
                    first_value = list(form.values())[0]
                    if isinstance(first_value, StarletteUploadFile):
                        file = first_value

            if file is None:
                raise ValueError("No file found in multipart/form-data")

            # Read the actual file bytes
            file_bytes = await file.read()

            logger.info(f"📎 Received multipart file upload for attachment {attachment_id}")
            logger.info(f"   File field name: {file.filename}")
            logger.info(f"   Content-Type: {file.content_type}")
            logger.info(f"   Size: {len(file_bytes)} bytes")
            logger.info(f"   First 20 bytes (hex): {file_bytes[:20].hex()}")

            # Store the actual file bytes
            store_attachment_content(attachment_id, file_bytes)

            return JSONResponse(
                {
                    "success": True,
                    "attachment_id": attachment_id,
                    "size": len(file_bytes),
                }
            )
        else:
            # Fallback: raw bytes (shouldn't happen with ChatKit)
            file_bytes = await request.body()

            logger.info(f"📎 Received raw file upload for attachment {attachment_id}")
            logger.info(f"   Size: {len(file_bytes)} bytes")

            store_attachment_content(attachment_id, file_bytes)

            return JSONResponse(
                {
                    "success": True,
                    "attachment_id": attachment_id,
                    "size": len(file_bytes),
                }
            )
    except Exception as e:
        logger.error(f"❌ Failed to handle file upload for {attachment_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            {"success": False, "error": str(e), "attachment_id": attachment_id},
            status_code=500,
        )


@router.post("/chatkit")
async def chatkit_endpoint(
    request: Request,
    agent_type: str = Query(
        "sii_general",
        description="Agent type to use: 'sii_general' (default) or 'remuneraciones'",
    ),
    company_id: str | None = Query(
        None, description="Company ID from frontend query params"
    ),
    ui_component: str | None = Query(
        None, description="UI component that triggered the message"
    ),
    entity_id: str | None = Query(
        None, description="Entity ID (contact, document, etc) for UI context"
    ),
    entity_type: str | None = Query(
        None, description="Entity type (contact, document, etc) for UI context"
    ),
    subscription: "Subscription | None" = Depends(get_subscription_or_none),
    server: ChatKitServerAdapter = Depends(get_chatkit_server),
) -> Response:
    """ChatKit conversational endpoint."""
    # 🕐 START: Log request start time
    request_start_time = time.time()

    # Determine agent scope based on subscription
    plan_code = subscription.plan.code if subscription else None
    agent_scope = get_scope_for_plan(plan_code)

    # Get optional user from JWT token
    user = await get_optional_user(request)
    user_id = user.get("sub") if user else "anonymous"

    # Priority: Query param > JWT token
    if not company_id:
        company_id = user.get("company_id") if user else None

    payload = await request.body()

    # Extract message from payload to use for UI context extraction
    user_message = ""
    operation = "unknown"
    try:
        payload_dict = json.loads(payload)
        operation = payload_dict.get("op", "unknown")
        # Try to extract message from payload
        if payload_dict.get("op") == "create_message" and "text" in payload_dict:
            user_message = payload_dict["text"]
    except:
        pass

    # NEW: Dispatch to UI Tools system if ui_component is present
    ui_tool_result = None
    ui_context_text = ""

    if ui_component and ui_component != "null":
        # Get database session for UI tool processing
        async with AsyncSessionLocal() as db:
            # Build additional_data dict from query params
            additional_data = {}
            if entity_id:
                additional_data["entity_id"] = entity_id
            if entity_type:
                additional_data["entity_type"] = entity_type

            ui_tool_result = await UIToolDispatcher.dispatch(
                ui_component=ui_component,
                user_message=user_message,
                company_id=company_id,
                user_id=user_id,
                db=db,
                additional_data=additional_data if additional_data else None,
            )

        if ui_tool_result and ui_tool_result.success:
            ui_context_text = ui_tool_result.context_text
        elif ui_tool_result and not ui_tool_result.success:
            logger.warning(f"⚠️ UI Tool failed: {ui_tool_result.error}")
            # Fallback to legacy system if UI tool fails
            ui_context = extract_ui_component_context(
                ui_component=ui_component,
                message=user_message,
                company_id=company_id,
            )
            ui_context_text = format_ui_context_for_agent(ui_context)
    else:
        # No ui_component, use legacy system as fallback
        ui_context = extract_ui_component_context(
            ui_component=ui_component,
            message=user_message,
            company_id=company_id,
        )
        ui_context_text = format_ui_context_for_agent(ui_context)

    context = {
        "request": request,
        "user_id": user_id,
        "user": user,
        "company_id": company_id,
        "ui_component": ui_component,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "ui_tool_result": ui_tool_result,
        "ui_context_text": ui_context_text,
        "agent_type": agent_type,
        "agent_scope": agent_scope,  # Pass scope to agent system
        "request_start_time": request_start_time,  # Pass timing to agent
    }

    # Single consolidated log
    user_id_short = user_id[:8] if user_id != "anonymous" else "anon"
    company_id_short = company_id[:8] if company_id else "none"
    logger.info(
        f"🚀 ChatKit | op={operation} | user={user_id_short} | "
        f"company={company_id_short} | scope={agent_scope} | ui_tool={ui_component or 'none'}"
    )

    # Process request through ChatKit server
    try:
        result = await server.process(payload, context)

        if isinstance(result, StreamingResult):
            # Wrap streaming result to catch guardrail exceptions during streaming
            async def stream_with_guardrail_handler():
                try:
                    async for chunk in result:
                        yield chunk
                except InputGuardrailTripwireTriggered as e:
                    # Input bloqueado por guardrail durante streaming
                    logger.warning(
                        f"🚨 Input guardrail triggered (during stream) | "
                        f"User: {user_id} | "
                        f"Company: {company_id} | "
                        f"Guardrail: {e.guardrail_name} | "
                        f"Reason: {e.result.output.output_info}"
                    )

                    # Determinar mensaje basado en el tipo de bloqueo
                    reason = e.result.output.output_info.get("reason", "").lower()

                    if "prompt injection" in reason:
                        message_text = (
                            "⚠️ Lo siento, detecté un intento de manipular mi comportamiento.\n\n"
                            "Estoy diseñado para ayudarte exclusivamente con temas tributarios y contables de Chile. "
                            "Por favor, hazme preguntas relacionadas con:\n"
                            "• Impuestos (IVA, F29, DTE)\n"
                            "• Contabilidad empresarial\n"
                            "• Remuneraciones y personal\n"
                            "• Documentos tributarios\n"
                            "• Obligaciones con el SII"
                        )
                    elif "off-topic" in reason:
                        message_text = (
                            "🤔 Tu pregunta parece estar fuera del alcance de Fizko.\n\n"
                            "Soy un asistente especializado en temas tributarios y contables de Chile. "
                            "Puedo ayudarte con:\n"
                            "• Cálculos de IVA y otros impuestos\n"
                            "• Llenado del formulario F29\n"
                            "• Gestión de documentos tributarios (facturas, boletas, guías)\n"
                            "• Remuneraciones y contratos laborales\n"
                            "• Obligaciones y plazos del SII\n"
                            "• Contabilidad empresarial\n\n"
                            "¿En qué tema tributario o contable puedo ayudarte hoy?"
                        )
                    else:
                        message_text = (
                            "Lo siento, no puedo procesar tu solicitud. "
                            "Por favor, reformula tu pregunta relacionada con temas tributarios y contables de Chile. "
                            "Estoy aquí para ayudarte con IVA, F29, documentos tributarios, remuneraciones y más."
                        )

                    # Enviar mensaje como evento SSE
                    error_event = {
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": message_text}]
                    }
                    yield f"data: {json.dumps(error_event)}\n\n"
                    yield "data: [DONE]\n\n"

            return StreamingResponse(stream_with_guardrail_handler(), media_type="text/event-stream")
        if hasattr(result, "json"):
            return Response(content=result.json, media_type="application/json")
        return JSONResponse(result)

    except InputGuardrailTripwireTriggered as e:
        # Input bloqueado por guardrail (ej: prompt injection, uso abusivo)
        logger.warning(
            f"🚨 Input guardrail triggered | "
            f"User: {user_id} | "
            f"Company: {company_id} | "
            f"Guardrail: {e.guardrail_name} | "
            f"Reason: {e.result.output.output_info}"
        )

        # Determinar mensaje basado en el tipo de bloqueo
        reason = e.result.output.output_info.get("reason", "").lower()

        if "prompt injection" in reason:
            # Mensaje para intentos de manipulación
            message_text = (
                "⚠️ Lo siento, detecté un intento de manipular mi comportamiento.\n\n"
                "Estoy diseñado para ayudarte exclusivamente con temas tributarios y contables de Chile. "
                "Por favor, hazme preguntas relacionadas con:\n"
                "• Impuestos (IVA, F29, DTE)\n"
                "• Contabilidad empresarial\n"
                "• Remuneraciones y personal\n"
                "• Documentos tributarios\n"
                "• Obligaciones con el SII"
            )
        elif "off-topic" in reason:
            # Mensaje para preguntas fuera de tema
            message_text = (
                "🤔 Tu pregunta parece estar fuera del alcance de Fizko.\n\n"
                "Soy un asistente especializado en temas tributarios y contables de Chile. "
                "Puedo ayudarte con:\n"
                "• Cálculos de IVA y otros impuestos\n"
                "• Llenado del formulario F29\n"
                "• Gestión de documentos tributarios (facturas, boletas, guías)\n"
                "• Remuneraciones y contratos laborales\n"
                "• Obligaciones y plazos del SII\n"
                "• Contabilidad empresarial\n\n"
                "¿En qué tema tributario o contable puedo ayudarte hoy?"
            )
        else:
            # Mensaje genérico para otros casos
            message_text = (
                "Lo siento, no puedo procesar tu solicitud. "
                "Por favor, reformula tu pregunta relacionada con temas tributarios y contables de Chile. "
                "Estoy aquí para ayudarte con IVA, F29, documentos tributarios, remuneraciones y más."
            )

        # Retornar mensaje amigable al usuario
        error_message = {
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": message_text
                }
            ]
        }
        return JSONResponse(error_message, status_code=200)  # 200 para que ChatKit lo muestre

    except OutputGuardrailTripwireTriggered as e:
        # Output bloqueado por guardrail (ej: PII detectado)
        logger.error(
            f"🚨 Output guardrail triggered | "
            f"User: {user_id} | "
            f"Company: {company_id} | "
            f"Guardrail: {e.guardrail_name} | "
            f"Reason: {e.result.output.output_info}"
        )

        # No mostrar el output bloqueado - devolver mensaje genérico
        error_message = {
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": (
                        "Lo siento, hubo un problema al procesar tu solicitud. "
                        "Por favor, intenta reformular tu pregunta o contacta con soporte si el problema persiste."
                    )
                }
            ]
        }
        return JSONResponse(error_message, status_code=200)

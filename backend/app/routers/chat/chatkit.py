"""ChatKit AI Agent endpoints."""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING

from chatkit.server import StreamingResult
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response, StreamingResponse
from starlette.responses import JSONResponse

from ...agents import FizkoServer, create_chatkit_server
from ...agents.ui_tools import UIToolDispatcher
from ...config.database import AsyncSessionLocal
from ...core import get_optional_user
from ...utils.ui_component_context import (
    extract_ui_component_context,
    format_ui_context_for_agent,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chatkit"])

# Lazy initialization of ChatKit server (only when first requested)
_chatkit_server: FizkoServer | None = None


def get_chatkit_server() -> FizkoServer:
    """Get or initialize the ChatKit server instance."""
    global _chatkit_server
    if _chatkit_server is None:
        try:
            # Get mode from environment variable (default: multi_agent)
            import os

            mode = os.getenv("CHATKIT_MODE", "multi_agent")
            logger.info(f"🤖 Initializing ChatKit server in '{mode}' mode")

            _chatkit_server = create_chatkit_server(mode=mode)
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
    server: FizkoServer = Depends(get_chatkit_server),
) -> Response:
    """
    ChatKit attachment upload endpoint (Phase 2 of two-phase upload).

    This endpoint receives the actual file content after ChatKit
    creates the attachment metadata in Phase 1.

    Phase 1: ChatKit client -> attachment tool -> memory attachment store
              (creates metadata, returns upload URL)
    Phase 2: ChatKit client -> this endpoint with file bytes
              (stores file, updates metadata)

    Args:
        attachment_id: The attachment ID from Phase 1
        request: FastAPI request with file bytes in body
        server: ChatKit server instance

    Returns:
        JSON response with success status
    """
    try:
        from ...agents.core.memory_attachment_store import handle_file_upload

        # Read raw bytes from request
        file_bytes = await request.body()
        logger.info(
            f"📎 Received file upload for attachment {attachment_id} ({len(file_bytes)} bytes)"
        )

        # Handle file upload
        result = await handle_file_upload(attachment_id, file_bytes)

        return JSONResponse(
            {
                "success": True,
                "attachment_id": attachment_id,
                "size": len(file_bytes),
                "file_path": result.get("file_path"),
            }
        )
    except Exception as e:
        logger.error(f"❌ Failed to handle file upload for {attachment_id}: {e}")
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
    server: FizkoServer = Depends(get_chatkit_server),
) -> Response:
    """ChatKit conversational endpoint."""
    # 🕐 START: Log request start time
    request_start_time = time.time()
    logger.info("=" * 80)
    logger.info(f"🚀 [REQUEST START] {request.method} {request.url.path}")

    # Get optional user from JWT token
    auth_start = time.time()
    user = await get_optional_user(request)
    user_id = user.get("sub") if user else "anonymous"
    logger.info(
        f"⏱️  [+{(time.time() - request_start_time):.3f}s] Auth validated ({(time.time() - auth_start):.3f}s)"
    )

    # Priority: Query param > JWT token
    if not company_id:
        company_id = user.get("company_id") if user else None

    payload_start = time.time()
    payload = await request.body()
    logger.info(
        f"⏱️  [+{(time.time() - request_start_time):.3f}s] Payload received ({len(payload)} bytes) ({(time.time() - payload_start):.3f}s)"
    )

    # Extract message from payload to use for UI context extraction
    parse_start = time.time()
    user_message = ""
    try:
        payload_dict = json.loads(payload)
        # Try to extract message from payload
        if payload_dict.get("op") == "create_message" and "text" in payload_dict:
            user_message = payload_dict["text"]
    except:
        pass
    logger.info(
        f"⏱️  [+{(time.time() - request_start_time):.3f}s] Payload parsed ({(time.time() - parse_start):.3f}s)"
    )

    # NEW: Dispatch to UI Tools system if ui_component is present
    ui_tool_result = None
    ui_context_text = ""

    if ui_component and ui_component != "null":
        ui_tool_start = time.time()
        logger.info(
            f"⏱️  [+{(time.time() - request_start_time):.3f}s] UI Tool dispatch started"
        )
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

        ui_tool_end = time.time()
        logger.info(
            f"⏱️  [+{(ui_tool_end - request_start_time):.3f}s] UI Tool completed ({(ui_tool_end - ui_tool_start):.3f}s)"
        )

        if ui_tool_result and ui_tool_result.success:
            ui_context_text = ui_tool_result.context_text
            logger.info(f"✅ UI Tool: {ui_component} ({len(ui_context_text)} chars)")
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

    context_prep_start = time.time()
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
        "request_start_time": request_start_time,  # Pass timing to agent
    }
    logger.info(
        f"⏱️  [+{(time.time() - request_start_time):.3f}s] Context prepared ({(time.time() - context_prep_start):.3f}s)"
    )

    # Process request through ChatKit server
    process_start = time.time()
    logger.info(
        f"⏱️  [+{(process_start - request_start_time):.3f}s] server.process() started"
    )
    result = await server.process(payload, context)
    logger.info(
        f"⏱️  [+{(time.time() - request_start_time):.3f}s] server.process() completed ({(time.time() - process_start):.3f}s)"
    )

    # Return streaming response (respond() is called during streaming)
    stream_response_start = time.time()
    logger.info(
        f"⏱️  [+{(stream_response_start - request_start_time):.3f}s] Creating StreamingResponse (respond() will be called during iteration)"
    )
    logger.info("=" * 80)

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)

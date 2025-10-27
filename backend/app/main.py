"""FastAPI entrypoint for Fizko tax/accounting platform."""

from __future__ import annotations

import logging
from typing import Any

from chatkit.server import StreamingResult
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from starlette.responses import JSONResponse

from .agents import FizkoServer, create_chatkit_server
from .config.database import AsyncSessionLocal
from .core import get_optional_user
from .routers import (
    admin_router,
    calendar,
    companies_router,
    contacts,
    conversations,
    form29,
    profile,
    purchase_documents,
    sales_documents,
    sessions,
    tax_documents,
    tax_summary,
    whatsapp,
)
from .routers.personnel import router as personnel_router
from .routers.sii import router as sii_router
from .utils.ui_component_context import extract_ui_component_context, format_ui_context_for_agent
from .agents.ui_tools import UIToolDispatcher

# Load environment variables from .env file
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fizko API",
    description="API for Fizko tax/accounting platform with AI assistance",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event():
    """Run startup tasks including database connection check."""
    from .config.database import check_db_connection

    logger.info("Running startup checks...")
    try:
        await check_db_connection()
        logger.info("All startup checks passed")
    except Exception as e:
        logger.error(f"Startup check failed: {e}")
        # Don't raise - let the app start but log the error
        # The actual endpoints will fail if DB is not accessible

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5171",  # Local development
        "http://127.0.0.1:5171",  # Local development
        "https://fizko-ai-mr.vercel.app",  # Production frontend
        "https://demo.fizko.ai",  # Demo frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy initialization of ChatKit server (only when first requested)
_chatkit_server: FizkoServer | None = None

# Include API routers
app.include_router(admin_router.router)
app.include_router(calendar.router)
app.include_router(companies_router.router)
app.include_router(contacts.router)
app.include_router(profile.router)
app.include_router(sessions.router)
app.include_router(purchase_documents.router)
app.include_router(sales_documents.router)
app.include_router(form29.router)
app.include_router(conversations.router)
app.include_router(tax_summary.router)
app.include_router(tax_documents.router)
app.include_router(sii_router)
app.include_router(whatsapp.router)
app.include_router(whatsapp.webhook_router)  # Webhook sin autenticación JWT
app.include_router(personnel_router)  # Personnel management (people & payroll)


def get_chatkit_server() -> FizkoServer:
    global _chatkit_server
    if _chatkit_server is None:
        try:
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


@app.post("/chatkit")
async def chatkit_endpoint(
    request: Request,
    agent_type: str = Query(
        "sii_general", description="Agent type to use: 'sii_general' (default) or 'remuneraciones'"
    ),
    company_id: str | None = Query(None, description="Company ID from frontend query params"),
    ui_component: str | None = Query(None, description="UI component that triggered the message"),
    entity_id: str | None = Query(None, description="Entity ID (contact, document, etc) for UI context"),
    entity_type: str | None = Query(None, description="Entity type (contact, document, etc) for UI context"),
    server: FizkoServer = Depends(get_chatkit_server),
) -> Response:
    """ChatKit conversational endpoint."""
    import time

    # 🕐 START: Log request start time
    request_start_time = time.time()
    logger.info("=" * 80)
    logger.info(f"🚀 [REQUEST START] {request.method} {request.url.path}")

    # Get optional user from JWT token
    auth_start = time.time()
    user = await get_optional_user(request)
    user_id = user.get("sub") if user else "anonymous"
    logger.info(f"⏱️  [+{(time.time() - request_start_time):.3f}s] Auth validated ({(time.time() - auth_start):.3f}s)")

    # Priority: Query param > JWT token
    if not company_id:
        company_id = user.get("company_id") if user else None

    payload_start = time.time()
    payload = await request.body()
    logger.info(f"⏱️  [+{(time.time() - request_start_time):.3f}s] Payload received ({len(payload)} bytes) ({(time.time() - payload_start):.3f}s)")

    # Log request
    import json

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
    logger.info(f"⏱️  [+{(time.time() - request_start_time):.3f}s] Payload parsed ({(time.time() - parse_start):.3f}s)")

    # NEW: Dispatch to UI Tools system if ui_component is present
    ui_tool_result = None
    ui_context_text = ""

    if ui_component and ui_component != "null":
        ui_tool_start = time.time()
        logger.info(f"⏱️  [+{(time.time() - request_start_time):.3f}s] UI Tool dispatch started")
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
        logger.info(f"⏱️  [+{(ui_tool_end - request_start_time):.3f}s] UI Tool completed ({(ui_tool_end - ui_tool_start):.3f}s)")

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
        "ui_tool_result": ui_tool_result,
        "ui_context_text": ui_context_text,
        "agent_type": agent_type,
        "request_start_time": request_start_time,  # Pass timing to agent
    }
    logger.info(f"⏱️  [+{(time.time() - request_start_time):.3f}s] Context prepared ({(time.time() - context_prep_start):.3f}s)")

    # Process request through ChatKit server
    process_start = time.time()
    logger.info(f"⏱️  [+{(process_start - request_start_time):.3f}s] server.process() started")
    result = await server.process(payload, context)
    logger.info(f"⏱️  [+{(time.time() - request_start_time):.3f}s] server.process() completed ({(time.time() - process_start):.3f}s)")

    # Return streaming response (respond() is called during streaming)
    stream_response_start = time.time()
    logger.info(f"⏱️  [+{(stream_response_start - request_start_time):.3f}s] Creating StreamingResponse (respond() will be called during iteration)")
    logger.info("=" * 80)

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "fizko-backend"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Fizko Tax/Accounting Platform API",
        "version": "1.0.0",
        "docs": "/docs",
    }

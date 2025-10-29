"""FastAPI entrypoint for Fizko tax/accounting platform."""

from __future__ import annotations

import logging
from typing import Any

from chatkit.server import StreamingResult
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import HttpUrl
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
from .routers.admin import notifications as admin_notifications
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
    redirect_slashes=False,  # Prevent 307 redirects for trailing slashes
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

# Add CORS middleware with flexible origin checking
from fastapi.middleware.cors import CORSMiddleware

def is_allowed_origin(origin: str) -> bool:
    """Check if origin is allowed for CORS."""
    allowed = [
        "http://localhost:5171",
        "http://127.0.0.1:5171",
        "https://fizko-ai-mr.vercel.app",
        "https://demo.fizko.ai",
    ]

    # Allow any Vercel preview/production domain
    if origin and (".vercel.app" in origin or "fizko.ai" in origin):
        return True

    return origin in allowed

# Custom CORS middleware that checks origins dynamically
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*fizko\.ai|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy initialization of ChatKit server (only when first requested)
_chatkit_server: FizkoServer | None = None

# Include API routers
app.include_router(admin_router.router)
app.include_router(calendar.router)
app.include_router(admin_notifications.router)  # Admin notification templates
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


@app.post("/chatkit/upload/{attachment_id}")
async def chatkit_upload_attachment(
    attachment_id: str,
    request: Request,
    server: FizkoServer = Depends(get_chatkit_server),
) -> Response:
    """
    ChatKit attachment upload endpoint (Phase 2 of two-phase upload).

    This endpoint receives the actual file content after ChatKit
    creates the attachment metadata in Phase 1.

    The file is uploaded to Supabase Storage for persistence.
    """
    from fastapi import UploadFile, File, Form
    from .agents.core import store_attachment_content
    from .services.storage.attachment_storage import get_attachment_storage

    # Get metadata from MemoryAttachmentStore (created in Phase 1)
    # This contains the correct mime_type and filename
    metadata = server.attachment_store.get_attachment_metadata(attachment_id)

    if metadata is None:
        logger.error(f"❌ Attachment metadata not found for {attachment_id}")
        return JSONResponse(
            {
                "success": False,
                "error": "Attachment metadata not found. Please try again.",
                "attachment_id": attachment_id
            },
            status_code=404
        )

    mime_type = metadata.get("mime_type", "application/octet-stream")
    filename = metadata.get("name")

    logger.info(f"📤 Upload request for: {attachment_id} (expected: {mime_type}, {filename})")
    logger.info(f"📋 Headers: Content-Type={request.headers.get('content-type')}")

    # Check if it's multipart/form-data
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        # Parse multipart form data
        try:
            from starlette.datastructures import UploadFile as StarletteUploadFile

            form = await request.form()
            logger.info(f"📦 Form fields: {list(form.keys())}")

            # Try to find the file in the form
            file_content = None
            for key, value in form.items():
                logger.info(f"  - {key}: {type(value)}")
                if isinstance(value, StarletteUploadFile):
                    file_content = await value.read()
                    logger.info(f"✅ Found file in form field '{key}': {len(file_content)} bytes")
                    break

            if file_content is None:
                # Fallback: read raw body
                logger.warning("⚠️ No file found in form, reading raw body")
                file_content = await request.body()
        except Exception as e:
            logger.error(f"❌ Error parsing multipart: {e}", exc_info=True)
            file_content = await request.body()
    else:
        # Read raw file bytes from request body
        file_content = await request.body()

    logger.info(f"📤 Uploading attachment: {attachment_id} ({len(file_content)} bytes, {mime_type}, {filename})")

    # Store in memory first (for backward compatibility with MemoryAttachmentStore)
    store_attachment_content(attachment_id, file_content)

    # Upload to Supabase Storage
    try:
        storage = get_attachment_storage()
        success, url, error = storage.upload_attachment(
            attachment_id=attachment_id,
            content=file_content,
            mime_type=mime_type,
            filename=filename
        )

        if not success:
            logger.error(f"❌ Failed to upload to Supabase: {error}")
            return JSONResponse(
                {
                    "success": False,
                    "error": error,
                    "attachment_id": attachment_id
                },
                status_code=500
            )

        logger.info(f"✅ Attachment uploaded to Supabase: {url}")

        # For PDFs: Also upload to OpenAI Files API and create Vector Store
        openai_file_id = None
        vector_store_id = None

        if mime_type == "application/pdf":
            from .services.openai_files import get_openai_files_service

            logger.info(f"📄 PDF detected, uploading to OpenAI Files API for file_search")
            openai_service = get_openai_files_service()

            # Upload to OpenAI Files API
            success_openai, openai_file_id, error_openai = openai_service.upload_file_for_file_search(
                file_content=file_content,
                filename=filename,
                mime_type=mime_type
            )

            if success_openai and openai_file_id:
                logger.info(f"✅ PDF uploaded to OpenAI: {openai_file_id}")

                # Create Vector Store for this file
                success_vs, vector_store_id, error_vs = openai_service.create_vector_store_with_file(
                    file_id=openai_file_id,
                    store_name=f"{filename}"
                )

                if success_vs and vector_store_id:
                    logger.info(f"✅ Vector Store created: {vector_store_id}")
                    # Store OpenAI metadata in memory attachment store
                    server.attachment_store.set_openai_metadata(
                        attachment_id=attachment_id,
                        file_id=openai_file_id,
                        vector_store_id=vector_store_id
                    )

                    # IMPORTANT: Also persist to database via SupabaseStore
                    # We need to get the attachment and re-save it with OpenAI metadata
                    attachment_for_db = await server.attachment_store.get_attachment(attachment_id)
                    if attachment_for_db:
                        context_with_openai = {
                            "thread_id": None,  # Will be set when message is sent
                            "openai_file_id": openai_file_id,
                            "openai_vector_store_id": vector_store_id
                        }
                        await server.attachment_store.store.save_attachment(
                            attachment_for_db,
                            context_with_openai
                        )
                        logger.info(f"💾 Persisted OpenAI metadata to database for {attachment_id}")
                else:
                    logger.warning(f"⚠️ Failed to create Vector Store: {error_vs}")
            else:
                logger.warning(f"⚠️ Failed to upload PDF to OpenAI: {error_openai}")
                # Don't fail the whole upload - PDF is still in Supabase

        # CRITICAL: Get the full attachment object and update preview_url
        # ChatKit needs the complete attachment object to display the image correctly
        attachment = await server.attachment_store.get_attachment(attachment_id)

        if not attachment:
            logger.error(f"❌ Attachment not found after upload: {attachment_id}")
            return JSONResponse(
                {
                    "success": False,
                    "error": "Attachment not found after upload",
                    "attachment_id": attachment_id
                },
                status_code=404
            )

        # Update preview_url with the Supabase public URL for images
        if mime_type.startswith("image/"):
            # Convert string URL to HttpUrl (Pydantic type) to avoid serialization warnings
            attachment.preview_url = HttpUrl(url)
            # Update in memory store
            server.attachment_store._attachments[attachment_id] = attachment
            logger.info(f"✅ Updated preview_url with Supabase public URL: {url}")

        # CRITICAL: ChatKit expects the response in this exact format
        # Must be nested inside a "file" object with these specific fields
        response = {
            "file": {
                "id": attachment_id,
                "name": filename,
                "content_type": mime_type,
                "url": url
            }
        }

        logger.info(f"📤 Returning ChatKit-formatted response with url: {url}")
        return JSONResponse(response)

    except Exception as e:
        logger.error(f"❌ Error uploading attachment: {e}", exc_info=True)
        return JSONResponse(
            {
                "success": False,
                "error": str(e),
                "attachment_id": attachment_id
            },
            status_code=500
        )


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

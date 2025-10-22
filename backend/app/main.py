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
from .core import get_optional_user
from .routers import (
    admin,
    companies,
    conversations,
    form29,
    profile,
    purchase_documents,
    sales_documents,
    sessions,
    tax_documents,
    tax_summary,
)
from .routers.sii import router as sii_router

# Load environment variables from .env file
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fizko API",
    description="API for Fizko tax/accounting platform with AI assistance",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_chatkit_server: FizkoServer | None = create_chatkit_server()

# Include API routers
app.include_router(admin.router)
app.include_router(companies.router)
app.include_router(profile.router)
app.include_router(sessions.router)
app.include_router(purchase_documents.router)
app.include_router(sales_documents.router)
app.include_router(form29.router)
app.include_router(conversations.router)
app.include_router(tax_summary.router)
app.include_router(tax_documents.router)
app.include_router(sii_router)


def get_chatkit_server() -> FizkoServer:
    if _chatkit_server is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ChatKit dependencies are missing. Install the ChatKit Python "
                "package to enable the conversational endpoint."
            ),
        )
    return _chatkit_server


@app.post("/chatkit")
async def chatkit_endpoint(
    request: Request,
    agent_type: str = Query(
        "sii_general", description="Agent type to use: 'sii_general' (default) or 'remuneraciones'"
    ),
    server: FizkoServer = Depends(get_chatkit_server),
) -> Response:
    """ChatKit conversational endpoint."""
    # Get optional user from JWT token
    user = await get_optional_user(request)
    user_id = user.get("sub") if user else "anonymous"

    payload = await request.body()

    # Log request
    import json

    try:
        payload_dict = json.loads(payload)
        logger.info(f"ChatKit request op: {payload_dict.get('op')}")
    except:
        pass

    context = {
        "request": request,
        "user_id": user_id,
        "user": user,
        "agent_type": agent_type,
    }
    result = await server.process(payload, context)
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

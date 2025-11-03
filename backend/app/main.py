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

from .routers import (
    admin_router,
    calendar,
    chatkit,
    companies_router,
    company_settings,
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
from .routers.admin import template_variables as admin_template_variables
from .routers.personnel import router as personnel_router
from .routers.scheduled_tasks import router as scheduled_tasks_router
from .routers.sii import router as sii_router
from .routers.tasks import router as tasks_router
from .routers.user import router as user_router

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
    allow_origin_regex=r"^(https://.*\.vercel\.app|https://.*\.fizko\.ai|http://localhost:\d+|http://127\.0\.0\.1:\d+)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(admin_router.router)
app.include_router(calendar.router)
app.include_router(admin_notifications.router)  # Admin notification templates
app.include_router(admin_template_variables.router, prefix="/api")  # Template variables metadata
app.include_router(chatkit.router)  # ChatKit AI agent endpoints
app.include_router(companies_router.router)
app.include_router(company_settings.router)  # Company settings configuration
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
app.include_router(tasks_router)  # Celery task management
app.include_router(scheduled_tasks_router, prefix="/api")  # Celery Beat scheduled tasks
app.include_router(user_router)  # User-specific operations (notification preferences)


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

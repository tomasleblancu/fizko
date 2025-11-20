"""
Main WhatsApp router - aggregates all WhatsApp routes.

Two separate routers:
1. router - Authenticated endpoints (JWT required)
2. webhook_router - Webhook endpoint (HMAC validation)
"""

from fastapi import APIRouter

from .routes import messaging, webhooks

# Authenticated router (JWT required - applied at route level)
router = APIRouter(
    prefix="/api/whatsapp",
    tags=["whatsapp"],
)

# Webhook router (no JWT - uses HMAC validation)
webhook_router = APIRouter(
    prefix="/api/whatsapp",
    tags=["whatsapp-webhooks"],
)

# Include sub-routers
router.include_router(messaging.router)
webhook_router.include_router(webhooks.router)

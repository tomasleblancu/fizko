"""
Router de WhatsApp - Gestión de mensajería vía Kapso

Este módulo agrega todos los sub-routers en una estructura modular:
- Mensajería (envío de mensajes)
- Conversaciones
- Contactos y búsqueda
- Templates e inbox
- Webhooks (procesamiento de eventos)
"""
from fastapi import APIRouter, Depends

from app.dependencies import require_auth

# Importar todos los sub-routers
from .routes import (
    messaging,
    conversations,
    contacts,
    misc,
    webhooks,
)

# Router principal con autenticación JWT
router = APIRouter(
    prefix="/api/whatsapp",
    tags=["whatsapp"],
    dependencies=[Depends(require_auth)]
)

# Router separado para webhooks (sin autenticación JWT - usa firma HMAC)
webhook_router = APIRouter(
    prefix="/api/whatsapp",
    tags=["whatsapp-webhooks"],
)

# =============================================================================
# Agregar sub-routers
# =============================================================================

# Endpoints autenticados
router.include_router(messaging.router)
router.include_router(conversations.router)
router.include_router(contacts.router)
router.include_router(misc.router)

# Endpoints de webhooks (sin autenticación JWT)
webhook_router.include_router(webhooks.router)

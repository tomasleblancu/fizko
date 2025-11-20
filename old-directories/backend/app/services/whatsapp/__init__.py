"""
Servicios de WhatsApp
"""
import os
from typing import Optional

from .service import WhatsAppService
from .auth import (
    authenticate_user_by_whatsapp,
    get_user_info_by_whatsapp,
    update_phone_verification,
)
from .conversation_manager import WhatsAppConversationManager
from .agent_runner import WhatsAppAgentRunner
from .media_processor import WhatsAppMediaProcessor, get_media_processor

__all__ = [
    "WhatsAppService",
    "authenticate_user_by_whatsapp",
    "get_user_info_by_whatsapp",
    "update_phone_verification",
    "WhatsAppConversationManager",
    "WhatsAppAgentRunner",
    "WhatsAppMediaProcessor",
    "get_media_processor",
    "get_whatsapp_service",
]

# Global WhatsApp service instance
_whatsapp_service: Optional[WhatsAppService] = None


def get_whatsapp_service() -> Optional[WhatsAppService]:
    """
    Get the global WhatsApp service instance.
    Returns None if KAPSO_API_TOKEN is not configured.
    """
    global _whatsapp_service

    if _whatsapp_service is None:
        api_token = os.getenv("KAPSO_API_TOKEN")
        if api_token:
            _whatsapp_service = WhatsAppService(api_token=api_token)

    return _whatsapp_service

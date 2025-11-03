"""
Base service for notification operations
Provides common dependencies and utilities for all notification modules
"""
import logging
from typing import Optional

from app.services.whatsapp.service import WhatsAppService

logger = logging.getLogger(__name__)


class BaseNotificationService:
    """
    Base service providing common dependencies and utilities
    for all notification service modules
    """

    def __init__(self, whatsapp_service: WhatsAppService):
        """
        Initialize base notification service.

        Args:
            whatsapp_service: WhatsApp service instance for sending messages
        """
        self.whatsapp_service = whatsapp_service
        self.logger = logger

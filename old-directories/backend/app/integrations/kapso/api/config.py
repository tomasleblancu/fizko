"""
Config API - WhatsApp configuration management.
"""
import logging
from typing import Dict, Optional, Any

from .base import BaseAPI

logger = logging.getLogger(__name__)


class ConfigAPI(BaseAPI):
    """API for WhatsApp configuration operations."""

    async def list(
        self,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List WhatsApp configurations.

        Args:
            customer_id: Filter by customer

        Returns:
            List of configurations
        """
        params = {}
        if customer_id:
            params["customer_id"] = customer_id

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/configs_overview",
            params=params,
        )

        return result

    async def get_inbox(
        self,
        whatsapp_config_id: str,
        limit: int = 20,
        page: int = 1,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get inbox for a configuration.

        Args:
            whatsapp_config_id: Configuration ID
            limit: Results limit
            page: Page number
            status: Filter by status (active/ended)

        Returns:
            Inbox conversations
        """
        params = {
            "whatsapp_config_id": whatsapp_config_id,
            "limit": limit,
            "page": page,
        }

        if status:
            params["status"] = status

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/inbox",
            params=params,
        )

        return result

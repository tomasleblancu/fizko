"""Templates API - manage WhatsApp templates."""

import logging
from typing import Any, Optional

from .base import BaseAPI

logger = logging.getLogger(__name__)


class TemplatesAPI(BaseAPI):
    """API for WhatsApp template operations."""

    async def list(
        self,
        whatsapp_config_id: Optional[str] = None,
        category: Optional[str] = None,
        language_code: Optional[str] = None,
        limit: int = 50,
        page: int = 1,
    ) -> dict[str, Any]:
        """
        List approved WhatsApp templates.

        Args:
            whatsapp_config_id: Optional filter by WhatsApp config
            category: Optional filter by category (MARKETING, UTILITY, AUTHENTICATION)
            language_code: Optional filter by language (e.g., es_CL)
            limit: Max results per page
            page: Page number

        Returns:
            Paginated list of templates
        """
        params: dict[str, Any] = {"limit": limit, "page": page}

        if whatsapp_config_id:
            params["whatsapp_config_id"] = whatsapp_config_id
        if category:
            params["category"] = category
        if language_code:
            params["language_code"] = language_code

        return await self._make_request(
            method="GET",
            endpoint="whatsapp_templates",
            params=params,
        )

    async def get(
        self,
        template_name: str,
        language_code: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get details for a specific template.

        Args:
            template_name: Template name
            language_code: Optional language code if multiple languages exist

        Returns:
            Template details with parameter schema
        """
        params: dict[str, Any] = {"name": template_name}

        if language_code:
            params["language_code"] = language_code

        return await self._make_request(
            method="GET",
            endpoint="whatsapp_templates/by_name",
            params=params,
        )

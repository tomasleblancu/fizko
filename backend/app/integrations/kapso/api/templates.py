"""Templates API - manage WhatsApp templates."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from .base import BaseAPI
from ..exceptions import KapsoAPIError

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
    ) -> Dict[str, Any]:
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
        params: Dict[str, Any] = {"limit": limit, "page": page}

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
    ) -> Dict[str, Any]:
        """
        Get details for a specific template.

        Args:
            template_name: Template name
            language_code: Optional language code if multiple languages exist

        Returns:
            Template details with parameter schema
        """
        params: Dict[str, Any] = {"name": template_name}

        if language_code:
            params["language_code"] = language_code

        return await self._make_request(
            method="GET",
            endpoint="whatsapp_templates/by_name",
            params=params,
        )

    async def send_with_params(
        self,
        phone_number: str,
        template_name: str,
        phone_number_id: str,
        template_params: Dict[str, str],
        template_language: str = "en",
    ) -> Dict[str, Any]:
        """
        Send a template using Meta API with named parameters.

        Args:
            phone_number: Destination phone (E.164 format, with or without +)
            template_name: Approved template name
            phone_number_id: WhatsApp Business Phone Number ID
            template_params: Named parameters as dict (e.g., {"codigo": "123456"})
            template_language: Language code (e.g., "en", "es", "es_CL")

        Returns:
            Meta API response with message ID

        Raises:
            KapsoAPIError: If sending fails

        Example:
            >>> result = await api.send_with_params(
            ...     phone_number="+56912345678",
            ...     template_name="wp_verification",
            ...     phone_number_id="815755844962703",
            ...     template_params={"codigo": "123456"},
            ...     template_language="en"
            ... )
        """
        # Normalize phone number (remove + if present)
        normalized_phone = phone_number.lstrip('+')

        # Build parameters with parameter_name field for named params
        parameters = [
            {
                "type": "text",
                "parameter_name": param_name,
                "text": param_value
            }
            for param_name, param_value in template_params.items()
        ]

        # Build payload for Meta API
        payload = {
            "messaging_product": "whatsapp",
            "to": normalized_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": template_language
                },
                "components": [{
                    "type": "body",
                    "parameters": parameters
                }]
            }
        }

        # Use Meta API endpoint directly through Kapso
        meta_url = f"https://api.kapso.ai/meta/whatsapp/v21.0/{phone_number_id}/messages"

        logger.info(f"📤 Sending WhatsApp template via Meta API:")
        logger.info(f"  - Template: {template_name}")
        logger.info(f"  - To: {normalized_phone}")
        logger.info(f"  - Language: {template_language}")
        logger.info(f"  - Params: {template_params}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    meta_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60,
                )

                logger.info(f"📬 Template response. Status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Template '{template_name}' sent to {normalized_phone}")
                    return result
                else:
                    error_text = response.text
                    logger.error(f"❌ Error sending template: {response.status_code} - {error_text}")
                    raise KapsoAPIError(
                        f"Error {response.status_code}: {error_text}",
                        status_code=response.status_code
                    )

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error sending template: {e}")
            raise KapsoAPIError(f"HTTP error: {str(e)}")
        except KapsoAPIError:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error sending template: {e}")
            raise KapsoAPIError(f"Unexpected error: {str(e)}")

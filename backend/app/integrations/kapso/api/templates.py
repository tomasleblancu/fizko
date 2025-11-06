"""
Templates API - WhatsApp template operations.
"""
import logging
from typing import Dict, List, Optional, Any
import httpx

from .base import BaseAPI
from ..exceptions import KapsoAPIError, KapsoNotFoundError, KapsoValidationError

logger = logging.getLogger(__name__)


class TemplatesAPI(BaseAPI):
    """API for WhatsApp template operations."""

    async def list(
        self,
        whatsapp_config_id: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        List available templates.

        Args:
            whatsapp_config_id: Filter by configuration
            limit: Results limit
            page: Page number

        Returns:
            List of templates
        """
        params = {
            "limit": limit,
            "page": page,
        }

        if whatsapp_config_id:
            params["whatsapp_config_id"] = whatsapp_config_id

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/templates",
            params=params,
        )

        return result

    async def get_structure(
        self,
        template_name: str,
        business_account_id: str,
    ) -> Dict[str, Any]:
        """
        Get WhatsApp template structure from Meta API.

        Extracts named_parameters from template and builds the structure
        needed by the notification system (header_params, body_params).

        Args:
            template_name: Template name in Meta (e.g., daily_business_summary)
            business_account_id: WhatsApp Business Account ID

        Returns:
            Dict with:
            - template_name: Template name
            - whatsapp_template_structure: {header_params: [...], body_params: [...]}
            - named_parameters: Full list of parameters with metadata

        Raises:
            KapsoNotFoundError: If template doesn't exist
            KapsoAPIError: If API error occurs

        Example:
            >>> api = TemplatesAPI(api_token="...", base_url="...")
            >>> structure = await api.get_structure(
            ...     template_name="daily_business_summary",
            ...     business_account_id="123456789"
            ... )
            >>> print(structure["whatsapp_template_structure"])
            {
                "header_params": ["day_name"],
                "body_params": ["sales_count", "sales_total_ft", ...]
            }
        """
        # Use Meta API endpoint through Kapso
        meta_url = f"https://api.kapso.ai/meta/whatsapp/v23.0/{business_account_id}/message_templates"

        logger.info(f"📤 Fetching template structure from Meta API")
        logger.info(f"  - Template name: {template_name}")
        logger.info(f"  - WABA ID: {business_account_id}")
        logger.info(f"  - URL: {meta_url}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    meta_url,
                    headers=self.headers,
                    params={"name": template_name},
                    timeout=30.0
                )

                logger.info(f"📬 Response status: {response.status_code}")

                if response.status_code != 200:
                    logger.error(f"❌ Error response: {response.text}")
                    raise KapsoAPIError(
                        f"Failed to fetch template from Meta API: {response.text}",
                        status_code=response.status_code,
                        response_data=response.text
                    )

                data = response.json()
                templates = data.get("data", [])

                if not templates:
                    raise KapsoNotFoundError(
                        f"Template '{template_name}' not found in Meta API",
                        status_code=404,
                        response_data=str(data)
                    )

                # Get first matching template
                meta_template = templates[0]
                logger.info(f"✅ Template found: {meta_template.get('name')}")

                # Extract named parameters from components
                named_params = []
                header_params = []
                body_params = []

                components = meta_template.get("components", [])
                for component in components:
                    component_type = component.get("type", "").lower()

                    # Extract parameters from example
                    if "example" in component:
                        example = component["example"]

                        # Named parameters (newer format)
                        if "header_text_named_params" in example:
                            for param in example["header_text_named_params"]:
                                param_name = param.get("param_name")
                                if param_name:
                                    header_params.append(param_name)
                                    named_params.append({
                                        "name": param_name,
                                        "location": "header",
                                        "example": param.get("example")
                                    })

                        if "body_text_named_params" in example:
                            for param in example["body_text_named_params"]:
                                param_name = param.get("param_name")
                                if param_name:
                                    body_params.append(param_name)
                                    named_params.append({
                                        "name": param_name,
                                        "location": "body",
                                        "example": param.get("example")
                                    })

                if not named_params:
                    logger.warning(f"⚠️  Template '{template_name}' has no named_parameters")

                template_structure = {
                    "header_params": header_params,
                    "body_params": body_params
                }

                logger.info(f"✅ Template structure extracted:")
                logger.info(f"  - Header params: {header_params}")
                logger.info(f"  - Body params: {body_params}")

                return {
                    "template_name": template_name,
                    "whatsapp_template_structure": template_structure,
                    "named_parameters": named_params
                }

        except (KapsoAPIError, KapsoNotFoundError):
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching template structure: {e}")
            raise KapsoAPIError(f"Unexpected error: {str(e)}")

    async def create(
        self,
        waba_id: str,
        name: str,
        category: str,
        language: str,
        components: List[Dict],
    ) -> Dict[str, Any]:
        """
        Create a WhatsApp Business template in Meta via Kapso.

        Args:
            waba_id: WhatsApp Business Account ID
            name: Template name (lowercase, underscores)
            category: UTILITY, MARKETING, or AUTHENTICATION
            language: Language code (es, en_US, etc.)
            components: List of components (HEADER, BODY, FOOTER, BUTTONS)

        Returns:
            Meta response with created template

        Raises:
            KapsoValidationError: If template is invalid or already exists
            KapsoAPIError: If API error occurs

        Example:
            >>> result = await api.create(
            ...     waba_id="1890372408497828",
            ...     name="order_confirmation",
            ...     category="UTILITY",
            ...     language="es",
            ...     components=[{
            ...         "type": "BODY",
            ...         "text": "Hola {{customer_name}}, tu pedido {{order_number}} fue confirmado!",
            ...         "example": {
            ...             "body_text_named_params": [
            ...                 {"param_name": "customer_name", "example": "Juan"},
            ...                 {"param_name": "order_number", "example": "12345"}
            ...             ]
            ...         }
            ...     }]
            ... )
        """
        payload = {
            "name": name,
            "category": category,
            "language": language,
            "components": components,
        }

        logger.info(f"📤 Creating WhatsApp template:")
        logger.info(f"  - WABA ID: {waba_id}")
        logger.info(f"  - Template name: {name}")
        logger.info(f"  - Category: {category}")
        logger.info(f"  - Language: {language}")

        try:
            # Meta API uses different base URL
            meta_url = f"https://api.kapso.ai/meta/whatsapp/v21.0/{waba_id}/message_templates"

            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method="POST",
                    url=meta_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60,
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                elif response.status_code == 404:
                    raise KapsoNotFoundError(
                        "Recurso no encontrado",
                        status_code=response.status_code,
                        response_data=response.text,
                    )
                elif response.status_code == 422:
                    raise KapsoValidationError(
                        f"Error de validación: {response.text[:200]}",
                        status_code=response.status_code,
                        response_data=response.text,
                    )
                else:
                    raise KapsoAPIError(
                        f"Error {response.status_code}: {response.text[:200]}",
                        status_code=response.status_code,
                        response_data=response.text,
                    )

            logger.info(f"✅ WhatsApp template '{name}' created successfully")
            return result

        except KapsoValidationError as e:
            logger.error(f"❌ Validation error creating template '{name}': {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error creating template '{name}': {e}")
            raise

    async def send(
        self,
        phone_number_id: str,
        to: str,
        template_name: str,
        language_code: str = "es",
        header_params: Optional[List[Dict[str, str]]] = None,
        body_params: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Send a message using an existing WhatsApp template.

        Args:
            phone_number_id: WhatsApp Business Phone Number ID
            to: Destination phone number (international format, e.g., "56912345678")
            template_name: Template name (must be approved in Meta)
            language_code: Language code (default: "es")
            header_params: Header parameters (if template has variables)
            body_params: Body parameters (if template has variables)

        Returns:
            Meta response with sent message

        Raises:
            KapsoAPIError: If sending fails

        Example:
            >>> result = await api.send(
            ...     phone_number_id="647015955153740",
            ...     to="56912345678",
            ...     template_name="daily_business_summary_v2",
            ...     language_code="es",
            ...     header_params=[{"type": "text", "text": "Lunes"}],
            ...     body_params=[
            ...         {"type": "text", "text": "5"},
            ...         {"type": "text", "text": "$1,500,000"},
            ...     ]
            ... )
        """
        # Build components array
        components = []

        # Add header component if params provided
        if header_params:
            components.append({
                "type": "header",
                "parameters": header_params
            })

        # Add body component if params provided
        if body_params:
            components.append({
                "type": "body",
                "parameters": body_params
            })

        # Build payload
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }

        # Add components only if we have any
        if components:
            payload["template"]["components"] = components

        # Use Meta API endpoint for sending messages
        meta_url = f"https://api.kapso.ai/meta/whatsapp/v21.0/{phone_number_id}/messages"

        logger.info(f"📤 Sending WhatsApp template message:")
        logger.info(f"  - Phone Number ID: {phone_number_id}")
        logger.info(f"  - To: {to}")
        logger.info(f"  - Template: {template_name}")
        logger.info(f"  - Language: {language_code}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method="POST",
                    url=meta_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60,
                )

                logger.info(f"📬 Template sent. Status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Message ID: {result.get('messages', [{}])[0].get('id', 'N/A')}")
                    return result
                else:
                    error_text = response.text
                    logger.error(f"❌ Error sending template: {response.status_code} - {error_text}")
                    raise KapsoAPIError(f"Error {response.status_code}: {error_text}")

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error sending template: {e}")
            raise KapsoAPIError(f"HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error sending template: {e}")
            raise

    async def send_with_components(
        self,
        phone_number: str,
        template_name: str,
        phone_number_id: str,
        components: Optional[List[Dict[str, Any]]] = None,
        template_language: str = "es_CL",
    ) -> Dict[str, Any]:
        """
        Send a template using Meta API with pre-built components.

        This is used by the notification system which builds components
        from template structure and message context.

        Args:
            phone_number: Destination phone (without +)
            template_name: Approved template name
            phone_number_id: WhatsApp Business Phone Number ID
            components: Pre-built Meta API components
            template_language: Language code

        Returns:
            Meta API response
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": template_language
                }
            }
        }

        if components:
            payload["template"]["components"] = components

        # Use Meta API endpoint directly
        meta_url = f"https://api.kapso.ai/meta/whatsapp/v21.0/{phone_number_id}/messages"

        logger.info(f"📤 Sending Meta API template request to {meta_url}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method="POST",
                    url=meta_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60,
                )

                logger.info(f"📬 Template response. Status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Template '{template_name}' sent to {phone_number}")
                    return result
                else:
                    error_text = response.text
                    logger.error(f"❌ Error sending template: {response.status_code} - {error_text}")
                    raise KapsoAPIError(f"Error {response.status_code}: {error_text}")

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error sending template: {e}")
            raise KapsoAPIError(f"HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error sending template: {e}")
            raise

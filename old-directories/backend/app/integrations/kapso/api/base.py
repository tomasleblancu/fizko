"""
Base API client with common HTTP logic.
"""
import logging
from typing import Dict, Optional, Any
import httpx

from ..exceptions import (
    KapsoAPIError,
    KapsoAuthenticationError,
    KapsoValidationError,
    KapsoTimeoutError,
    KapsoNotFoundError,
)

logger = logging.getLogger(__name__)


class BaseAPI:
    """
    Base class for all Kapso API modules.
    Provides common HTTP request handling.
    """

    def __init__(self, api_token: str, base_url: str, timeout: int = 30):
        """
        Initialize base API client.

        Args:
            api_token: Kapso API token
            base_url: Base URL for API requests
            timeout: Default timeout in seconds
        """
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "X-API-Key": api_token,
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Kapso API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base_url)
            data: JSON data for request body
            params: Query parameters
            timeout: Custom timeout

        Returns:
            Response as dict

        Raises:
            KapsoAPIError: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout_val = timeout or self.timeout

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=timeout_val,
                )

                # Handle status codes
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 401:
                    raise KapsoAuthenticationError(
                        "Error de autenticación con Kapso API",
                        status_code=response.status_code,
                        response_data=response.text,
                    )
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
                        f"Error en Kapso API {response.status_code}: {response.text[:200]}",
                        status_code=response.status_code,
                        response_data=response.text,
                    )

        except httpx.TimeoutException:
            raise KapsoTimeoutError(
                f"Timeout conectando con Kapso API después de {timeout_val}s"
            )
        except (
            KapsoAPIError,
            KapsoAuthenticationError,
            KapsoValidationError,
            KapsoTimeoutError,
            KapsoNotFoundError,
        ):
            # Re-raise Kapso exceptions
            raise
        except Exception as e:
            logger.exception(f"Error inesperado en petición a Kapso: {e}")
            raise KapsoAPIError(f"Error inesperado: {str(e)}")

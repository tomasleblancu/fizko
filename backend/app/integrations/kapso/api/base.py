"""Base API client for common HTTP operations."""

import logging
from typing import Any, Optional

import httpx

from ..exceptions import (
    KapsoAPIError,
    KapsoAuthenticationError,
    KapsoNotFoundError,
    KapsoTimeoutError,
    KapsoValidationError,
)

logger = logging.getLogger(__name__)


class BaseAPI:
    """Base class for Kapso API modules with common HTTP functionality."""

    def __init__(self, api_token: str, base_url: str, timeout: int = 30):
        """
        Initialize base API client.

        Args:
            api_token: Kapso API token
            base_url: Base URL for Kapso API
            timeout: Default request timeout in seconds
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
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        timeout: Optional[int] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (will be appended to base_url)
            data: JSON payload for request body
            params: Query parameters
            timeout: Request timeout (uses default if not specified)
            headers: Additional headers to merge with default headers

        Returns:
            Parsed JSON response

        Raises:
            KapsoAuthenticationError: Invalid API token (401)
            KapsoNotFoundError: Resource not found (404)
            KapsoValidationError: Validation error (422)
            KapsoTimeoutError: Request timeout
            KapsoAPIError: Other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout_val = timeout or self.timeout

        # Merge headers
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=data,
                    params=params,
                    timeout=timeout_val,
                )

                # Handle different status codes
                if response.status_code == 401:
                    logger.error("Authentication failed: Invalid API token")
                    raise KapsoAuthenticationError("Invalid API token")
                elif response.status_code == 404:
                    logger.error(f"Resource not found: {endpoint}")
                    raise KapsoNotFoundError(f"Resource not found: {endpoint}")
                elif response.status_code == 422:
                    error_detail = response.text
                    logger.error(f"Validation error: {error_detail}")
                    raise KapsoValidationError(error_detail)
                elif response.status_code >= 500:
                    error_detail = response.text
                    logger.error(f"Server error ({response.status_code}): {error_detail}")
                    raise KapsoAPIError(f"Server error: {error_detail}", response.status_code)
                elif response.status_code >= 400:
                    error_detail = response.text
                    logger.error(f"Client error ({response.status_code}): {error_detail}")
                    raise KapsoAPIError(error_detail, response.status_code)

                # Success - return JSON
                return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout after {timeout_val}s: {url}")
            raise KapsoTimeoutError(f"Request timeout: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {str(e)}")
            raise KapsoAPIError(f"HTTP error: {str(e)}")

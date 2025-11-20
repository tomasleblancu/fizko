"""
Base Repository - Common functionality for all repositories.

Provides shared Supabase client access and error handling patterns.
"""

import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base class for all Supabase repositories."""

    def __init__(self, client: "Client"):
        """
        Initialize repository with Supabase client.

        Args:
            client: Supabase Python client instance
        """
        self._client = client

    def _log_error(self, operation: str, error: Exception, **context: Any) -> None:
        """
        Log repository errors with context.

        Args:
            operation: Name of the operation that failed
            error: The exception that occurred
            **context: Additional context to log
        """
        logger.error(
            f"Repository error in {operation}: {str(error)}",
            extra={"context": context},
            exc_info=True
        )

    def _extract_data(self, response: Any, operation: str) -> dict[str, Any] | None:
        """
        Extract data from Supabase response with error handling.

        Args:
            response: Supabase response object
            operation: Name of the operation (for logging)

        Returns:
            Extracted data dict or None if no data
        """
        if hasattr(response, 'data'):
            data = response.data
            # Supabase upsert can return a list when inserting (HTTP 201)
            # or a dict when updating (HTTP 200). Normalize to dict.
            if isinstance(data, list):
                return data[0] if len(data) > 0 else None
            return data
        else:
            logger.warning(f"Unexpected response format in {operation}: {type(response)}")
            return None

    def _extract_data_list(self, response: Any, operation: str) -> list[dict[str, Any]]:
        """
        Extract list data from Supabase response with error handling.

        Args:
            response: Supabase response object
            operation: Name of the operation (for logging)

        Returns:
            List of data dicts (empty list if no data)
        """
        data = self._extract_data(response, operation)
        if data is None:
            return []
        if isinstance(data, list):
            return data
        return [data]

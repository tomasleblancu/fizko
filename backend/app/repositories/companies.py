"""
Companies Repository - Handles company queries.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class CompaniesRepository(BaseRepository):
    """Repository for company data access."""

    async def get_by_id(
        self, company_id: str, include_tax_info: bool = True
    ) -> dict[str, Any] | None:
        """
        Get a company by ID.

        Args:
            company_id: Company UUID
            include_tax_info: Include company_tax_info relation (default True)

        Returns:
            Company dict or None if not found
        """
        try:
            # Build select string with optional tax info join
            select_str = "*"
            if include_tax_info:
                select_str = "*, company_tax_info(*)"

            response = (
                self._client
                .table("companies")
                .select(select_str)
                .eq("id", company_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_by_id")
        except Exception as e:
            self._log_error("get_by_id", e, company_id=company_id)
            return None

    async def get_by_rut(self, rut: str) -> dict[str, Any] | None:
        """
        Get a company by RUT.

        Args:
            rut: Company RUT (Chilean tax ID)

        Returns:
            Company dict or None if not found
        """
        try:
            response = (
                self._client
                .table("companies")
                .select("*")
                .eq("rut", rut)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_by_rut")
        except Exception as e:
            self._log_error("get_by_rut", e, rut=rut)
            return None

    async def get_all(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get all companies.

        Args:
            limit: Maximum number of companies

        Returns:
            List of company dicts
        """
        try:
            response = (
                self._client
                .table("companies")
                .select("*")
                .order("name")
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_all")
        except Exception as e:
            self._log_error("get_all", e, limit=limit)
            return []

    async def search_by_name(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Search companies by name.

        Args:
            query: Search query (name substring)
            limit: Maximum number of results

        Returns:
            List of matching company dicts
        """
        try:
            response = (
                self._client
                .table("companies")
                .select("*")
                .ilike("name", f"%{query}%")
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "search_by_name")
        except Exception as e:
            self._log_error("search_by_name", e, query=query)
            return []

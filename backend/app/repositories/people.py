"""
People Repository - Handles people/payroll queries.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class PeopleRepository(BaseRepository):
    """Repository for people/payroll data access."""

    async def get_person_by_id(self, person_id: str) -> dict[str, Any] | None:
        """
        Get a person by ID.

        Args:
            person_id: Person UUID

        Returns:
            Person dict or None if not found
        """
        try:
            response = (
                self._client
                .table("people")
                .select("*")
                .eq("id", person_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_person_by_id")
        except Exception as e:
            self._log_error("get_person_by_id", e, person_id=person_id)
            return None

    async def get_person_by_rut(
        self, company_id: str, rut: str
    ) -> dict[str, Any] | None:
        """
        Get a person by RUT for a specific company.

        Args:
            company_id: Company UUID
            rut: Person RUT (Chilean tax ID)

        Returns:
            Person dict or None if not found
        """
        try:
            response = (
                self._client
                .table("people")
                .select("*")
                .eq("company_id", company_id)
                .eq("rut", rut)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_person_by_rut")
        except Exception as e:
            self._log_error("get_person_by_rut", e, company_id=company_id, rut=rut)
            return None

    async def get_people_by_company(
        self,
        company_id: str,
        status: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get people for a company.

        Args:
            company_id: Company UUID
            status: Optional status filter (active, inactive)
            limit: Maximum number of people

        Returns:
            List of person dicts
        """
        try:
            query = (
                self._client
                .table("people")
                .select("*")
                .eq("company_id", company_id)
            )

            if status:
                query = query.eq("status", status)

            query = query.order("name").limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "get_people_by_company")
        except Exception as e:
            self._log_error(
                "get_people_by_company",
                e,
                company_id=company_id,
                status=status,
                limit=limit
            )
            return []

    async def get_active_employees(
        self, company_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get active employees for a company.

        Args:
            company_id: Company UUID
            limit: Maximum number of employees

        Returns:
            List of active employee dicts
        """
        try:
            response = (
                self._client
                .table("people")
                .select("*")
                .eq("company_id", company_id)
                .eq("status", "active")
                .order("name")
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_active_employees")
        except Exception as e:
            self._log_error("get_active_employees", e, company_id=company_id, limit=limit)
            return []

    async def get_employee_count(self, company_id: str) -> int:
        """
        Get total count of active employees for a company.

        Args:
            company_id: Company UUID

        Returns:
            Count of active employees
        """
        try:
            response = (
                self._client
                .table("people")
                .select("id", count="exact")
                .eq("company_id", company_id)
                .eq("status", "active")
                .execute()
            )

            # Supabase returns count in response.count
            if hasattr(response, 'count') and response.count is not None:
                return response.count

            # Fallback to counting data
            data = self._extract_data_list(response, "get_employee_count")
            return len(data)
        except Exception as e:
            self._log_error("get_employee_count", e, company_id=company_id)
            return 0

    async def get_payroll_summary(
        self, company_id: str, period: str | None = None
    ) -> dict[str, Any]:
        """
        Get payroll summary for a company.

        Args:
            company_id: Company UUID
            period: Optional period filter (YYYYMM format)

        Returns:
            Dict with payroll summary data
        """
        try:
            # This would ideally use a payroll table
            # For now, return basic employee count
            employee_count = await self.get_employee_count(company_id)

            return {
                "employee_count": employee_count,
                "period": period
            }
        except Exception as e:
            self._log_error("get_payroll_summary", e, company_id=company_id, period=period)
            return {
                "employee_count": 0,
                "period": period
            }

    async def search_people(
        self, company_id: str, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Search people by name or RUT.

        Args:
            company_id: Company UUID
            query: Search query (name or RUT substring)
            limit: Maximum number of results

        Returns:
            List of matching person dicts
        """
        try:
            # Search by name or RUT using ilike (case-insensitive)
            response = (
                self._client
                .table("people")
                .select("*")
                .eq("company_id", company_id)
                .or_(f"name.ilike.%{query}%,rut.ilike.%{query}%")
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "search_people")
        except Exception as e:
            self._log_error("search_people", e, company_id=company_id, query=query)
            return []

    async def create(
        self,
        company_id: str,
        rut: str,
        first_name: str,
        last_name: str,
        **kwargs
    ) -> dict[str, Any] | None:
        """
        Create a new person.

        Args:
            company_id: Company UUID
            rut: Person RUT (should be normalized before calling)
            first_name: First name
            last_name: Last name
            **kwargs: Additional person fields (email, phone, position_title, etc.)

        Returns:
            Created person dict or None if error
        """
        try:
            data = {
                "company_id": company_id,
                "rut": rut,
                "first_name": first_name,
                "last_name": last_name,
                "status": "active",
                **kwargs
            }

            response = (
                self._client
                .table("people")
                .insert(data)
                .execute()
            )

            return self._extract_data(response, "create_person")
        except Exception as e:
            self._log_error(
                "create_person",
                e,
                company_id=company_id,
                rut=rut
            )
            return None

    async def update(
        self,
        person_id: str,
        **kwargs
    ) -> dict[str, Any] | None:
        """
        Update a person.

        Args:
            person_id: Person UUID
            **kwargs: Fields to update

        Returns:
            Updated person dict or None if error
        """
        try:
            response = (
                self._client
                .table("people")
                .update(kwargs)
                .eq("id", person_id)
                .execute()
            )

            return self._extract_data(response, "update_person")
        except Exception as e:
            self._log_error("update_person", e, person_id=person_id)
            return None

"""
F29 Repository - Handles F29 form queries.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class F29Repository(BaseRepository):
    """Repository for F29 form data access."""

    async def get_form_by_id(self, form_id: str) -> dict[str, Any] | None:
        """
        Get an F29 form by ID.

        Args:
            form_id: F29 form UUID

        Returns:
            F29 form dict or None if not found
        """
        try:
            response = (
                self._client
                .table("f29_forms")
                .select("*")
                .eq("id", form_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_form_by_id")
        except Exception as e:
            self._log_error("get_form_by_id", e, form_id=form_id)
            return None

    async def get_forms_by_company(
        self,
        company_id: str,
        limit: int = 12,
        status: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get F29 forms for a company.

        Args:
            company_id: Company UUID
            limit: Maximum number of forms (default 12 for last year)
            status: Optional status filter (pending, paid, overdue)

        Returns:
            List of F29 form dicts
        """
        try:
            query = (
                self._client
                .table("f29_forms")
                .select("*")
                .eq("company_id", company_id)
            )

            if status:
                query = query.eq("status", status)

            query = query.order("period", desc=True).limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "get_forms_by_company")
        except Exception as e:
            self._log_error(
                "get_forms_by_company",
                e,
                company_id=company_id,
                status=status,
                limit=limit
            )
            return []

    async def get_form_by_period(
        self, company_id: str, period: str
    ) -> dict[str, Any] | None:
        """
        Get F29 form for a specific period.

        Args:
            company_id: Company UUID
            period: Period in YYYYMM format

        Returns:
            F29 form dict or None if not found
        """
        try:
            response = (
                self._client
                .table("f29_forms")
                .select("*")
                .eq("company_id", company_id)
                .eq("period", period)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_form_by_period")
        except Exception as e:
            self._log_error(
                "get_form_by_period",
                e,
                company_id=company_id,
                period=period
            )
            return None

    async def get_latest_form(
        self, company_id: str
    ) -> dict[str, Any] | None:
        """
        Get the most recent F29 form for a company.

        Args:
            company_id: Company UUID

        Returns:
            Latest F29 form dict or None if no forms exist
        """
        try:
            response = (
                self._client
                .table("f29_forms")
                .select("*")
                .eq("company_id", company_id)
                .order("period", desc=True)
                .limit(1)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_latest_form")
        except Exception as e:
            self._log_error("get_latest_form", e, company_id=company_id)
            return None

    async def get_pending_forms(
        self, company_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get pending F29 forms.

        Args:
            company_id: Optional company UUID filter
            limit: Maximum number of forms

        Returns:
            List of pending F29 form dicts
        """
        try:
            query = (
                self._client
                .table("f29_forms")
                .select("*")
                .eq("status", "pending")
            )

            if company_id:
                query = query.eq("company_id", company_id)

            query = query.order("due_date", desc=False).limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "get_pending_forms")
        except Exception as e:
            self._log_error("get_pending_forms", e, company_id=company_id, limit=limit)
            return []

    async def get_overdue_forms(
        self, company_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get overdue F29 forms.

        Args:
            company_id: Optional company UUID filter
            limit: Maximum number of forms

        Returns:
            List of overdue F29 form dicts
        """
        try:
            query = (
                self._client
                .table("f29_forms")
                .select("*")
                .eq("status", "overdue")
            )

            if company_id:
                query = query.eq("company_id", company_id)

            query = query.order("due_date", desc=False).limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "get_overdue_forms")
        except Exception as e:
            self._log_error("get_overdue_forms", e, company_id=company_id, limit=limit)
            return []

    async def get_payment_history(
        self, company_id: str, limit: int = 12
    ) -> list[dict[str, Any]]:
        """
        Get F29 payment history for a company.

        Args:
            company_id: Company UUID
            limit: Maximum number of paid forms

        Returns:
            List of paid F29 form dicts
        """
        try:
            response = (
                self._client
                .table("f29_forms")
                .select("*")
                .eq("company_id", company_id)
                .eq("status", "paid")
                .order("period", desc=True)
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_payment_history")
        except Exception as e:
            self._log_error("get_payment_history", e, company_id=company_id, limit=limit)
            return []

    async def get_by_folio(
        self, company_id: str, folio: str
    ) -> dict[str, Any] | None:
        """
        Get F29 form by company and folio.

        Args:
            company_id: Company UUID
            folio: F29 folio number

        Returns:
            F29 form dict or None if not found
        """
        try:
            response = (
                self._client
                .table("form29")
                .select("*")
                .eq("company_id", company_id)
                .eq("folio", folio)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_by_folio")
        except Exception as e:
            self._log_error("get_by_folio", e, company_id=company_id, folio=folio)
            return None

    async def upsert_f29_forms(
        self, forms: list[dict[str, Any]]
    ) -> tuple[int, int]:
        """
        Upsert F29 forms from SII downloads (insert or update based on unique constraint).

        Uses the form29_sii_downloads table which stores raw F29 data extracted
        from the SII portal, including folio, period, status, and PDF tracking.

        Args:
            forms: List of F29 form dicts to upsert (must match form29_sii_downloads schema)

        Returns:
            Tuple of (newly_created_count, updated_count)
        """
        if not forms:
            return 0, 0

        try:
            # Get existing folios to count new vs updated
            company_id = forms[0]["company_id"]
            folios = [form["sii_folio"] for form in forms if form.get("sii_folio") is not None]

            existing_folios = set()
            if folios:
                response = (
                    self._client
                    .table("form29_sii_downloads")
                    .select("sii_folio")
                    .eq("company_id", company_id)
                    .in_("sii_folio", folios)
                    .execute()
                )
                existing_folios = {form["sii_folio"] for form in response.data}

            # Count new vs updated
            nuevos = sum(1 for form in forms if form.get("sii_folio") not in existing_folios)
            actualizados = len(forms) - nuevos

            # Supabase upsert - use company_id + sii_folio as unique identifier
            # This matches the unique constraint: form29_sii_downloads_company_folio_unique
            response = (
                self._client
                .table("form29_sii_downloads")
                .upsert(forms, on_conflict="company_id,sii_folio")
                .execute()
            )

            logger.info(
                f"✅ Upserted {len(forms)} F29 forms to form29_sii_downloads: "
                f"{nuevos} nuevos, {actualizados} actualizados"
            )
            return nuevos, actualizados

        except Exception as e:
            self._log_error("upsert_f29_forms", e, count=len(forms))
            return 0, 0

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
                .table("form29")
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
                .table("form29")
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
                .table("form29")
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
                .table("form29")
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
                .table("form29")
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
                .table("form29")
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
                .table("form29")
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

    # =====================================================================
    # DRAFT MANAGEMENT METHODS (form29 table)
    # =====================================================================

    async def get_draft_by_period(
        self,
        company_id: str,
        period_year: int,
        period_month: int,
        revision_number: int | None = None
    ) -> dict[str, Any] | None:
        """
        Get Form29 draft for a specific period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)
            revision_number: Optional revision number (defaults to latest non-cancelled)

        Returns:
            Form29 draft dict or None if not found
        """
        try:
            query = (
                self._client
                .table("form29")
                .select("*")
                .eq("company_id", company_id)
                .eq("period_year", period_year)
                .eq("period_month", period_month)
            )

            if revision_number is not None:
                query = query.eq("revision_number", revision_number)
            else:
                # Get latest non-cancelled revision
                query = query.neq("status", "cancelled").order("revision_number", desc=True)

            query = query.limit(1).maybe_single()
            response = query.execute()

            return self._extract_data(response, "get_draft_by_period")
        except Exception as e:
            self._log_error(
                "get_draft_by_period",
                e,
                company_id=company_id,
                period_year=period_year,
                period_month=period_month,
                revision_number=revision_number
            )
            return None

    async def draft_exists_for_period(
        self,
        company_id: str,
        period_year: int,
        period_month: int,
        exclude_cancelled: bool = True
    ) -> bool:
        """
        Check if a Form29 draft exists for a specific period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)
            exclude_cancelled: Whether to exclude cancelled forms (default True)

        Returns:
            True if draft exists, False otherwise
        """
        try:
            query = (
                self._client
                .table("form29")
                .select("id", count="exact")
                .eq("company_id", company_id)
                .eq("period_year", period_year)
                .eq("period_month", period_month)
            )

            if exclude_cancelled:
                query = query.neq("status", "cancelled")

            response = query.execute()
            return response.count > 0 if hasattr(response, 'count') else False
        except Exception as e:
            self._log_error(
                "draft_exists_for_period",
                e,
                company_id=company_id,
                period_year=period_year,
                period_month=period_month
            )
            return False

    async def get_latest_revision_number(
        self,
        company_id: str,
        period_year: int,
        period_month: int
    ) -> int:
        """
        Get the latest revision number for a period.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)

        Returns:
            Latest revision number (0 if none exist)
        """
        try:
            response = (
                self._client
                .table("form29")
                .select("revision_number")
                .eq("company_id", company_id)
                .eq("period_year", period_year)
                .eq("period_month", period_month)
                .order("revision_number", desc=True)
                .limit(1)
                .maybe_single()
                .execute()
            )

            data = self._extract_data(response, "get_latest_revision_number")
            return data["revision_number"] if data else 0
        except Exception as e:
            self._log_error(
                "get_latest_revision_number",
                e,
                company_id=company_id,
                period_year=period_year,
                period_month=period_month
            )
            return 0

    async def create_draft(
        self,
        company_id: str,
        period_year: int,
        period_month: int,
        created_by_user_id: str | None = None,
        **values
    ) -> dict[str, Any] | None:
        """
        Create a new Form29 draft.

        Args:
            company_id: Company UUID
            period_year: Year
            period_month: Month (1-12)
            created_by_user_id: Optional user ID who created the draft
            **values: Additional form values (total_sales, taxable_sales, etc.)

        Returns:
            Created Form29 draft or None on error
        """
        try:
            # Get next revision number
            revision_number = await self.get_latest_revision_number(
                company_id, period_year, period_month
            ) + 1

            # Prepare form data
            form_data = {
                "company_id": company_id,
                "period_year": period_year,
                "period_month": period_month,
                "revision_number": revision_number,
                "status": "draft",
                "validation_status": "pending",
                "payment_status": "unpaid",
                **values
            }

            if created_by_user_id:
                form_data["created_by_user_id"] = created_by_user_id

            # Insert form
            response = (
                self._client
                .table("form29")
                .insert(form_data)
                .execute()
            )

            result = self._extract_data(response, "create_draft")
            if result:
                logger.info(
                    f"✅ Created Form29 draft for company {company_id}, "
                    f"period {period_year}-{period_month:02d}, revision {revision_number}"
                )
            return result
        except Exception as e:
            self._log_error(
                "create_draft",
                e,
                company_id=company_id,
                period_year=period_year,
                period_month=period_month
            )
            return None

    async def update_draft(
        self,
        form_id: str,
        **updates
    ) -> dict[str, Any] | None:
        """
        Update a Form29 draft.

        Args:
            form_id: Form29 UUID
            **updates: Fields to update

        Returns:
            Updated Form29 draft or None on error
        """
        try:
            response = (
                self._client
                .table("form29")
                .update(updates)
                .eq("id", form_id)
                .execute()
            )

            return self._extract_data(response, "update_draft")
        except Exception as e:
            self._log_error("update_draft", e, form_id=form_id, updates=updates)
            return None

    async def get_active_drafts(
        self,
        company_id: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get all active drafts (status=draft).

        Args:
            company_id: Optional company filter
            limit: Maximum number of drafts

        Returns:
            List of Form29 drafts
        """
        try:
            query = (
                self._client
                .table("form29")
                .select("*")
                .eq("status", "draft")
            )

            if company_id:
                query = query.eq("company_id", company_id)

            query = query.order("period_year", desc=True).order("period_month", desc=True).limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "get_active_drafts")
        except Exception as e:
            self._log_error("get_active_drafts", e, company_id=company_id, limit=limit)
            return []

    async def get_drafts_by_company(
        self,
        company_id: str,
        period_year: int | None = None,
        period_month: int | None = None,
        status: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get Form29 drafts for a company with filters.

        Args:
            company_id: Company UUID
            period_year: Optional year filter
            period_month: Optional month filter
            status: Optional status filter
            limit: Maximum number of drafts

        Returns:
            List of Form29 drafts
        """
        try:
            query = (
                self._client
                .table("form29")
                .select("*")
                .eq("company_id", company_id)
            )

            if period_year is not None:
                query = query.eq("period_year", period_year)

            if period_month is not None:
                query = query.eq("period_month", period_month)

            if status:
                query = query.eq("status", status)

            query = query.order("period_year", desc=True).order("period_month", desc=True).limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "get_drafts_by_company")
        except Exception as e:
            self._log_error(
                "get_drafts_by_company",
                e,
                company_id=company_id,
                period_year=period_year,
                period_month=period_month,
                status=status
            )
            return []

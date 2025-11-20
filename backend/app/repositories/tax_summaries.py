"""
Tax Summaries Repository - Data access layer for tax documents.

This repository ONLY handles data extraction from Supabase.
Business logic is handled by TaxSummaryService.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class TaxSummariesRepository(BaseRepository):
    """
    Repository for tax document data access.

    Provides simple data extraction methods without business logic.
    All calculations and credit note handling is done in the service layer.
    """

    async def get_documents(
        self,
        table: str,
        company_id: str,
        document_types: list[str] | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
        fields: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get documents from a table with optional filters.

        Args:
            table: Table name (sales_documents or purchase_documents)
            company_id: Company UUID
            document_types: Optional list of document types to filter
            period_start: Optional start date (YYYY-MM-DD format)
            period_end: Optional end date (YYYY-MM-DD format, exclusive)
            fields: Fields to select (defaults to all)

        Returns:
            List of document dicts
        """
        try:
            # Build query
            select_fields = ", ".join(fields) if fields else "*"
            query = (
                self._client
                .table(table)
                .select(select_fields)
                .eq("company_id", company_id)
            )

            # Add document type filter if provided
            if document_types:
                query = query.in_("document_type", document_types)

            # Add date range filter if provided
            if period_start and period_end:
                query = query.gte("issue_date", period_start).lt("issue_date", period_end)

            # Execute query
            response = query.execute()
            return self._extract_data_list(response, f"get_documents_{table}")

        except Exception as e:
            self._log_error(
                "get_documents",
                e,
                table=table,
                company_id=company_id,
                document_types=document_types
            )
            return []

    async def get_sales_documents(
        self,
        company_id: str,
        document_types: list[str] | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
        fields: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get sales documents.

        Convenience method that calls get_documents for sales_documents table.
        """
        return await self.get_documents(
            "sales_documents",
            company_id,
            document_types,
            period_start,
            period_end,
            fields
        )

    async def get_purchase_documents(
        self,
        company_id: str,
        document_types: list[str] | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
        fields: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get purchase documents.

        Convenience method that calls get_documents for purchase_documents table.
        """
        return await self.get_documents(
            "purchase_documents",
            company_id,
            document_types,
            period_start,
            period_end,
            fields
        )

    # Legacy methods for backward compatibility (delegate to service)
    # These will be deprecated - use TaxSummaryService instead

    async def get_iva_summary(
        self, company_id: str, period: str | None = None
    ) -> dict[str, Any]:
        """
        DEPRECATED: Use TaxSummaryService.get_iva_summary() instead.

        This method is kept for backward compatibility but delegates
        all logic to the service layer.
        """
        logger.warning(
            "TaxSummariesRepository.get_iva_summary() is deprecated. "
            "Use TaxSummaryService.get_iva_summary() instead."
        )

        # Import service here to avoid circular dependency
        from app.services.tax_summary_service import TaxSummaryService
        from app.config.supabase import get_supabase_client

        supabase = get_supabase_client()
        service = TaxSummaryService(supabase)
        return await service.get_iva_summary(company_id, period)

    async def get_revenue_summary(
        self, company_id: str, period: str | None = None
    ) -> dict[str, Any]:
        """
        DEPRECATED: Use TaxSummaryService.get_revenue_summary() instead.
        """
        logger.warning(
            "TaxSummariesRepository.get_revenue_summary() is deprecated. "
            "Use TaxSummaryService.get_revenue_summary() instead."
        )

        from app.services.tax_summary_service import TaxSummaryService
        from app.config.supabase import get_supabase_client

        supabase = get_supabase_client()
        service = TaxSummaryService(supabase)
        return await service.get_revenue_summary(company_id, period)

    async def get_expense_summary(
        self, company_id: str, period: str | None = None
    ) -> dict[str, Any]:
        """
        DEPRECATED: Use TaxSummaryService.get_expense_summary() instead.
        """
        logger.warning(
            "TaxSummariesRepository.get_expense_summary() is deprecated. "
            "Use TaxSummaryService.get_expense_summary() instead."
        )

        from app.services.tax_summary_service import TaxSummaryService
        from app.config.supabase import get_supabase_client

        supabase = get_supabase_client()
        service = TaxSummaryService(supabase)
        return await service.get_expense_summary(company_id, period)

    async def get_tax_summary(
        self, company_id: str, period: str | None = None
    ) -> dict[str, Any] | None:
        """
        DEPRECATED: Use TaxSummaryService methods instead.

        Get comprehensive tax summary (IVA, revenue, expenses).
        """
        logger.warning(
            "TaxSummariesRepository.get_tax_summary() is deprecated. "
            "Use TaxSummaryService methods instead."
        )

        try:
            from app.services.tax_summary_service import TaxSummaryService
            from app.config.supabase import get_supabase_client

            supabase = get_supabase_client()
            service = TaxSummaryService(supabase)

            # Get all summaries
            iva_summary = await service.get_iva_summary(company_id, period)
            revenue_summary = await service.get_revenue_summary(company_id, period)
            expense_summary = await service.get_expense_summary(company_id, period)

            return {
                "iva": iva_summary,
                "revenue": revenue_summary,
                "expenses": expense_summary,
                "period": period
            }

        except Exception as e:
            self._log_error("get_tax_summary", e, company_id=company_id, period=period)
            return None

    async def get_monthly_revenue_trend(
        self, company_id: str, months: int = 6
    ) -> list[dict[str, Any]]:
        """
        Get monthly revenue trend for the last N months.

        Simple aggregation - no complex business logic.
        """
        try:
            response = (
                self._client
                .table("sales_documents")
                .select("issue_date, total_amount")
                .eq("company_id", company_id)
                .order("issue_date", desc=True)
                .execute()
            )

            data = self._extract_data_list(response, "get_monthly_revenue_trend")

            # Aggregate by month (YYYYMM)
            monthly_revenue: dict[str, float] = {}
            for doc in data:
                issue_date = doc.get("issue_date", "")
                if not issue_date:
                    continue

                # Extract YYYYMM from date
                month_key = str(issue_date).replace("-", "")[:6]
                if month_key not in monthly_revenue:
                    monthly_revenue[month_key] = 0

                monthly_revenue[month_key] += doc.get("total_amount", 0) or 0

            # Sort by month and limit
            trend = [
                {"month": month, "revenue": revenue}
                for month, revenue in sorted(monthly_revenue.items(), reverse=True)[:months]
            ]

            return trend

        except Exception as e:
            self._log_error("get_monthly_revenue_trend", e, company_id=company_id, months=months)
            return []

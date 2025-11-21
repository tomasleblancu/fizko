"""
Tax Summary Service - Business logic for tax calculations.

This service handles all tax calculation logic, delegating data extraction
to repositories. Follows the service layer pattern for separation of concerns.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TaxSummaryService:
    """
    Service for tax summary calculations.

    Handles business logic for:
    - IVA (VAT) calculations with credit notes
    - Revenue and expense summaries
    - Tax balance computations

    Uses SupabaseClient repositories for data access.
    """

    def __init__(self, supabase_client):
        """
        Initialize service with Supabase client.

        Args:
            supabase_client: SupabaseClient instance with repository access
        """
        self.supabase = supabase_client

    async def get_iva_summary(
        self, company_id: str, period: str | None = None
    ) -> dict[str, Any]:
        """
        Calculate IVA summary with proper credit note handling.

        Business logic:
        1. Sum positive sales documents (facturas, boletas, etc.)
        2. Subtract sales credit notes
        3. Sum positive purchase documents
        4. Subtract purchase credit notes
        5. Calculate net IVA balance
        6. Get previous month credit from F29
        7. Calculate PPM (0.125% of net revenue)
        8. Get retención from honorarios receipts

        Args:
            company_id: Company UUID
            period: Period in YYYY-MM format (optional)

        Returns:
            Dict with:
            - debito_fiscal: Net sales IVA (after credit notes)
            - credito_fiscal: Net purchase IVA (after credit notes)
            - balance: Net IVA to pay (positive) or credit (negative)
            - previous_month_credit: Credit from previous month's F29
            - overdue_iva_credit: Overdue IVA that can't be recovered
            - ppm: PPM amount (0.125% of net revenue)
            - retencion: Retención from honorarios receipts
            - reverse_charge_withholding: Retención Cambio de Sujeto (código 46)
            - sales_count: Total sales documents
            - purchases_count: Total purchase documents
        """
        try:
            # Calculate date range
            period_start, period_end = self._calculate_period_range(period)

            # Get sales data with total_amount and net_amount for PPM calculation
            sales_positive = await self._get_documents(
                "sales_documents",
                company_id,
                document_types=[
                    'factura_venta', 'boleta', 'boleta_exenta',
                    'factura_exenta', 'comprobante_pago',
                    'liquidacion_factura', 'nota_debito_venta'
                ],
                period_start=period_start,
                period_end=period_end,
                fields=["tax_amount", "total_amount", "net_amount", "overdue_iva_credit"]
            )

            sales_credits = await self._get_documents(
                "sales_documents",
                company_id,
                document_types=['nota_credito_venta'],
                period_start=period_start,
                period_end=period_end,
                fields=["tax_amount", "total_amount", "net_amount", "overdue_iva_credit"]
            )

            # Calculate net sales IVA and revenue
            sales_positive_tax = sum(doc.get("tax_amount", 0) or 0 for doc in sales_positive)
            sales_positive_total = sum(doc.get("total_amount", 0) or 0 for doc in sales_positive)
            sales_positive_overdue = sum(doc.get("overdue_iva_credit", 0) or 0 for doc in sales_positive)

            # For PPM calculation: exclude documents with overdue_iva_credit
            # If a document has overdue, it means it's "out of time" and shouldn't affect the tax base
            sales_positive_net = sum(
                doc.get("net_amount", 0) or 0
                for doc in sales_positive
                if not (doc.get("overdue_iva_credit", 0) or 0) > 0
            )

            sales_credit_tax = sum(doc.get("tax_amount", 0) or 0 for doc in sales_credits)
            sales_credit_total = sum(doc.get("total_amount", 0) or 0 for doc in sales_credits)
            sales_credit_overdue = sum(doc.get("overdue_iva_credit", 0) or 0 for doc in sales_credits)

            # For PPM calculation: exclude credit notes with overdue_iva_credit
            sales_credit_net = sum(
                doc.get("net_amount", 0) or 0
                for doc in sales_credits
                if not (doc.get("overdue_iva_credit", 0) or 0) > 0
            )

            debito_fiscal = sales_positive_tax - sales_credit_tax
            total_revenue = sales_positive_total - sales_credit_total
            net_revenue = sales_positive_net - sales_credit_net
            # Overdue IVA: ALWAYS adds to tax burden (can't be recovered)
            # Both positive docs AND credit notes increase the burden
            overdue_iva_from_sales = sales_positive_overdue + sales_credit_overdue

            # Get purchase data using repository
            purchases_positive = await self._get_documents(
                "purchase_documents",
                company_id,
                document_types=[
                    'factura_compra', 'factura_exenta_compra',
                    'liquidacion_factura', 'nota_debito_compra',
                    'declaracion_ingreso'
                ],
                period_start=period_start,
                period_end=period_end,
                fields=["tax_amount", "overdue_iva_credit"]
            )

            purchases_credits = await self._get_documents(
                "purchase_documents",
                company_id,
                document_types=['nota_credito_compra'],
                period_start=period_start,
                period_end=period_end,
                fields=["tax_amount", "overdue_iva_credit"]
            )

            # Calculate net purchase IVA
            purchases_positive_tax = sum(doc.get("tax_amount", 0) or 0 for doc in purchases_positive)
            purchases_positive_overdue = sum(doc.get("overdue_iva_credit", 0) or 0 for doc in purchases_positive)

            purchases_credit_tax = sum(doc.get("tax_amount", 0) or 0 for doc in purchases_credits)
            purchases_credit_overdue = sum(doc.get("overdue_iva_credit", 0) or 0 for doc in purchases_credits)

            credito_fiscal = purchases_positive_tax - purchases_credit_tax
            # Overdue IVA: ALWAYS adds to tax burden (can't be claimed)
            # Both positive docs AND credit notes increase the burden
            overdue_iva_from_purchases = purchases_positive_overdue + purchases_credit_overdue

            # Calculate total overdue IVA credit
            overdue_iva_credit = overdue_iva_from_sales + overdue_iva_from_purchases

            # Calculate balance
            balance = debito_fiscal - credito_fiscal

            # Get previous month credit from F29
            previous_month_credit = await self._get_previous_month_credit(company_id, period_start)

            # Calculate PPM (0.125% of net revenue excluding IVA)
            ppm = self._calculate_ppm(net_revenue)

            # Get retención from honorarios receipts
            retencion = await self._get_retencion(company_id, period_start, period_end)

            # Get reverse charge withholding (código 46)
            reverse_charge_withholding = await self._get_reverse_charge_withholding(company_id, period_start, period_end)

            # Count documents
            sales_count = len(sales_positive) + len(sales_credits)
            purchases_count = len(purchases_positive) + len(purchases_credits)

            return {
                "debito_fiscal": debito_fiscal,
                "credito_fiscal": credito_fiscal,
                "balance": balance,
                "previous_month_credit": previous_month_credit or 0.0,
                "overdue_iva_credit": overdue_iva_credit,
                "ppm": ppm or 0.0,
                "retencion": retencion or 0.0,
                "reverse_charge_withholding": reverse_charge_withholding or 0.0,
                "sales_count": sales_count,
                "purchases_count": purchases_count
            }

        except Exception as e:
            logger.error(f"Error calculating IVA summary: {e}", exc_info=True)
            return {
                "debito_fiscal": 0,
                "credito_fiscal": 0,
                "balance": 0,
                "previous_month_credit": 0.0,
                "overdue_iva_credit": 0.0,
                "ppm": 0.0,
                "retencion": 0.0,
                "reverse_charge_withholding": 0.0,
                "sales_count": 0,
                "purchases_count": 0
            }

    async def get_revenue_summary(
        self, company_id: str, period: str | None = None
    ) -> dict[str, Any]:
        """
        Calculate revenue summary with credit note handling.

        Args:
            company_id: Company UUID
            period: Period in YYYY-MM format (optional)

        Returns:
            Dict with total_revenue, net_revenue, document_count
        """
        try:
            period_start, period_end = self._calculate_period_range(period)

            # Get positive sales
            sales_positive = await self._get_documents(
                "sales_documents",
                company_id,
                document_types=[
                    'factura_venta', 'boleta', 'boleta_exenta',
                    'factura_exenta', 'comprobante_pago',
                    'liquidacion_factura', 'nota_debito_venta'
                ],
                period_start=period_start,
                period_end=period_end,
                fields=["total_amount", "net_amount"]
            )

            # Get credit notes
            sales_credits = await self._get_documents(
                "sales_documents",
                company_id,
                document_types=['nota_credito_venta'],
                period_start=period_start,
                period_end=period_end,
                fields=["total_amount", "net_amount"]
            )

            # Calculate net revenue
            positive_total = sum(doc.get("total_amount", 0) or 0 for doc in sales_positive)
            positive_net = sum(doc.get("net_amount", 0) or 0 for doc in sales_positive)

            credit_total = sum(doc.get("total_amount", 0) or 0 for doc in sales_credits)
            credit_net = sum(doc.get("net_amount", 0) or 0 for doc in sales_credits)

            total_revenue = positive_total - credit_total
            net_revenue = positive_net - credit_net

            return {
                "total_revenue": total_revenue,
                "net_revenue": net_revenue,
                "document_count": len(sales_positive) + len(sales_credits)
            }

        except Exception as e:
            logger.error(f"Error calculating revenue summary: {e}", exc_info=True)
            return {
                "total_revenue": 0,
                "net_revenue": 0,
                "document_count": 0
            }

    async def get_expense_summary(
        self, company_id: str, period: str | None = None
    ) -> dict[str, Any]:
        """
        Calculate expense summary with credit note handling.

        Args:
            company_id: Company UUID
            period: Period in YYYY-MM format (optional)

        Returns:
            Dict with total_expenses, net_expenses, document_count
        """
        try:
            period_start, period_end = self._calculate_period_range(period)

            # Get positive purchases
            purchases_positive = await self._get_documents(
                "purchase_documents",
                company_id,
                document_types=[
                    'factura_compra', 'factura_exenta_compra',
                    'liquidacion_factura', 'nota_debito_compra',
                    'declaracion_ingreso'
                ],
                period_start=period_start,
                period_end=period_end,
                fields=["total_amount", "net_amount"]
            )

            # Get credit notes
            purchases_credits = await self._get_documents(
                "purchase_documents",
                company_id,
                document_types=['nota_credito_compra'],
                period_start=period_start,
                period_end=period_end,
                fields=["total_amount", "net_amount"]
            )

            # Calculate net expenses
            positive_total = sum(doc.get("total_amount", 0) or 0 for doc in purchases_positive)
            positive_net = sum(doc.get("net_amount", 0) or 0 for doc in purchases_positive)

            credit_total = sum(doc.get("total_amount", 0) or 0 for doc in purchases_credits)
            credit_net = sum(doc.get("net_amount", 0) or 0 for doc in purchases_credits)

            total_expenses = positive_total - credit_total
            net_expenses = positive_net - credit_net

            return {
                "total_expenses": total_expenses,
                "net_expenses": net_expenses,
                "document_count": len(purchases_positive) + len(purchases_credits)
            }

        except Exception as e:
            logger.error(f"Error calculating expense summary: {e}", exc_info=True)
            return {
                "total_expenses": 0,
                "net_expenses": 0,
                "document_count": 0
            }

    # Private helper methods

    def _calculate_ppm(self, net_revenue: float) -> float | None:
        """
        Calculate PPM (Pago Provisional Mensual) as 0.125% of net revenue.

        PPM is a monthly provisional payment towards annual income tax.
        Calculated as 0.125% of net sales revenue (excluding IVA).

        Args:
            net_revenue: Net sales revenue for the period (excluding IVA)

        Returns:
            PPM amount or None if revenue is 0 or negative
        """
        if net_revenue > 0:
            return net_revenue * 0.00125  # 0.125%
        return None

    async def _get_retencion(
        self,
        company_id: str,
        period_start: str | None,
        period_end: str | None
    ) -> float | None:
        """
        Get retención (withholding) from honorarios receipts.

        Retención is the tax withholding from professional services invoices
        (boletas de honorarios). Typically 12.25% in Chile.

        Args:
            company_id: Company UUID
            period_start: Period start date (YYYY-MM-DD)
            period_end: Period end date (YYYY-MM-DD, exclusive)

        Returns:
            Total retención amount or None if no receipts found
        """
        try:
            # Build query for honorarios_receipts table
            query = (
                self.supabase.client
                .table("honorarios_receipts")
                .select("recipient_retention")
                .eq("company_id", company_id)
                .eq("receipt_type", "received")  # Only receipts we received (paid)
            )

            # Add date filters if provided
            if period_start and period_end:
                query = query.gte("issue_date", period_start).lt("issue_date", period_end)

            # Execute query
            response = query.execute()

            # Extract and sum retención
            if hasattr(response, 'data') and response.data:
                receipts = response.data if isinstance(response.data, list) else [response.data]
                total_retencion = sum(
                    receipt.get("recipient_retention", 0) or 0
                    for receipt in receipts
                )
                return total_retencion if total_retencion > 0 else None

        except Exception as e:
            logger.error(f"Error getting retención: {e}", exc_info=True)

        return None

    async def _get_reverse_charge_withholding(
        self,
        company_id: str,
        period_start: str | None,
        period_end: str | None
    ) -> float | None:
        """
        Get Reverse Charge Withholding from purchase documents with code 46.

        This is when the buyer pays the seller's IVA obligation (Retención Cambio de Sujeto).
        Document type code 46 represents this special case in Chilean tax law.

        Args:
            company_id: Company UUID
            period_start: Period start date (YYYY-MM-DD)
            period_end: Period end date (YYYY-MM-DD, exclusive)

        Returns:
            Total reverse charge withholding amount or None if no documents found
        """
        try:
            # Build query for purchase_documents table
            query = (
                self.supabase.client
                .table("purchase_documents")
                .select("tax_amount")
                .eq("company_id", company_id)
                .eq("document_type_code", "46")  # Código 46: Retención Cambio de Sujeto
            )

            # Add date filters if provided (use accounting_date for consistency)
            if period_start and period_end:
                query = query.gte("accounting_date", period_start).lt("accounting_date", period_end)

            # Execute query
            response = query.execute()

            # Extract and sum tax amounts
            if hasattr(response, 'data') and response.data:
                documents = response.data if isinstance(response.data, list) else [response.data]
                total_reverse_charge = sum(
                    doc.get("tax_amount", 0) or 0
                    for doc in documents
                )
                return total_reverse_charge if total_reverse_charge > 0 else None

        except Exception as e:
            logger.error(f"Error getting reverse charge withholding: {e}", exc_info=True)

        return None

    async def _get_previous_month_credit(
        self,
        company_id: str,
        period_start: str | None
    ) -> float | None:
        """
        Get credit from previous month's F29 (código 077 or negative net_iva).

        First checks form29 drafts (saved/paid), then falls back
        to form29_sii_downloads for real SII forms.

        Logic:
        1. Search form29 table for saved/paid forms
           - If net_iva < 0, use abs(net_iva) as credit
        2. Fallback to form29_sii_downloads table
           - Extract código 077 from extra_data

        Args:
            company_id: Company UUID
            period_start: Current period start date (YYYY-MM-DD)

        Returns:
            Previous month credit amount or None if not found
        """
        if not period_start:
            return None

        try:
            # Calculate previous month
            year, month, _ = period_start.split("-")
            year, month = int(year), int(month)

            if month == 1:
                prev_year = year - 1
                prev_month = 12
            else:
                prev_year = year
                prev_month = month - 1

            # FIRST: Check form29 drafts for saved/paid forms
            draft_response = (
                self.supabase.client
                .table("form29")
                .select("net_iva")
                .eq("company_id", company_id)
                .eq("period_year", prev_year)
                .eq("period_month", prev_month)
                .in_("status", ["saved", "paid"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if hasattr(draft_response, 'data') and draft_response.data:
                draft = draft_response.data[0] if isinstance(draft_response.data, list) else draft_response.data
                net_iva = draft.get("net_iva")
                if net_iva is not None and net_iva < 0:
                    # Negative net_iva means credit to carry forward
                    return abs(float(net_iva))

            # FALLBACK: Query for the "Vigente" F29 from SII downloads
            sii_response = (
                self.supabase.client
                .table("form29_sii_downloads")
                .select("extra_data")
                .eq("company_id", company_id)
                .eq("period_year", prev_year)
                .eq("period_month", prev_month)
                .eq("status", "Vigente")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if hasattr(sii_response, 'data') and sii_response.data:
                f29 = sii_response.data[0] if isinstance(sii_response.data, list) else sii_response.data
                extra_data = f29.get("extra_data")

                if extra_data:
                    # Extract code 077 from extra_data
                    f29_data = extra_data.get("f29_data", {})
                    codes = f29_data.get("codes", {})
                    code_077 = codes.get("077", {})
                    remanente_value = code_077.get("value")

                    if remanente_value is not None:
                        return float(remanente_value)

        except Exception as e:
            logger.error(f"Error getting previous month credit: {e}", exc_info=True)

        return None

    def _calculate_period_range(self, period: str | None) -> tuple[str | None, str | None]:
        """
        Calculate date range from period string.

        Args:
            period: Period in YYYY-MM format or None

        Returns:
            Tuple of (period_start, period_end) in YYYY-MM-DD format
        """
        if not period:
            return None, None

        year, month = period.split("-")
        year, month = int(year), int(month)

        period_start = f"{year}-{month:02d}-01"

        if month == 12:
            period_end = f"{year + 1}-01-01"
        else:
            period_end = f"{year}-{month + 1:02d}-01"

        return period_start, period_end

    async def _get_documents(
        self,
        table: str,
        company_id: str,
        document_types: list[str],
        period_start: str | None = None,
        period_end: str | None = None,
        fields: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get documents from repository with filters.

        Uses accounting_date for tax recognition.
        accounting_date logic:
        - Sales: always issue_date
        - Purchases: reception_date for most, issue_date for DIN

        Args:
            table: Table name (sales_documents or purchase_documents)
            company_id: Company UUID
            document_types: List of document types to filter
            period_start: Start date (YYYY-MM-DD)
            period_end: End date (YYYY-MM-DD)
            fields: Fields to select (defaults to ["tax_amount"])

        Returns:
            List of document dicts
        """
        if fields is None:
            fields = ["tax_amount"]

        # Build query
        query = (
            self.supabase.client
            .table(table)
            .select(", ".join(fields))
            .eq("company_id", company_id)
            .in_("document_type", document_types)
        )

        # Add date filters if provided
        # Always use accounting_date for tax calculations
        if period_start and period_end:
            query = query.gte("accounting_date", period_start).lt("accounting_date", period_end)

        # Execute query
        response = query.execute()

        # Extract data
        if hasattr(response, 'data') and response.data:
            return response.data if isinstance(response.data, list) else [response.data]

        return []

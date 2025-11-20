"""
Expenses Repository - Handles manual expense queries.
"""

import logging
from datetime import date
from typing import Any
from decimal import Decimal

from .base import BaseRepository

logger = logging.getLogger(__name__)


class ExpensesRepository(BaseRepository):
    """Repository for manual expense data access."""

    async def create(
        self,
        company_id: str,
        created_by_user_id: str,
        expense_category: str,
        expense_date: date,
        description: str,
        total_amount: Decimal,
        has_tax: bool = True,
        vendor_name: str | None = None,
        vendor_rut: str | None = None,
        receipt_number: str | None = None,
        is_reimbursable: bool = False,
        notes: str | None = None,
        receipt_file_url: str | None = None,
        receipt_file_name: str | None = None,
        receipt_mime_type: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Create a new expense.

        Args:
            company_id: Company UUID
            created_by_user_id: User UUID who created the expense
            expense_category: Category (transport, parking, meals, etc.)
            expense_date: Date of expense
            description: Brief description
            total_amount: Total amount paid
            has_tax: Whether amount includes 19% IVA
            vendor_name: Vendor name
            vendor_rut: Vendor RUT
            receipt_number: Receipt number
            is_reimbursable: Whether expense should be reimbursed
            notes: Additional notes
            receipt_file_url: URL to receipt file
            receipt_file_name: Receipt filename
            receipt_mime_type: Receipt MIME type

        Returns:
            Created expense dict or None if error
        """
        try:
            # Calculate net and tax amounts
            if has_tax:
                # Total includes 19% IVA
                # net = total / 1.19
                # tax = total - net
                net_amount = float(total_amount) / 1.19
                tax_amount = float(total_amount) - net_amount
            else:
                net_amount = float(total_amount)
                tax_amount = 0.0

            data = {
                "company_id": company_id,
                "created_by_user_id": created_by_user_id,
                "expense_category": expense_category,
                "expense_date": expense_date.isoformat(),
                "description": description,
                "vendor_name": vendor_name,
                "vendor_rut": vendor_rut,
                "receipt_number": receipt_number,
                "total_amount": float(total_amount),
                "net_amount": net_amount,
                "tax_amount": tax_amount,
                "has_tax": has_tax,
                "is_reimbursable": is_reimbursable,
                "notes": notes,
                "receipt_file_url": receipt_file_url,
                "receipt_file_name": receipt_file_name,
                "receipt_mime_type": receipt_mime_type,
                "status": "draft",
            }

            response = (
                self._client
                .table("expenses")
                .insert(data)
                .execute()
            )

            return self._extract_data(response, "create_expense")
        except Exception as e:
            self._log_error(
                "create_expense",
                e,
                company_id=company_id,
                category=expense_category
            )
            return None

    async def list(
        self,
        company_id: str,
        status: str | None = None,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List expenses with filters.

        Args:
            company_id: Company UUID
            status: Filter by status
            category: Filter by category
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            Tuple of (expenses list, total count)
        """
        try:
            query = (
                self._client
                .table("expenses")
                .select("*", count="exact")
                .eq("company_id", company_id)
            )

            if status:
                query = query.eq("status", status)
            if category:
                query = query.eq("expense_category", category)
            if date_from:
                query = query.gte("expense_date", date_from.isoformat())
            if date_to:
                query = query.lte("expense_date", date_to.isoformat())

            query = (
                query
                .order("expense_date", desc=True)
                .range(offset, offset + limit - 1)
            )

            response = query.execute()
            expenses = self._extract_data_list(response, "list_expenses")

            # Get total count from response
            total = response.count if hasattr(response, 'count') and response.count else len(expenses)

            return expenses, total
        except Exception as e:
            self._log_error(
                "list_expenses",
                e,
                company_id=company_id,
                status=status,
                category=category
            )
            return [], 0

    async def get_summary(
        self,
        company_id: str,
        date_from: date | None = None,
        date_to: date | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """
        Get expense summary statistics.

        Args:
            company_id: Company UUID
            date_from: Start date filter
            date_to: End date filter
            category: Filter by category
            status: Filter by status

        Returns:
            Dict with summary statistics
        """
        try:
            query = (
                self._client
                .table("expenses")
                .select("total_amount, net_amount, tax_amount")
                .eq("company_id", company_id)
            )

            if status:
                query = query.eq("status", status)
            if category:
                query = query.eq("expense_category", category)
            if date_from:
                query = query.gte("expense_date", date_from.isoformat())
            if date_to:
                query = query.lte("expense_date", date_to.isoformat())

            response = query.execute()
            expenses = self._extract_data_list(response, "get_expense_summary")

            total_amount = sum(exp.get("total_amount", 0) or 0 for exp in expenses)
            total_net = sum(exp.get("net_amount", 0) or 0 for exp in expenses)
            total_tax = sum(exp.get("tax_amount", 0) or 0 for exp in expenses)

            return {
                "total_count": len(expenses),
                "total_amount": total_amount,
                "total_net": total_net,
                "total_tax": total_tax,
            }
        except Exception as e:
            self._log_error(
                "get_expense_summary",
                e,
                company_id=company_id,
                date_from=date_from,
                date_to=date_to
            )
            return {
                "total_count": 0,
                "total_amount": 0,
                "total_net": 0,
                "total_tax": 0,
            }

    async def get_by_id(self, expense_id: str) -> dict[str, Any] | None:
        """
        Get expense by ID.

        Args:
            expense_id: Expense UUID

        Returns:
            Expense dict or None if not found
        """
        try:
            response = (
                self._client
                .table("expenses")
                .select("*")
                .eq("id", expense_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_expense_by_id")
        except Exception as e:
            self._log_error("get_expense_by_id", e, expense_id=expense_id)
            return None

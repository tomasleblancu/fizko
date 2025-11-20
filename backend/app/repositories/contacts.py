"""
Contacts Repository - Handles all contact-related database queries.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class ContactsRepository(BaseRepository):
    """Repository for contact data access."""

    async def get_by_rut(
        self, company_id: str, rut: str
    ) -> dict[str, Any] | None:
        """
        Get a contact by RUT for a specific company.

        Args:
            company_id: Company UUID
            rut: Contact RUT (Chilean tax ID)

        Returns:
            Contact dict or None if not found
        """
        try:
            response = (
                self._client
                .table("contacts")
                .select("*")
                .eq("company_id", company_id)
                .eq("rut", rut)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_by_rut")
        except Exception as e:
            self._log_error("get_by_rut", e, company_id=company_id, rut=rut)
            return None

    async def get_by_id(self, contact_id: str) -> dict[str, Any] | None:
        """
        Get a contact by ID.

        Args:
            contact_id: Contact UUID

        Returns:
            Contact dict or None if not found
        """
        try:
            response = (
                self._client
                .table("contacts")
                .select("*")
                .eq("id", contact_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_by_id")
        except Exception as e:
            self._log_error("get_by_id", e, contact_id=contact_id)
            return None

    async def get_sales_summary(self, contact_id: str) -> dict[str, Any] | None:
        """
        Get sales summary for a contact (as a client).

        Aggregates total sales amount and document count.

        Args:
            contact_id: Contact UUID

        Returns:
            Dict with total_amount and document_count, or None if error
        """
        try:
            # Use RPC function if available, otherwise aggregate in Python
            response = (
                self._client
                .table("sales_documents")
                .select("total_amount")
                .eq("contact_id", contact_id)
                .execute()
            )

            data = self._extract_data_list(response, "get_sales_summary")
            if not data:
                return {"total_amount": 0, "document_count": 0}

            total_amount = sum(doc.get("total_amount", 0) or 0 for doc in data)
            return {
                "total_amount": total_amount,
                "document_count": len(data)
            }
        except Exception as e:
            self._log_error("get_sales_summary", e, contact_id=contact_id)
            return None

    async def get_purchase_summary(self, contact_id: str) -> dict[str, Any] | None:
        """
        Get purchase summary for a contact (as a provider).

        Aggregates total purchase amount and document count.

        Args:
            contact_id: Contact UUID

        Returns:
            Dict with total_amount and document_count, or None if error
        """
        try:
            response = (
                self._client
                .table("purchase_documents")
                .select("total_amount")
                .eq("contact_id", contact_id)
                .execute()
            )

            data = self._extract_data_list(response, "get_purchase_summary")
            if not data:
                return {"total_amount": 0, "document_count": 0}

            total_amount = sum(doc.get("total_amount", 0) or 0 for doc in data)
            return {
                "total_amount": total_amount,
                "document_count": len(data)
            }
        except Exception as e:
            self._log_error("get_purchase_summary", e, contact_id=contact_id)
            return None

    async def get_top_clients(
        self, company_id: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get top clients by total sales amount.

        Args:
            company_id: Company UUID
            limit: Number of top clients to return

        Returns:
            List of contact dicts with total_sales field
        """
        try:
            # This requires a view or RPC function in Supabase
            # For now, we'll fetch all sales and aggregate in Python
            response = (
                self._client
                .table("sales_documents")
                .select("contact_id, total_amount, contacts!inner(id, name, rut)")
                .eq("contacts.company_id", company_id)
                .execute()
            )

            data = self._extract_data_list(response, "get_top_clients")
            if not data:
                return []

            # Aggregate by contact
            client_totals: dict[str, dict[str, Any]] = {}
            for doc in data:
                contact = doc.get("contacts")
                if not contact:
                    continue

                contact_id = contact.get("id")
                if contact_id not in client_totals:
                    client_totals[contact_id] = {
                        **contact,
                        "total_sales": 0
                    }

                client_totals[contact_id]["total_sales"] += doc.get("total_amount", 0) or 0

            # Sort by total sales and limit
            top_clients = sorted(
                client_totals.values(),
                key=lambda x: x["total_sales"],
                reverse=True
            )[:limit]

            return top_clients
        except Exception as e:
            self._log_error("get_top_clients", e, company_id=company_id, limit=limit)
            return []

    async def get_top_providers(
        self, company_id: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get top providers by total purchase amount.

        Args:
            company_id: Company UUID
            limit: Number of top providers to return

        Returns:
            List of contact dicts with total_purchases field
        """
        try:
            response = (
                self._client
                .table("purchase_documents")
                .select("contact_id, total_amount, contacts!inner(id, name, rut)")
                .eq("contacts.company_id", company_id)
                .execute()
            )

            data = self._extract_data_list(response, "get_top_providers")
            if not data:
                return []

            # Aggregate by contact
            provider_totals: dict[str, dict[str, Any]] = {}
            for doc in data:
                contact = doc.get("contacts")
                if not contact:
                    continue

                contact_id = contact.get("id")
                if contact_id not in provider_totals:
                    provider_totals[contact_id] = {
                        **contact,
                        "total_purchases": 0
                    }

                provider_totals[contact_id]["total_purchases"] += doc.get("total_amount", 0) or 0

            # Sort by total purchases and limit
            top_providers = sorted(
                provider_totals.values(),
                key=lambda x: x["total_purchases"],
                reverse=True
            )[:limit]

            return top_providers
        except Exception as e:
            self._log_error("get_top_providers", e, company_id=company_id, limit=limit)
            return []

    async def upsert_contact(
        self,
        company_id: str,
        rut: str,
        business_name: str,
        contact_type: str
    ) -> dict[str, Any] | None:
        """
        Upsert a contact (insert or update based on company_id + rut).

        Uses the UNIQUE constraint (company_id, rut) to handle upserts.

        Args:
            company_id: Company UUID
            rut: Contact RUT (Chilean tax ID)
            business_name: Business name
            contact_type: Type of contact ('provider', 'client', or 'both')

        Returns:
            Upserted contact dict or None if error
        """
        try:
            contact_data = {
                "company_id": company_id,
                "rut": rut,
                "business_name": business_name,
                "contact_type": contact_type
            }

            response = (
                self._client
                .table("contacts")
                .upsert(
                    contact_data,
                    on_conflict="company_id,rut"
                )
                .execute()
            )

            result = self._extract_data(response, "upsert_contact")
            if result:
                logger.debug(f"✅ Upserted contact: {business_name} ({rut})")
            return result
        except Exception as e:
            self._log_error(
                "upsert_contact",
                e,
                company_id=company_id,
                rut=rut,
                business_name=business_name
            )
            return None

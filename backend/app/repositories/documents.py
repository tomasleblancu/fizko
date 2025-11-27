"""
Documents Repository - Handles sales and purchase document queries.
"""

import logging
from typing import Any, Literal

from .base import BaseRepository

logger = logging.getLogger(__name__)


class DocumentsRepository(BaseRepository):
    """Repository for sales and purchase document data access."""

    async def get_sales_document(
        self, document_id: str, include_contact: bool = True
    ) -> dict[str, Any] | None:
        """
        Get a sales document by ID.

        Args:
            document_id: Sales document UUID
            include_contact: Whether to include related contact data

        Returns:
            Sales document dict or None if not found
        """
        try:
            select_query = "*"
            if include_contact:
                select_query = "*, contacts(*)"

            response = (
                self._client
                .table("sales_documents")
                .select(select_query)
                .eq("id", document_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_sales_document")
        except Exception as e:
            self._log_error("get_sales_document", e, document_id=document_id)
            return None

    async def get_purchase_document(
        self, document_id: str, include_contact: bool = True
    ) -> dict[str, Any] | None:
        """
        Get a purchase document by ID.

        Args:
            document_id: Purchase document UUID
            include_contact: Whether to include related contact data

        Returns:
            Purchase document dict or None if not found
        """
        try:
            select_query = "*"
            if include_contact:
                select_query = "*, contacts(*)"

            response = (
                self._client
                .table("purchase_documents")
                .select(select_query)
                .eq("id", document_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_purchase_document")
        except Exception as e:
            self._log_error("get_purchase_document", e, document_id=document_id)
            return None

    async def get_documents_by_type(
        self,
        company_id: str,
        document_type: Literal["sales", "purchase"],
        tipo_dte: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get documents by type and optional DTE type.

        Args:
            company_id: Company UUID
            document_type: Either "sales" or "purchase"
            tipo_dte: Optional DTE type filter (e.g., "33" for electronic invoice)
            limit: Maximum number of documents to return

        Returns:
            List of document dicts
        """
        try:
            table = "sales_documents" if document_type == "sales" else "purchase_documents"

            query = (
                self._client
                .table(table)
                .select("*, contacts(*)")
                .eq("company_id", company_id)
            )

            if tipo_dte:
                query = query.eq("tipo_dte", tipo_dte)

            query = query.order("emission_date", desc=True).limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "get_documents_by_type")
        except Exception as e:
            self._log_error(
                "get_documents_by_type",
                e,
                company_id=company_id,
                document_type=document_type,
                tipo_dte=tipo_dte
            )
            return []

    async def get_recent_sales(
        self, company_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get recent sales documents.

        Args:
            company_id: Company UUID
            limit: Number of documents to return

        Returns:
            List of recent sales documents
        """
        try:
            response = (
                self._client
                .table("sales_documents")
                .select("*, contacts(*)")
                .eq("company_id", company_id)
                .order("emission_date", desc=True)
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_recent_sales")
        except Exception as e:
            self._log_error("get_recent_sales", e, company_id=company_id, limit=limit)
            return []

    async def get_recent_purchases(
        self, company_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get recent purchase documents.

        Args:
            company_id: Company UUID
            limit: Number of documents to return

        Returns:
            List of recent purchase documents
        """
        try:
            response = (
                self._client
                .table("purchase_documents")
                .select("*, contacts(*)")
                .eq("company_id", company_id)
                .order("emission_date", desc=True)
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_recent_purchases")
        except Exception as e:
            self._log_error("get_recent_purchases", e, company_id=company_id, limit=limit)
            return []

    async def get_sales_by_contact(
        self, contact_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get sales documents for a specific contact.

        Args:
            contact_id: Contact UUID
            limit: Maximum number of documents

        Returns:
            List of sales documents
        """
        try:
            response = (
                self._client
                .table("sales_documents")
                .select("*")
                .eq("contact_id", contact_id)
                .order("emission_date", desc=True)
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_sales_by_contact")
        except Exception as e:
            self._log_error("get_sales_by_contact", e, contact_id=contact_id)
            return []

    async def get_purchases_by_contact(
        self, contact_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get purchase documents for a specific contact.

        Args:
            contact_id: Contact UUID
            limit: Maximum number of documents

        Returns:
            List of purchase documents
        """
        try:
            response = (
                self._client
                .table("purchase_documents")
                .select("*")
                .eq("contact_id", contact_id)
                .order("emission_date", desc=True)
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_purchases_by_contact")
        except Exception as e:
            self._log_error("get_purchases_by_contact", e, contact_id=contact_id)
            return []

    async def search_documents(
        self,
        company_id: str,
        document_type: str = "both",
        rut: str | None = None,
        folio: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 20
    ) -> dict[str, Any]:
        """
        Advanced search for documents with multiple filters.

        Args:
            company_id: Company UUID
            document_type: "sales", "purchases", or "both"
            rut: Filter by RUT (sender for purchases, receiver for sales)
            folio: Filter by folio number
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            limit: Maximum documents per type

        Returns:
            Dict with sales_documents and purchase_documents lists
        """
        result = {
            "sales_documents": [],
            "purchase_documents": []
        }

        try:
            # Search purchases
            if document_type in ["purchases", "both"]:
                query = (
                    self._client
                    .table("purchase_documents")
                    .select("*, contacts(*)")
                    .eq("company_id", company_id)
                )

                if rut:
                    query = query.eq("sender_rut", rut)
                if folio:
                    query = query.eq("folio", folio)
                if start_date:
                    query = query.gte("issue_date", start_date)
                if end_date:
                    query = query.lte("issue_date", end_date)

                query = query.order("issue_date", desc=True).limit(limit)
                response = query.execute()
                result["purchase_documents"] = self._extract_data_list(response, "search_purchases")

            # Search sales
            if document_type in ["sales", "both"]:
                query = (
                    self._client
                    .table("sales_documents")
                    .select("*, contacts(*)")
                    .eq("company_id", company_id)
                )

                if rut:
                    query = query.eq("recipient_rut", rut)
                if folio:
                    query = query.eq("folio", folio)
                if start_date:
                    query = query.gte("issue_date", start_date)
                if end_date:
                    query = query.lte("issue_date", end_date)

                query = query.order("issue_date", desc=True).limit(limit)
                response = query.execute()
                result["sales_documents"] = self._extract_data_list(response, "search_sales")

        except Exception as e:
            self._log_error(
                "search_documents",
                e,
                company_id=company_id,
                document_type=document_type,
                rut=rut,
                folio=folio
            )

        return result

    async def upsert_purchase_documents(
        self, documents: list[dict[str, Any]]
    ) -> tuple[int, int]:
        """
        Upsert purchase documents (insert or update based on company_id + folio + sender_rut).

        Args:
            documents: List of purchase documents to upsert

        Returns:
            Tuple of (newly_created_count, updated_count)
        """
        if not documents:
            return 0, 0

        try:
            # Get existing documents to count new vs updated
            company_id = documents[0]["company_id"]

            # Build list of (folio, sender_rut) tuples for matching
            doc_keys = [(doc["folio"], doc.get("sender_rut")) for doc in documents if doc.get("folio") is not None]

            existing_keys = set()
            if doc_keys:
                # Get all purchase documents for this company with matching folios
                folios = [key[0] for key in doc_keys]
                response = (
                    self._client
                    .table("purchase_documents")
                    .select("folio,sender_rut")
                    .eq("company_id", company_id)
                    .in_("folio", folios)
                    .execute()
                )
                existing_keys = {(doc["folio"], doc.get("sender_rut")) for doc in response.data}

            # Count new vs updated based on (folio, sender_rut) combination
            nuevos = sum(1 for doc in documents if (doc.get("folio"), doc.get("sender_rut")) not in existing_keys)
            actualizados = len(documents) - nuevos

            # Supabase upsert (inserts or updates based on unique constraint)
            # Note: Unique constraint is now (company_id, folio, sender_rut)
            response = (
                self._client
                .table("purchase_documents")
                .upsert(documents, on_conflict="company_id,folio,sender_rut")
                .execute()
            )

            logger.info(
                f"✅ Upserted {len(documents)} purchase documents: "
                f"{nuevos} nuevos, {actualizados} actualizados"
            )
            return nuevos, actualizados

        except Exception as e:
            self._log_error("upsert_purchase_documents", e, count=len(documents))
            return 0, 0

    async def upsert_sales_documents(
        self, documents: list[dict[str, Any]]
    ) -> tuple[int, int]:
        """
        Upsert sales documents (insert or update based on company_id + folio).

        Args:
            documents: List of sales documents to upsert

        Returns:
            Tuple of (newly_created_count, updated_count)
        """
        if not documents:
            return 0, 0

        try:
            # Get existing folios to count new vs updated
            company_id = documents[0]["company_id"]
            folios = [doc["folio"] for doc in documents if doc.get("folio") is not None]

            existing_folios = set()
            if folios:
                response = (
                    self._client
                    .table("sales_documents")
                    .select("folio")
                    .eq("company_id", company_id)
                    .in_("folio", folios)
                    .execute()
                )
                existing_folios = {doc["folio"] for doc in response.data}

            # Count new vs updated
            nuevos = sum(1 for doc in documents if doc.get("folio") not in existing_folios)
            actualizados = len(documents) - nuevos

            # Supabase upsert (inserts or updates based on unique constraint)
            response = (
                self._client
                .table("sales_documents")
                .upsert(documents, on_conflict="company_id,folio")
                .execute()
            )

            logger.info(
                f"✅ Upserted {len(documents)} sales documents: "
                f"{nuevos} nuevos, {actualizados} actualizados"
            )
            return nuevos, actualizados

        except Exception as e:
            self._log_error("upsert_sales_documents", e, count=len(documents))
            return 0, 0

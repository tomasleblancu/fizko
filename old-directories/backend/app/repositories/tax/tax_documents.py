"""Composite repository for unified tax document access."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.tax.purchase_documents import PurchaseDocumentRepository
from app.repositories.tax.sales_documents import SalesDocumentRepository
from app.repositories.tax.honorarios import HonorariosRepository


class TaxDocumentRepository:
    """
    Composite repository for unified access to all tax documents.

    Combines PurchaseDocument, SalesDocument, and HonorariosReceipt into a unified view.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.purchases = PurchaseDocumentRepository(db)
        self.sales = SalesDocumentRepository(db)
        self.honorarios = HonorariosRepository(db)

    async def get_all_documents(
        self,
        company_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10,
        offset: int = 0,
        contact_rut: Optional[str] = None
    ) -> List[dict]:
        """
        Get all tax documents (purchases + sales + honorarios) unified and sorted.

        Args:
            company_id: Company UUID
            start_date: Filter by date >= start_date
            end_date: Filter by date <= end_date
            limit: Max total results
            offset: Number of documents to skip (for pagination)
            contact_rut: Filter by contact RUT (sender for purchases, recipient for sales)

        Returns:
            List of unified document dictionaries
        """
        # Get purchases (fetch all, pagination happens after merge+sort)
        purchases = await self.purchases.find_by_company(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            limit=None,  # Fetch all to enable proper pagination after sorting
            sender_rut=contact_rut  # Filter by provider RUT
        )

        # Get sales (fetch all, pagination happens after merge+sort)
        sales = await self.sales.find_by_company(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            limit=None,  # Fetch all to enable proper pagination after sorting
            recipient_rut=contact_rut  # Filter by client RUT
        )

        # Get honorarios (fetch all, pagination happens after merge+sort)
        honorarios = await self.honorarios.find_by_company(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            limit=None,  # Fetch all to enable proper pagination after sorting
            issuer_rut=contact_rut  # Filter by issuer RUT
        )

        # Transform to unified format
        all_docs = []

        for doc in purchases:
            all_docs.append({
                'id': str(doc.id),
                'company_id': str(doc.company_id),
                'document_type': doc.document_type,
                'document_number': str(doc.folio) if doc.folio else 'N/A',
                'issue_date': doc.issue_date.isoformat(),
                'amount': float(doc.total_amount),
                'tax_amount': float(doc.tax_amount),
                'status': doc.status,
                'description': f"Purchase: {doc.sender_name or 'Unknown'}",
                'created_at': doc.created_at.isoformat(),
                'source': 'purchase'
            })

        for doc in sales:
            all_docs.append({
                'id': str(doc.id),
                'company_id': str(doc.company_id),
                'document_type': doc.document_type,
                'document_number': str(doc.folio) if doc.folio else 'N/A',
                'issue_date': doc.issue_date.isoformat(),
                'amount': float(doc.total_amount),
                'tax_amount': float(doc.tax_amount),
                'status': doc.status,
                'description': f"Sale: {doc.recipient_name or 'Unknown'}",
                'created_at': doc.created_at.isoformat(),
                'source': 'sale'
            })

        # Add honorarios - formatted like purchases (professional fee payments)
        for doc in honorarios:
            # Determine issuer/provider name based on receipt type
            if doc.receipt_type == 'received':
                # Company received the service (paid to provider)
                # Use emission_user as fallback when issuer_name is not available
                provider_name = doc.issuer_name or doc.emission_user or 'Proveedor desconocido'
                doc_type = 'boleta_honorarios_recibida'
                # Amounts are NEGATIVE for received (expenses)
                amount_sign = -1
            else:
                # Company issued the service (received payment)
                provider_name = doc.recipient_name or doc.emission_user or 'Cliente desconocido'
                doc_type = 'boleta_honorarios_emitida'
                # Amounts are POSITIVE for issued (income)
                amount_sign = 1

            all_docs.append({
                'id': str(doc.id),
                'company_id': str(doc.company_id),
                'document_type': doc_type,
                'document_number': str(doc.folio) if doc.folio else 'N/A',
                'issue_date': doc.issue_date.isoformat(),
                'amount': float(doc.gross_amount) * amount_sign,  # Negative for received, positive for issued
                'tax_amount': float(doc.recipient_retention) * amount_sign,  # Negative for received, positive for issued
                'status': doc.status,
                'description': f"Honorarios: {provider_name}",
                'created_at': doc.created_at.isoformat(),
                'source': 'honorarios',
                # Additional honorarios-specific fields
                'net_amount': float(doc.net_amount) * amount_sign,
                'retention_amount': float(doc.recipient_retention) * amount_sign,
                'receipt_type': doc.receipt_type
            })

        # Sort by issue date descending
        all_docs.sort(key=lambda x: x['issue_date'], reverse=True)

        # Apply offset and limit for pagination
        return all_docs[offset:offset + limit]

    async def get_period_summary(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> dict:
        """
        Get summary of all tax activity for a period.

        Args:
            company_id: Company UUID
            start_date: Period start
            end_date: Period end

        Returns:
            Dictionary with summary data
        """
        purchases_totals = await self.purchases.get_period_totals(
            company_id, start_date, end_date
        )

        sales_totals = await self.sales.get_period_totals(
            company_id, start_date, end_date
        )

        honorarios_totals = await self.honorarios.get_period_totals(
            company_id, start_date, end_date
        )

        return {
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'purchases': purchases_totals,
            'sales': sales_totals,
            'honorarios': honorarios_totals,
            'net_iva': sales_totals['tax_amount'] - purchases_totals['tax_amount'],
            'total_documents': (
                purchases_totals['document_count'] +
                sales_totals['document_count'] +
                honorarios_totals['document_count']
            )
        }

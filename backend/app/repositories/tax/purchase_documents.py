"""Repository for purchase document management."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.documents import PurchaseDocument
from app.repositories.base import BaseRepository


class PurchaseDocumentRepository(BaseRepository[PurchaseDocument]):
    """Repository for managing purchase documents (documentos de compra)."""

    def __init__(self, db: AsyncSession):
        super().__init__(PurchaseDocument, db)

    async def find_by_company(
        self,
        company_id: UUID,
        document_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[PurchaseDocument]:
        """
        Find purchase documents by company with filters.

        Args:
            company_id: Company UUID
            document_type: Filter by document type
            start_date: Filter by issue date >= start_date
            end_date: Filter by issue date <= end_date
            status: Filter by status
            skip: Pagination offset
            limit: Max results

        Returns:
            List of PurchaseDocument instances
        """
        query = select(PurchaseDocument).where(
            PurchaseDocument.company_id == company_id
        )

        if document_type:
            query = query.where(PurchaseDocument.document_type == document_type)

        if start_date:
            query = query.where(PurchaseDocument.issue_date >= start_date)

        if end_date:
            query = query.where(PurchaseDocument.issue_date <= end_date)

        if status:
            query = query.where(PurchaseDocument.status == status)

        query = query.order_by(desc(PurchaseDocument.issue_date))
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_period_totals(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date
    ) -> dict:
        """
        Get aggregated totals for a period.

        Args:
            company_id: Company UUID
            start_date: Period start
            end_date: Period end

        Returns:
            Dictionary with totals
        """
        query = select(
            func.sum(PurchaseDocument.total_amount).label('total'),
            func.sum(PurchaseDocument.net_amount).label('net'),
            func.sum(PurchaseDocument.tax_amount).label('tax'),
            func.count(PurchaseDocument.id).label('count')
        ).where(
            and_(
                PurchaseDocument.company_id == company_id,
                PurchaseDocument.issue_date >= start_date,
                PurchaseDocument.issue_date <= end_date
            )
        )

        result = await self.db.execute(query)
        row = result.one()

        return {
            'total_amount': float(row.total or 0),
            'net_amount': float(row.net or 0),
            'tax_amount': float(row.tax or 0),
            'document_count': row.count or 0
        }

"""Repository for sales document management."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.documents import SalesDocument
from app.repositories.base import BaseRepository


class SalesDocumentRepository(BaseRepository[SalesDocument]):
    """Repository for managing sales documents (documentos de venta)."""

    def __init__(self, db: AsyncSession):
        super().__init__(SalesDocument, db)

    async def find_by_company(
        self,
        company_id: UUID,
        document_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[SalesDocument]:
        """
        Find sales documents by company with filters.

        Args:
            company_id: Company UUID
            document_type: Filter by document type
            start_date: Filter by issue date >= start_date
            end_date: Filter by issue date <= end_date
            status: Filter by status
            skip: Pagination offset
            limit: Max results

        Returns:
            List of SalesDocument instances
        """
        query = select(SalesDocument).where(
            SalesDocument.company_id == company_id
        )

        if document_type:
            query = query.where(SalesDocument.document_type == document_type)

        if start_date:
            query = query.where(SalesDocument.issue_date >= start_date)

        if end_date:
            query = query.where(SalesDocument.issue_date <= end_date)

        if status:
            query = query.where(SalesDocument.status == status)

        query = query.order_by(desc(SalesDocument.issue_date))
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
            func.sum(SalesDocument.total_amount).label('total'),
            func.sum(SalesDocument.net_amount).label('net'),
            func.sum(SalesDocument.tax_amount).label('tax'),
            func.count(SalesDocument.id).label('count')
        ).where(
            and_(
                SalesDocument.company_id == company_id,
                SalesDocument.issue_date >= start_date,
                SalesDocument.issue_date <= end_date
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

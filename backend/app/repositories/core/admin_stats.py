"""Repository for admin statistics and aggregations."""

from typing import List, Optional, NamedTuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    PurchaseDocument,
    SalesDocument,
    Form29SIIDownload,
    CalendarEvent,
    NotificationHistory,
)


class DocumentStats(NamedTuple):
    """Document statistics for a company."""
    total_purchase_documents: int
    total_sales_documents: int
    latest_purchase_date: Optional[datetime]
    latest_sales_date: Optional[datetime]
    total_purchase_amount: float
    total_sales_amount: float


class DocumentCounts(NamedTuple):
    """Document counts for batch operations."""
    company_id: UUID
    purchase_count: int
    sales_count: int


class AdminStatsRepository:
    """Repository for admin-level statistics and aggregations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_document_stats(self, company_id: UUID) -> DocumentStats:
        """
        Get document statistics for a company.

        Args:
            company_id: Company UUID

        Returns:
            DocumentStats with purchase and sales aggregations
        """
        # Purchase stats
        purchase_stats_stmt = select(
            func.count(PurchaseDocument.id).label('count'),
            func.max(PurchaseDocument.created_at).label('latest'),
            func.sum(PurchaseDocument.total_amount).label('total')
        ).where(PurchaseDocument.company_id == company_id)

        # Sales stats
        sales_stats_stmt = select(
            func.count(SalesDocument.id).label('count'),
            func.max(SalesDocument.created_at).label('latest'),
            func.sum(SalesDocument.total_amount).label('total')
        ).where(SalesDocument.company_id == company_id)

        # Execute both queries
        purchase_result = await self.db.execute(purchase_stats_stmt)
        sales_result = await self.db.execute(sales_stats_stmt)

        purchase_stats = purchase_result.one()
        sales_stats = sales_result.one()

        return DocumentStats(
            total_purchase_documents=purchase_stats.count or 0,
            total_sales_documents=sales_stats.count or 0,
            latest_purchase_date=purchase_stats.latest,
            latest_sales_date=sales_stats.latest,
            total_purchase_amount=float(purchase_stats.total or 0),
            total_sales_amount=float(sales_stats.total or 0)
        )

    async def get_document_counts_batch(
        self,
        company_ids: List[UUID]
    ) -> dict[UUID, DocumentCounts]:
        """
        Get document counts for multiple companies in batch.

        Args:
            company_ids: List of company UUIDs

        Returns:
            Dictionary mapping company_id to DocumentCounts
        """
        # Purchase counts
        purchase_count_stmt = (
            select(
                PurchaseDocument.company_id,
                func.count(PurchaseDocument.id).label('purchase_count')
            )
            .where(PurchaseDocument.company_id.in_(company_ids))
            .group_by(PurchaseDocument.company_id)
        )

        # Sales counts
        sales_count_stmt = (
            select(
                SalesDocument.company_id,
                func.count(SalesDocument.id).label('sales_count')
            )
            .where(SalesDocument.company_id.in_(company_ids))
            .group_by(SalesDocument.company_id)
        )

        # Execute both queries
        purchase_result = await self.db.execute(purchase_count_stmt)
        sales_result = await self.db.execute(sales_count_stmt)

        # Build maps
        purchase_map = {row.company_id: row.purchase_count for row in purchase_result.all()}
        sales_map = {row.company_id: row.sales_count for row in sales_result.all()}

        # Combine results
        result = {}
        for company_id in company_ids:
            result[company_id] = DocumentCounts(
                company_id=company_id,
                purchase_count=purchase_map.get(company_id, 0),
                sales_count=sales_map.get(company_id, 0)
            )

        return result

    async def count_entities_for_deletion(
        self,
        company_id: UUID
    ) -> dict[str, int]:
        """
        Count all entities related to a company before deletion.

        Args:
            company_id: Company UUID

        Returns:
            Dictionary with counts for each entity type
        """
        # Count purchases
        purchases_stmt = select(func.count(PurchaseDocument.id)).where(
            PurchaseDocument.company_id == company_id
        )
        purchases_count = (await self.db.execute(purchases_stmt)).scalar() or 0

        # Count sales
        sales_stmt = select(func.count(SalesDocument.id)).where(
            SalesDocument.company_id == company_id
        )
        sales_count = (await self.db.execute(sales_stmt)).scalar() or 0

        # Count F29
        f29_stmt = select(func.count(Form29SIIDownload.id)).where(
            Form29SIIDownload.company_id == company_id
        )
        f29_count = (await self.db.execute(f29_stmt)).scalar() or 0

        # Count calendar events
        calendar_stmt = select(func.count(CalendarEvent.id)).where(
            CalendarEvent.company_id == company_id
        )
        calendar_count = (await self.db.execute(calendar_stmt)).scalar() or 0

        # Count notifications
        notifications_stmt = select(func.count(NotificationHistory.id)).where(
            NotificationHistory.company_id == company_id
        )
        notifications_count = (await self.db.execute(notifications_stmt)).scalar() or 0

        return {
            "purchase_documents_deleted": purchases_count,
            "sales_documents_deleted": sales_count,
            "f29_forms_deleted": f29_count,
            "calendar_events_deleted": calendar_count,
            "notifications_deleted": notifications_count,
        }

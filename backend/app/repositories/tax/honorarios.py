"""Repository for honorarios receipts management."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.honorarios import HonorariosReceipt
from app.repositories.base import BaseRepository


class HonorariosRepository(BaseRepository[HonorariosReceipt]):
    """Repository for managing honorarios receipts (boletas de honorarios)."""

    def __init__(self, db: AsyncSession):
        super().__init__(HonorariosReceipt, db)

    async def find_by_company(
        self,
        company_id: UUID,
        receipt_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        issuer_rut: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[HonorariosReceipt]:
        """
        Find honorarios receipts by company with filters.

        Args:
            company_id: Company UUID
            receipt_type: Filter by receipt type ('received' or 'issued')
            start_date: Filter by issue date >= start_date
            end_date: Filter by issue date <= end_date
            status: Filter by status
            issuer_rut: Filter by issuer RUT (professional providing the service)
            skip: Pagination offset
            limit: Max results

        Returns:
            List of HonorariosReceipt instances
        """
        query = select(HonorariosReceipt).where(
            HonorariosReceipt.company_id == company_id
        )

        if receipt_type:
            query = query.where(HonorariosReceipt.receipt_type == receipt_type)

        if start_date:
            query = query.where(HonorariosReceipt.issue_date >= start_date)

        if end_date:
            query = query.where(HonorariosReceipt.issue_date <= end_date)

        if status:
            query = query.where(HonorariosReceipt.status == status)

        if issuer_rut:
            query = query.where(HonorariosReceipt.issuer_rut == issuer_rut)

        query = query.order_by(desc(HonorariosReceipt.issue_date))
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_period_totals(
        self,
        company_id: UUID,
        start_date: date,
        end_date: date,
        receipt_type: Optional[str] = None
    ) -> dict:
        """
        Get aggregated totals for a period.

        Args:
            company_id: Company UUID
            start_date: Period start
            end_date: Period end
            receipt_type: Optional filter by receipt type

        Returns:
            Dictionary with totals
        """
        conditions = [
            HonorariosReceipt.company_id == company_id,
            HonorariosReceipt.issue_date >= start_date,
            HonorariosReceipt.issue_date <= end_date
        ]

        if receipt_type:
            conditions.append(HonorariosReceipt.receipt_type == receipt_type)

        query = select(
            func.sum(HonorariosReceipt.gross_amount).label('gross'),
            func.sum(HonorariosReceipt.net_amount).label('net'),
            func.sum(HonorariosReceipt.recipient_retention).label('retention'),
            func.count(HonorariosReceipt.id).label('count')
        ).where(and_(*conditions))

        result = await self.db.execute(query)
        row = result.one()

        return {
            'gross_amount': float(row.gross or 0),
            'net_amount': float(row.net or 0),
            'retention_amount': float(row.retention or 0),
            'document_count': row.count or 0
        }

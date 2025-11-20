"""Repository for Form29 SII Download management."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Form29SIIDownload
from app.repositories.base import BaseRepository


class Form29SIIDownloadRepository(BaseRepository[Form29SIIDownload]):
    """Repository for managing Form29 SII Downloads."""

    def __init__(self, db: AsyncSession):
        super().__init__(Form29SIIDownload, db)

    async def find_by_company(
        self,
        company_id: UUID,
        year: Optional[int] = None,
        status_filter: Optional[str] = None
    ) -> List[Form29SIIDownload]:
        """
        Get F29 forms for a company with optional filters.

        Args:
            company_id: Company UUID
            year: Optional year filter
            status_filter: Optional status filter (Vigente, Rectificado, Anulado)

        Returns:
            List of Form29SIIDownload instances ordered by period
        """
        stmt = select(Form29SIIDownload).where(
            Form29SIIDownload.company_id == company_id
        ).order_by(
            desc(Form29SIIDownload.period_year),
            desc(Form29SIIDownload.period_month)
        )

        # Apply filters
        if year:
            stmt = stmt.where(Form29SIIDownload.period_year == year)

        if status_filter:
            stmt = stmt.where(Form29SIIDownload.status == status_filter)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

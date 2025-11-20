"""
CompanySettings Repository Pattern Implementation.

Provides data access for company business configuration settings.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BaseRepository
from ...db.models import CompanySettings


class CompanySettingsRepository(BaseRepository[CompanySettings]):
    """
    Repository for CompanySettings model operations.

    Provides methods to manage company business configuration like
    employees, imports, exports, and lease contracts.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize CompanySettings repository.

        Args:
            db: Async database session
        """
        super().__init__(CompanySettings, db)

    async def get_by_company(self, company_id: UUID) -> Optional[CompanySettings]:
        """
        Get settings for a specific company.

        Args:
            company_id: Company UUID

        Returns:
            CompanySettings instance or None if not found
        """
        stmt = select(CompanySettings).where(
            CompanySettings.company_id == company_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        company_id: UUID,
        **settings_data
    ) -> CompanySettings:
        """
        Create or update settings for a company.

        Args:
            company_id: Company UUID
            **settings_data: Settings fields to update

        Returns:
            CompanySettings instance (created or updated)
        """
        # Check if settings exist
        existing = await self.get_by_company(company_id)

        if existing:
            # Update existing settings
            for field, value in settings_data.items():
                if hasattr(existing, field):
                    setattr(existing, field, value)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new settings
            settings = CompanySettings(
                company_id=company_id,
                **settings_data
            )
            self.db.add(settings)
            await self.db.flush()
            await self.db.refresh(settings)
            return settings

"""Repository for calendar and event template management."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EventTemplate
from app.repositories.base import BaseRepository


class EventTemplateRepository(BaseRepository[EventTemplate]):
    """Repository for managing event templates."""

    def __init__(self, db: AsyncSession):
        super().__init__(EventTemplate, db)

    async def find_mandatory(self) -> List[EventTemplate]:
        """
        Find all mandatory event templates.

        Returns:
            List of mandatory EventTemplate instances
        """
        result = await self.db.execute(
            select(EventTemplate).where(EventTemplate.is_mandatory == True)
        )
        return list(result.scalars().all())

    async def find_by_code(self, code: str) -> Optional[EventTemplate]:
        """
        Find an event template by code.

        Args:
            code: Template code

        Returns:
            EventTemplate instance or None if not found
        """
        result = await self.db.execute(
            select(EventTemplate).where(EventTemplate.code == code)
        )
        return result.scalar_one_or_none()

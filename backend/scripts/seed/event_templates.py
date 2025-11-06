"""
Seeder for event_templates table.

Syncs event templates (calendar/tax event types) between environments.
Preserves template configurations for tax obligations like F29, F22, etc.
"""
import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseSeeder

logger = logging.getLogger(__name__)


class EventTemplateSeeder(BaseSeeder):
    """Seeder for event_templates table."""

    def get_entity_name(self) -> str:
        return "event_templates"

    async def fetch_source_data(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Fetch event templates from source."""
        query = text("""
            SELECT
                id,
                code,
                name,
                description,
                category,
                authority,
                is_mandatory,
                default_recurrence,
                metadata,
                created_at,
                updated_at
            FROM event_templates
            ORDER BY code
        """)

        result = await session.execute(query)
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def fetch_target_data(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Fetch event templates from target."""
        return await self.fetch_source_data(session)

    def get_unique_key(self, record: Dict[str, Any]) -> str:
        """Use 'code' as unique identifier."""
        return record["code"]

    async def create_record(
        self, session: AsyncSession, record: Dict[str, Any]
    ) -> None:
        """Create a new event template."""
        # Remove id and timestamps - let DB generate them
        insert_data = {k: v for k, v in record.items() if k not in ["id", "created_at", "updated_at"]}

        query = text("""
            INSERT INTO event_templates (
                code,
                name,
                description,
                category,
                authority,
                is_mandatory,
                default_recurrence,
                metadata
            ) VALUES (
                :code,
                :name,
                :description,
                :category,
                :authority,
                :is_mandatory,
                :default_recurrence,
                :metadata
            )
        """)

        await session.execute(query, insert_data)

    async def update_record(
        self,
        session: AsyncSession,
        existing_id: UUID,
        source_record: Dict[str, Any],
    ) -> None:
        """Update an existing event template."""
        # Don't update id, created_at, or code (unique key)
        update_data = {
            k: v for k, v in source_record.items()
            if k not in ["id", "created_at", "code"]
        }
        update_data["existing_id"] = existing_id

        query = text("""
            UPDATE event_templates
            SET
                name = :name,
                description = :description,
                category = :category,
                authority = :authority,
                is_mandatory = :is_mandatory,
                default_recurrence = :default_recurrence,
                metadata = :metadata,
                updated_at = NOW()
            WHERE id = :existing_id
        """)

        await session.execute(query, update_data)

    def should_update(
        self, source_record: Dict[str, Any], target_record: Dict[str, Any]
    ) -> bool:
        """
        Determine if event template should be updated.

        We always update if source has newer timestamp OR if content differs.
        """
        # Check timestamp first
        if super().should_update(source_record, target_record):
            return True

        # Compare critical fields for changes
        fields_to_compare = [
            "name",
            "description",
            "category",
            "authority",
            "is_mandatory",
            "default_recurrence",
            "metadata",
        ]

        for field in fields_to_compare:
            if source_record.get(field) != target_record.get(field):
                if self.verbose:
                    logger.info(
                        f"   Field '{field}' differs for {self.get_unique_key(source_record)}"
                    )
                return True

        return False

"""
Seeder for notification_templates table.

Syncs notification templates between environments while preserving:
- Template code (unique identifier)
- Message content and timing configuration
- WhatsApp template integration settings
- Auto-assignment flags
"""
import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseSeeder

logger = logging.getLogger(__name__)


class NotificationTemplateSeeder(BaseSeeder):
    """Seeder for notification_templates table."""

    def get_entity_name(self) -> str:
        return "notification_templates"

    async def fetch_source_data(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Fetch notification templates from source."""
        query = text("""
            SELECT
                id,
                code,
                name,
                description,
                category,
                entity_type,
                message_template,
                timing_config,
                priority,
                can_repeat,
                max_repeats,
                repeat_interval_hours,
                send_conditions,
                is_active,
                auto_assign_to_new_companies,
                extra_metadata,
                whatsapp_template_id,
                created_at,
                updated_at
            FROM notification_templates
            ORDER BY code
        """)

        result = await session.execute(query)
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def fetch_target_data(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Fetch notification templates from target."""
        return await self.fetch_source_data(session)

    def get_unique_key(self, record: Dict[str, Any]) -> str:
        """Use 'code' as unique identifier."""
        return record["code"]

    async def create_record(
        self, session: AsyncSession, record: Dict[str, Any]
    ) -> None:
        """Create a new notification template."""
        # Remove id and timestamps - let DB generate them
        insert_data = {k: v for k, v in record.items() if k not in ["id", "created_at", "updated_at"]}

        query = text("""
            INSERT INTO notification_templates (
                code,
                name,
                description,
                category,
                entity_type,
                message_template,
                timing_config,
                priority,
                can_repeat,
                max_repeats,
                repeat_interval_hours,
                send_conditions,
                is_active,
                auto_assign_to_new_companies,
                extra_metadata,
                whatsapp_template_id
            ) VALUES (
                :code,
                :name,
                :description,
                :category,
                :entity_type,
                :message_template,
                :timing_config,
                :priority,
                :can_repeat,
                :max_repeats,
                :repeat_interval_hours,
                :send_conditions,
                :is_active,
                :auto_assign_to_new_companies,
                :extra_metadata,
                :whatsapp_template_id
            )
        """)

        await session.execute(query, insert_data)

    async def update_record(
        self,
        session: AsyncSession,
        existing_id: UUID,
        source_record: Dict[str, Any],
    ) -> None:
        """Update an existing notification template."""
        # Don't update id, created_at, or code (unique key)
        update_data = {
            k: v for k, v in source_record.items()
            if k not in ["id", "created_at", "code"]
        }
        update_data["existing_id"] = existing_id

        query = text("""
            UPDATE notification_templates
            SET
                name = :name,
                description = :description,
                category = :category,
                entity_type = :entity_type,
                message_template = :message_template,
                timing_config = :timing_config,
                priority = :priority,
                can_repeat = :can_repeat,
                max_repeats = :max_repeats,
                repeat_interval_hours = :repeat_interval_hours,
                send_conditions = :send_conditions,
                is_active = :is_active,
                auto_assign_to_new_companies = :auto_assign_to_new_companies,
                extra_metadata = :extra_metadata,
                whatsapp_template_id = :whatsapp_template_id,
                updated_at = NOW()
            WHERE id = :existing_id
        """)

        await session.execute(query, update_data)

    def should_update(
        self, source_record: Dict[str, Any], target_record: Dict[str, Any]
    ) -> bool:
        """
        Determine if template should be updated.

        We always update if source has newer timestamp OR if content differs.
        """
        # Check timestamp first
        if super().should_update(source_record, target_record):
            return True

        # Compare critical fields for changes
        fields_to_compare = [
            "name",
            "description",
            "message_template",
            "timing_config",
            "is_active",
            "auto_assign_to_new_companies",
            "whatsapp_template_id",
            "extra_metadata",
        ]

        for field in fields_to_compare:
            if source_record.get(field) != target_record.get(field):
                if self.verbose:
                    logger.info(
                        f"   Field '{field}' differs for {self.get_unique_key(source_record)}"
                    )
                return True

        return False

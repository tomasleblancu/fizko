"""
History service for notifications
Handles notification history and analytics
"""
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationHistory
from .base_service import BaseNotificationService

logger = logging.getLogger(__name__)


class HistoryService(BaseNotificationService):
    """
    Service for managing notification history.
    Handles querying and analytics of sent notifications.
    """

    async def get_notification_history(
        self,
        db: AsyncSession,
        company_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[NotificationHistory]:
        """
        Get notification history with filters.

        Args:
            db: Database session
            company_id: Filter by company
            user_id: Filter by user
            entity_type: Filter by entity type
            entity_id: Filter by specific entity
            status: Filter by status
            limit: Result limit

        Returns:
            List of notification history records
        """
        query = select(NotificationHistory)

        if company_id:
            query = query.where(NotificationHistory.company_id == company_id)
        if user_id:
            query = query.where(NotificationHistory.user_id == user_id)
        if entity_type:
            query = query.where(NotificationHistory.entity_type == entity_type)
        if entity_id:
            query = query.where(NotificationHistory.entity_id == entity_id)
        if status:
            query = query.where(NotificationHistory.status == status)

        query = query.order_by(desc(NotificationHistory.sent_at)).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

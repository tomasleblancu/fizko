"""
Notifications Repository - Handles notification queries.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class NotificationsRepository(BaseRepository):
    """Repository for notification data access."""

    async def get_by_id(
        self, notification_id: str, include_template: bool = True
    ) -> dict[str, Any] | None:
        """
        Get a notification by ID.

        Args:
            notification_id: Notification UUID
            include_template: Whether to include notification template data

        Returns:
            Notification dict or None if not found
        """
        try:
            select_query = "*"
            if include_template:
                select_query = "*, notification_templates(*)"

            response = (
                self._client
                .table("notifications")
                .select(select_query)
                .eq("id", notification_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_by_id")
        except Exception as e:
            self._log_error("get_by_id", e, notification_id=notification_id)
            return None

    async def get_by_company(
        self,
        company_id: str,
        limit: int = 50,
        status: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get notifications for a company.

        Args:
            company_id: Company UUID
            limit: Maximum number of notifications
            status: Optional status filter (pending, sent, failed)

        Returns:
            List of notification dicts
        """
        try:
            query = (
                self._client
                .table("notifications")
                .select("*, notification_templates(*)")
                .eq("company_id", company_id)
            )

            if status:
                query = query.eq("status", status)

            query = query.order("created_at", desc=True).limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "get_by_company")
        except Exception as e:
            self._log_error(
                "get_by_company",
                e,
                company_id=company_id,
                status=status,
                limit=limit
            )
            return []

    async def get_pending(
        self, company_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get pending notifications.

        Args:
            company_id: Optional company UUID filter
            limit: Maximum number of notifications

        Returns:
            List of pending notification dicts
        """
        try:
            query = (
                self._client
                .table("notifications")
                .select("*, notification_templates(*)")
                .eq("status", "pending")
            )

            if company_id:
                query = query.eq("company_id", company_id)

            query = query.order("scheduled_for", desc=False).limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "get_pending")
        except Exception as e:
            self._log_error("get_pending", e, company_id=company_id, limit=limit)
            return []

    async def get_template_by_code(
        self, template_code: str
    ) -> dict[str, Any] | None:
        """
        Get a notification template by code.

        Args:
            template_code: Template code (e.g., "f29_reminder", "daily_summary")

        Returns:
            Template dict or None if not found
        """
        try:
            response = (
                self._client
                .table("notification_templates")
                .select("*")
                .eq("code", template_code)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_template_by_code")
        except Exception as e:
            self._log_error("get_template_by_code", e, template_code=template_code)
            return None

    async def get_all_templates(self) -> list[dict[str, Any]]:
        """
        Get all notification templates.

        Returns:
            List of template dicts
        """
        try:
            response = (
                self._client
                .table("notification_templates")
                .select("*")
                .order("code")
                .execute()
            )
            return self._extract_data_list(response, "get_all_templates")
        except Exception as e:
            self._log_error("get_all_templates", e)
            return []

    async def get_recent_by_template(
        self,
        company_id: str,
        template_code: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get recent notifications for a specific template.

        Args:
            company_id: Company UUID
            template_code: Template code
            limit: Maximum number of notifications

        Returns:
            List of notification dicts
        """
        try:
            # First get template ID
            template = await self.get_template_by_code(template_code)
            if not template:
                return []

            template_id = template.get("id")

            response = (
                self._client
                .table("notifications")
                .select("*")
                .eq("company_id", company_id)
                .eq("template_id", template_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_recent_by_template")
        except Exception as e:
            self._log_error(
                "get_recent_by_template",
                e,
                company_id=company_id,
                template_code=template_code
            )
            return []

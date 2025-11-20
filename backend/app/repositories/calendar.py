"""
Calendar Repository - Handles calendar event queries.
"""

import logging
from datetime import date
from typing import Any, Optional

from .base import BaseRepository

logger = logging.getLogger(__name__)


class CalendarRepository(BaseRepository):
    """Repository for calendar event data access."""

    # ============================================================================
    # COMPANY_EVENTS (Company-Template Relationships)
    # ============================================================================

    async def get_active_company_events(
        self,
        company_id: str
    ) -> list[dict[str, Any]]:
        """
        Get active company_events for a company with their event templates.

        Args:
            company_id: UUID of the company

        Returns:
            List of company_events with embedded event_template data
        """
        try:
            response = (
                self._client
                .table('company_events')
                .select('*, event_template:event_templates(*)')
                .eq('company_id', company_id)
                .eq('is_active', True)
                .execute()
            )
            return self._extract_data_list(response, "get_active_company_events")
        except Exception as e:
            self._log_error("get_active_company_events", e, company_id=company_id)
            return []

    async def get_company_event_by_id(
        self,
        company_event_id: str
    ) -> dict[str, Any] | None:
        """
        Get a specific company_event by ID with its template.

        Args:
            company_event_id: UUID of the company_event

        Returns:
            Company event dict or None if not found
        """
        try:
            response = (
                self._client
                .table('company_events')
                .select('*, event_template:event_templates(*)')
                .eq('id', company_event_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_company_event_by_id")
        except Exception as e:
            self._log_error("get_company_event_by_id", e, company_event_id=company_event_id)
            return None

    # ============================================================================
    # CALENDAR_EVENTS - Generation & Sync
    # ============================================================================

    async def get_existing_calendar_events(
        self,
        company_event_id: str,
        from_date: date
    ) -> list[dict[str, Any]]:
        """
        Get existing non-completed/non-cancelled calendar events from a date onwards.

        Args:
            company_event_id: UUID of the company_event
            from_date: Date to filter from (inclusive)

        Returns:
            List of calendar events ordered by due_date
        """
        try:
            response = (
                self._client
                .table('calendar_events')
                .select('*')
                .eq('company_event_id', company_event_id)
                .in_('status', ['pending', 'in_progress', 'overdue'])
                .gte('due_date', from_date.isoformat())
                .order('due_date', desc=False)
                .execute()
            )
            return self._extract_data_list(response, "get_existing_calendar_events")
        except Exception as e:
            self._log_error(
                "get_existing_calendar_events",
                e,
                company_event_id=company_event_id,
                from_date=from_date
            )
            return []

    async def create_calendar_event(
        self,
        company_event_id: str,
        company_id: str,
        event_template_id: str,
        due_date: date,
        period_start: date,
        period_end: date,
        status: str = 'pending',
        auto_generated: bool = True
    ) -> dict[str, Any] | None:
        """
        Create a new calendar event.

        Args:
            company_event_id: UUID of the parent company_event
            company_id: UUID of the company
            event_template_id: UUID of the event template
            due_date: Date when the event is due
            period_start: Start of the tax period
            period_end: End of the tax period
            status: Initial status (default: 'pending')
            auto_generated: Whether this was auto-generated (default: True)

        Returns:
            Created calendar event dict or None on error
        """
        try:
            event_data = {
                'company_event_id': company_event_id,
                'company_id': company_id,
                'event_template_id': event_template_id,
                'due_date': due_date.isoformat(),
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                'status': status,
                'auto_generated': auto_generated
            }

            response = (
                self._client
                .table('calendar_events')
                .insert(event_data)
                .execute()
            )

            data = self._extract_data_list(response, "create_calendar_event")
            return data[0] if data else None
        except Exception as e:
            self._log_error(
                "create_calendar_event",
                e,
                company_event_id=company_event_id,
                due_date=due_date
            )
            return None

    async def update_calendar_event_status(
        self,
        event_id: str,
        status: str
    ) -> dict[str, Any] | None:
        """
        Update the status of a calendar event.

        Args:
            event_id: UUID of the calendar event
            status: New status ('pending', 'in_progress', 'completed', 'overdue', 'cancelled')

        Returns:
            Updated calendar event dict or None on error
        """
        try:
            response = (
                self._client
                .table('calendar_events')
                .update({'status': status})
                .eq('id', event_id)
                .execute()
            )

            data = self._extract_data_list(response, "update_calendar_event_status")
            return data[0] if data else None
        except Exception as e:
            self._log_error(
                "update_calendar_event_status",
                e,
                event_id=event_id,
                status=status
            )
            return None

    async def get_all_companies_with_active_events(self) -> list[dict[str, Any]]:
        """
        Get all companies that have at least one active company_event.

        Returns:
            List of company dicts with active events
        """
        try:
            # Get distinct company_ids from active company_events
            response = (
                self._client
                .table('company_events')
                .select('company_id')
                .eq('is_active', True)
                .execute()
            )

            # Get unique company IDs
            company_ids = list(set(row['company_id'] for row in response.data))

            if not company_ids:
                return []

            # Fetch company details
            companies_response = (
                self._client
                .table('companies')
                .select('*')
                .in_('id', company_ids)
                .execute()
            )

            return self._extract_data_list(companies_response, "get_all_companies_with_active_events")
        except Exception as e:
            self._log_error("get_all_companies_with_active_events", e)
            return []

    # ============================================================================
    # ORIGINAL METHODS (Keep existing functionality)
    # ============================================================================

    async def get_event_by_id(
        self,
        event_id: str,
        include_template: bool = True,
        include_tasks: bool = True,
        include_history: bool = False
    ) -> dict[str, Any] | None:
        """
        Get a calendar event by ID.

        Args:
            event_id: Calendar event UUID
            include_template: Whether to include event template data
            include_tasks: Whether to include event tasks
            include_history: Whether to include event history

        Returns:
            Calendar event dict or None if not found
        """
        try:
            # Build select query based on includes
            select_parts = ["*"]
            if include_template:
                select_parts.append("event_templates(*)")
            if include_tasks:
                select_parts.append("event_tasks(*)")
            if include_history:
                select_parts.append("event_history(*)")

            select_query = ", ".join(select_parts)

            response = (
                self._client
                .table("calendar_events")
                .select(select_query)
                .eq("id", event_id)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_event_by_id")
        except Exception as e:
            self._log_error("get_event_by_id", e, event_id=event_id)
            return None

    async def get_events_by_company(
        self,
        company_id: str,
        limit: int = 50,
        status: str | None = None,
        include_template: bool = True
    ) -> list[dict[str, Any]]:
        """
        Get calendar events for a company.

        Args:
            company_id: Company UUID
            limit: Maximum number of events
            status: Optional status filter (pending, completed, cancelled)
            include_template: Whether to include event template data

        Returns:
            List of calendar event dicts
        """
        try:
            select_query = "*"
            if include_template:
                select_query = "*, event_templates(*)"

            query = (
                self._client
                .table("calendar_events")
                .select(select_query)
                .eq("company_id", company_id)
            )

            if status:
                query = query.eq("status", status)

            query = query.order("due_date", desc=False).limit(limit)

            response = query.execute()
            return self._extract_data_list(response, "get_events_by_company")
        except Exception as e:
            self._log_error(
                "get_events_by_company",
                e,
                company_id=company_id,
                status=status,
                limit=limit
            )
            return []

    async def get_upcoming_events(
        self,
        company_id: str,
        days_ahead: int = 30,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get upcoming calendar events for a company.

        Args:
            company_id: Company UUID
            days_ahead: Number of days to look ahead
            limit: Maximum number of events

        Returns:
            List of upcoming calendar event dicts
        """
        try:
            # This would ideally use a date range filter
            # For now, fetch pending events sorted by due_date
            response = (
                self._client
                .table("calendar_events")
                .select("*, event_templates(*)")
                .eq("company_id", company_id)
                .eq("status", "pending")
                .order("due_date", desc=False)
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_upcoming_events")
        except Exception as e:
            self._log_error(
                "get_upcoming_events",
                e,
                company_id=company_id,
                days_ahead=days_ahead
            )
            return []

    async def get_event_template_by_code(
        self, template_code: str
    ) -> dict[str, Any] | None:
        """
        Get an event template by code.

        Args:
            template_code: Template code (e.g., "f29_payment", "tax_declaration")

        Returns:
            Event template dict or None if not found
        """
        try:
            response = (
                self._client
                .table("event_templates")
                .select("*")
                .eq("code", template_code)
                .maybe_single()
                .execute()
            )
            return self._extract_data(response, "get_event_template_by_code")
        except Exception as e:
            self._log_error("get_event_template_by_code", e, template_code=template_code)
            return None

    async def get_all_event_templates(self) -> list[dict[str, Any]]:
        """
        Get all event templates.

        Returns:
            List of event template dicts
        """
        try:
            response = (
                self._client
                .table("event_templates")
                .select("*")
                .order("code")
                .execute()
            )
            return self._extract_data_list(response, "get_all_event_templates")
        except Exception as e:
            self._log_error("get_all_event_templates", e)
            return []

    async def get_event_tasks(self, event_id: str) -> list[dict[str, Any]]:
        """
        Get tasks for a calendar event.

        Args:
            event_id: Calendar event UUID

        Returns:
            List of task dicts
        """
        try:
            response = (
                self._client
                .table("event_tasks")
                .select("*")
                .eq("event_id", event_id)
                .order("created_at")
                .execute()
            )
            return self._extract_data_list(response, "get_event_tasks")
        except Exception as e:
            self._log_error("get_event_tasks", e, event_id=event_id)
            return []

    async def get_event_history(
        self, event_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get history for a calendar event.

        Args:
            event_id: Calendar event UUID
            limit: Maximum number of history entries

        Returns:
            List of history dicts
        """
        try:
            response = (
                self._client
                .table("event_history")
                .select("*")
                .eq("event_id", event_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_event_history")
        except Exception as e:
            self._log_error("get_event_history", e, event_id=event_id)
            return []

    async def get_events_by_template(
        self,
        company_id: str,
        template_code: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get events for a specific template.

        Args:
            company_id: Company UUID
            template_code: Event template code
            limit: Maximum number of events

        Returns:
            List of calendar event dicts
        """
        try:
            # First get template ID
            template = await self.get_event_template_by_code(template_code)
            if not template:
                return []

            template_id = template.get("id")

            response = (
                self._client
                .table("calendar_events")
                .select("*")
                .eq("company_id", company_id)
                .eq("template_id", template_id)
                .order("due_date", desc=True)
                .limit(limit)
                .execute()
            )
            return self._extract_data_list(response, "get_events_by_template")
        except Exception as e:
            self._log_error(
                "get_events_by_template",
                e,
                company_id=company_id,
                template_code=template_code
            )
            return []

"""Calendar repository for database operations."""

from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...db.models import CalendarEvent, Company, CompanyEvent, EventHistory, EventTask, EventTemplate


class CalendarRepository:
    """Repository for calendar-related database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================================
    # EVENT TEMPLATES
    # ============================================================================

    async def get_event_templates(
        self,
        category: Optional[str] = None,
        is_mandatory: Optional[bool] = None
    ) -> List[EventTemplate]:
        """Get event templates with optional filters."""
        query = select(EventTemplate)

        if category:
            query = query.where(EventTemplate.category == category)
        if is_mandatory is not None:
            query = query.where(EventTemplate.is_mandatory == is_mandatory)

        query = query.order_by(EventTemplate.category, EventTemplate.name)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_event_template_by_id(self, event_template_id: UUID) -> Optional[EventTemplate]:
        """Get event template by ID."""
        result = await self.db.execute(
            select(EventTemplate).where(EventTemplate.id == event_template_id)
        )
        return result.scalar_one_or_none()

    async def get_event_template_by_code(self, code: str) -> Optional[EventTemplate]:
        """Get event template by code."""
        result = await self.db.execute(
            select(EventTemplate).where(EventTemplate.code == code)
        )
        return result.scalar_one_or_none()

    async def create_event_template(self, event_template: EventTemplate) -> EventTemplate:
        """Create a new event template."""
        self.db.add(event_template)
        await self.db.commit()
        return event_template

    async def update_event_template(self, event_template: EventTemplate) -> EventTemplate:
        """Update an event template."""
        await self.db.commit()
        return event_template

    async def delete_event_template(self, event_template: EventTemplate) -> None:
        """Delete an event template."""
        await self.db.delete(event_template)
        await self.db.commit()

    # ============================================================================
    # COMPANY EVENTS
    # ============================================================================

    async def get_company_events(
        self,
        company_id: UUID,
        is_active: Optional[bool] = None
    ) -> List[CompanyEvent]:
        """Get company events with optional filters."""
        query = select(CompanyEvent).options(
            selectinload(CompanyEvent.event_template)
        ).where(CompanyEvent.company_id == company_id)

        if is_active is not None:
            query = query.where(CompanyEvent.is_active == is_active)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_active_company_events_by_template(
        self,
        event_template_id: UUID
    ) -> List[CompanyEvent]:
        """Get active company events for a specific template."""
        result = await self.db.execute(
            select(CompanyEvent).where(
                and_(
                    CompanyEvent.event_template_id == event_template_id,
                    CompanyEvent.is_active == True
                )
            )
        )
        return result.scalars().all()

    async def get_company_event_by_id(self, company_event_id: UUID) -> Optional[CompanyEvent]:
        """Get company event by ID."""
        result = await self.db.execute(
            select(CompanyEvent).where(CompanyEvent.id == company_event_id)
        )
        return result.scalar_one_or_none()

    async def get_company_event_by_company_and_template(
        self,
        company_id: UUID,
        event_template_id: UUID
    ) -> Optional[CompanyEvent]:
        """Get company event by company and template."""
        result = await self.db.execute(
            select(CompanyEvent).where(
                and_(
                    CompanyEvent.company_id == company_id,
                    CompanyEvent.event_template_id == event_template_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_company_event(self, company_event: CompanyEvent) -> CompanyEvent:
        """Create a new company event."""
        self.db.add(company_event)
        await self.db.commit()
        return company_event

    async def update_company_event(self, company_event: CompanyEvent) -> CompanyEvent:
        """Update a company event."""
        await self.db.commit()
        return company_event

    # ============================================================================
    # CALENDAR EVENTS
    # ============================================================================

    async def get_calendar_events(
        self,
        company_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        event_template_code: Optional[str] = None,
        limit: int = 50
    ) -> List[CalendarEvent]:
        """Get calendar events with optional filters."""
        query = select(CalendarEvent).options(
            selectinload(CalendarEvent.event_template),
            selectinload(CalendarEvent.tasks)
        ).where(CalendarEvent.company_id == company_id)

        if start_date:
            query = query.where(CalendarEvent.due_date >= start_date)
        if end_date:
            query = query.where(CalendarEvent.due_date <= end_date)
        if status:
            query = query.where(CalendarEvent.status == status)
        if event_template_code:
            query = query.join(EventTemplate).where(EventTemplate.code == event_template_code)

        query = query.order_by(CalendarEvent.due_date).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_upcoming_events(
        self,
        company_id: UUID,
        days_ahead: int = 30
    ) -> List[CalendarEvent]:
        """Get upcoming events for a company."""
        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        query = select(CalendarEvent).options(
            selectinload(CalendarEvent.event_template)
        ).where(
            and_(
                CalendarEvent.company_id == company_id,
                CalendarEvent.due_date >= today,
                CalendarEvent.due_date <= end_date,
                CalendarEvent.status.in_(["pending", "in_progress"])
            )
        ).order_by(CalendarEvent.due_date)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_calendar_event_by_id(self, event_id: UUID) -> Optional[CalendarEvent]:
        """Get calendar event by ID with relationships."""
        result = await self.db.execute(
            select(CalendarEvent).options(
                selectinload(CalendarEvent.event_template),
                selectinload(CalendarEvent.tasks)
            ).where(CalendarEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def update_calendar_event(self, event: CalendarEvent) -> CalendarEvent:
        """Update a calendar event."""
        await self.db.commit()
        return event

    # ============================================================================
    # STATISTICS
    # ============================================================================

    async def get_pending_events(self, company_id: UUID) -> List[CalendarEvent]:
        """Get pending events for a company."""
        query = select(CalendarEvent).where(
            and_(
                CalendarEvent.company_id == company_id,
                CalendarEvent.status == "pending"
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_overdue_events(self, company_id: UUID) -> List[CalendarEvent]:
        """Get overdue events for a company."""
        today = date.today()
        query = select(CalendarEvent).where(
            and_(
                CalendarEvent.company_id == company_id,
                CalendarEvent.due_date < today,
                CalendarEvent.status.in_(["pending", "in_progress"])
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_upcoming_week_events(self, company_id: UUID) -> List[CalendarEvent]:
        """Get events due in the next 7 days."""
        today = date.today()
        next_week = today + timedelta(days=7)
        query = select(CalendarEvent).where(
            and_(
                CalendarEvent.company_id == company_id,
                CalendarEvent.due_date >= today,
                CalendarEvent.due_date <= next_week,
                CalendarEvent.status.in_(["pending", "in_progress"])
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_completed_events_this_month(self, company_id: UUID) -> List[CalendarEvent]:
        """Get events completed this month."""
        today = date.today()
        month_start = today.replace(day=1)
        query = select(CalendarEvent).where(
            and_(
                CalendarEvent.company_id == company_id,
                CalendarEvent.status == "completed",
                CalendarEvent.completion_date >= month_start
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    # ============================================================================
    # EVENT HISTORY
    # ============================================================================

    async def get_event_history(
        self,
        event_id: UUID,
        limit: int = 50
    ) -> List[EventHistory]:
        """Get event history entries."""
        query = select(EventHistory).where(
            EventHistory.calendar_event_id == event_id
        ).order_by(EventHistory.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_event_history(self, history_entry: EventHistory) -> EventHistory:
        """Create a new event history entry."""
        self.db.add(history_entry)
        await self.db.commit()
        return history_entry

    # ============================================================================
    # UTILITIES
    # ============================================================================

    async def get_company_by_id(self, company_id: UUID) -> Optional[Company]:
        """Get company by ID."""
        result = await self.db.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()

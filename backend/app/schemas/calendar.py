"""Pydantic schemas for calendar and event management."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# EVENT TEMPLATE SCHEMAS
# ============================================================================

class CreateEventTemplateRequest(BaseModel):
    """Schema for creating a new event template."""
    code: str = Field(..., description="Unique code identifier for the template")
    name: str = Field(..., description="Display name of the event template")
    category: str = Field(..., description="Category (impuesto_mensual, impuesto_anual, prevision, etc.)")
    authority: str = Field(..., description="Authority responsible (SII, Previred, etc.)")
    is_mandatory: bool = Field(..., description="Whether this event is mandatory")
    default_recurrence: dict = Field(..., description="Default recurrence configuration")
    description: Optional[str] = Field(None, description="Detailed description of the event")
    applies_to_regimes: Optional[dict] = Field(None, description="Tax regimes this applies to")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class UpdateEventTemplateRequest(BaseModel):
    """Schema for updating an event template (all fields optional)."""
    code: Optional[str] = Field(None, description="Unique code identifier")
    name: Optional[str] = Field(None, description="Display name")
    category: Optional[str] = Field(None, description="Event category")
    authority: Optional[str] = Field(None, description="Responsible authority")
    is_mandatory: Optional[bool] = Field(None, description="Mandatory status")
    default_recurrence: Optional[dict] = Field(None, description="Recurrence configuration")
    description: Optional[str] = Field(None, description="Event description")
    applies_to_regimes: Optional[dict] = Field(None, description="Applicable regimes")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class EventTemplate(BaseModel):
    """Schema for reading an event template."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    category: str
    authority: str
    is_mandatory: bool
    default_recurrence: dict
    description: Optional[str] = None
    applies_to_regimes: Optional[dict] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# COMPANY EVENT SCHEMAS
# ============================================================================

class CreateCompanyEventRequest(BaseModel):
    """Schema for creating a company-specific event configuration."""
    event_template_id: UUID = Field(..., description="Reference to event template")
    company_id: UUID = Field(..., description="Company this event belongs to")
    is_enabled: bool = Field(default=True, description="Whether this event is enabled")
    custom_recurrence: Optional[dict] = Field(None, description="Custom recurrence overriding template")
    custom_metadata: Optional[dict] = Field(None, description="Company-specific metadata")


class UpdateCompanyEventRequest(BaseModel):
    """Schema for updating a company event configuration."""
    is_enabled: Optional[bool] = Field(None, description="Enable/disable status")
    custom_recurrence: Optional[dict] = Field(None, description="Custom recurrence")
    custom_metadata: Optional[dict] = Field(None, description="Custom metadata")


class CompanyEvent(BaseModel):
    """Schema for reading a company event configuration."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_template_id: UUID
    company_id: UUID
    is_enabled: bool
    custom_recurrence: Optional[dict] = None
    custom_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# CALENDAR EVENT SCHEMAS
# ============================================================================

class CreateCalendarEventRequest(BaseModel):
    """Schema for creating a calendar event instance."""
    company_event_id: UUID = Field(..., description="Reference to company event config")
    company_id: UUID = Field(..., description="Company this event belongs to")
    event_date: date = Field(..., description="Date of the event")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    status: str = Field(default="pending", description="Status: pending, completed, overdue")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class UpdateCalendarEventRequest(BaseModel):
    """Schema for updating a calendar event."""
    event_date: Optional[date] = Field(None, description="Event date")
    title: Optional[str] = Field(None, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    status: Optional[str] = Field(None, description="Event status")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class CalendarEvent(BaseModel):
    """Schema for reading a calendar event."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_event_id: UUID
    company_id: UUID
    event_date: date
    title: str
    description: Optional[str] = None
    status: str
    metadata: Optional[dict] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# EVENT HISTORY SCHEMAS
# ============================================================================

class CreateEventHistoryRequest(BaseModel):
    """Schema for creating an event history entry."""
    event_type: str = Field(..., description="Type of event that occurred")
    title: str = Field(..., description="Title of the history entry")
    description: Optional[str] = Field(None, description="Detailed description")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class EventHistory(BaseModel):
    """Schema for reading an event history entry."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    calendar_event_id: UUID
    event_type: str
    title: str
    description: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime


# ============================================================================
# EVENT TASK SCHEMAS
# ============================================================================

class CreateEventTaskRequest(BaseModel):
    """Schema for creating a task associated with an event."""
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    due_date: Optional[date] = Field(None, description="Task due date")
    status: str = Field(default="pending", description="Status: pending, in_progress, completed")
    assigned_to: Optional[UUID] = Field(None, description="User ID assigned to this task")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class UpdateEventTaskRequest(BaseModel):
    """Schema for updating an event task."""
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    due_date: Optional[date] = Field(None, description="Task due date")
    status: Optional[str] = Field(None, description="Task status")
    assigned_to: Optional[UUID] = Field(None, description="Assigned user ID")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class EventTask(BaseModel):
    """Schema for reading an event task."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    calendar_event_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: str
    assigned_to: Optional[UUID] = None
    metadata: Optional[dict] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class EventTemplateListResponse(BaseModel):
    """Response schema for listing event templates."""
    data: list[EventTemplate]
    total: int


class CompanyEventListResponse(BaseModel):
    """Response schema for listing company events."""
    data: list[CompanyEvent]
    total: int


class CalendarEventListResponse(BaseModel):
    """Response schema for listing calendar events."""
    data: list[CalendarEvent]
    total: int


class EventHistoryListResponse(BaseModel):
    """Response schema for listing event history."""
    data: list[EventHistory]
    total: int


class EventTaskListResponse(BaseModel):
    """Response schema for listing event tasks."""
    data: list[EventTask]
    total: int

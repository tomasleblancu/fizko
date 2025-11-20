"""Pydantic schemas for notification management."""

from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID
import re

from pydantic import BaseModel, ConfigDict, Field, validator


# ============================================================================
# NOTIFICATION TEMPLATE SCHEMAS
# ============================================================================

class CreateNotificationTemplateRequest(BaseModel):
    """Schema for creating a new notification template."""
    code: str = Field(..., description="Unique code identifier for the template")
    name: str = Field(..., description="Display name of the notification template")
    description: Optional[str] = Field(None, description="Detailed description")
    category: str = Field(..., description="Category (calendar, tax_document, payroll, system, custom)")
    entity_type: Optional[str] = Field(None, description="Entity type (calendar_event, form29, etc.)")
    message_template: str = Field(..., description="Message template with {{variables}}")
    timing_config: dict = Field(..., description="Timing configuration (type: relative/absolute/immediate)")
    priority: str = Field(default="normal", description="Priority (low, normal, high, urgent)")
    is_active: bool = Field(default=True, description="Whether the template is active")
    auto_assign_to_new_companies: bool = Field(default=False, description="Auto-assign to new companies")
    metadata: Optional[dict] = Field(None, description="Additional metadata")

    # WhatsApp Template Integration (manual)
    whatsapp_template_id: Optional[str] = Field(None, description="WhatsApp template ID from Meta Business Manager")


class UpdateNotificationTemplateRequest(BaseModel):
    """Schema for updating a notification template (all fields optional)."""
    code: Optional[str] = Field(None, description="Unique code identifier")
    name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Notification category")
    entity_type: Optional[str] = Field(None, description="Entity type")
    message_template: Optional[str] = Field(None, description="Message template")
    timing_config: Optional[dict] = Field(None, description="Timing configuration")
    priority: Optional[str] = Field(None, description="Priority level")
    is_active: Optional[bool] = Field(None, description="Active status")
    auto_assign_to_new_companies: Optional[bool] = Field(None, description="Auto-assign setting")
    metadata: Optional[dict] = Field(None, description="Additional metadata")

    # WhatsApp Template Integration (manual)
    whatsapp_template_id: Optional[str] = Field(None, description="WhatsApp template ID from Meta Business Manager")


class NotificationTemplate(BaseModel):
    """Schema for reading a notification template."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    category: str
    entity_type: Optional[str] = None
    message_template: str
    timing_config: dict
    priority: str
    is_active: bool
    auto_assign_to_new_companies: bool
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# NOTIFICATION SUBSCRIPTION SCHEMAS
# ============================================================================

class CreateNotificationSubscriptionRequest(BaseModel):
    """Schema for subscribing a company to a notification template."""
    template_id: UUID = Field(..., description="Notification template ID")
    company_id: UUID = Field(..., description="Company ID")
    is_enabled: bool = Field(default=True, description="Whether this subscription is enabled")
    custom_message_template: Optional[str] = Field(None, description="Company-specific message override")
    custom_timing_config: Optional[dict] = Field(None, description="Company-specific timing override")
    custom_metadata: Optional[dict] = Field(None, description="Company-specific metadata")


class UpdateNotificationSubscriptionRequest(BaseModel):
    """Schema for updating a notification subscription."""
    is_enabled: Optional[bool] = Field(None, description="Enable/disable status")
    custom_message_template: Optional[str] = Field(None, description="Custom message template")
    custom_timing_config: Optional[dict] = Field(None, description="Custom timing configuration")
    custom_metadata: Optional[dict] = Field(None, description="Custom metadata")


class NotificationSubscription(BaseModel):
    """Schema for reading a notification subscription."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_id: UUID
    company_id: UUID
    is_enabled: bool
    custom_message_template: Optional[str] = None
    custom_timing_config: Optional[dict] = None
    custom_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# SCHEDULED NOTIFICATION SCHEMAS
# ============================================================================

class ScheduledNotification(BaseModel):
    """Schema for reading a scheduled notification."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subscription_id: UUID
    company_id: UUID
    entity_id: Optional[UUID] = None
    entity_type: Optional[str] = None
    scheduled_for: datetime
    message: str
    priority: str
    status: str
    metadata: Optional[dict] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# NOTIFICATION HISTORY SCHEMAS
# ============================================================================

class NotificationHistory(BaseModel):
    """Schema for reading notification history."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subscription_id: UUID
    company_id: UUID
    entity_id: Optional[UUID] = None
    entity_type: Optional[str] = None
    message: str
    priority: str
    channel: str
    sent_at: datetime
    status: str
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime


# ============================================================================
# USER NOTIFICATION PREFERENCE SCHEMAS
# ============================================================================

class CreateUserNotificationPreferenceRequest(BaseModel):
    """Schema for creating user notification preferences."""
    user_id: UUID = Field(..., description="User ID")
    template_id: UUID = Field(..., description="Notification template ID")
    is_enabled: bool = Field(default=True, description="Whether notifications are enabled")
    channels: list[str] = Field(default_factory=lambda: ["whatsapp"], description="Notification channels")
    custom_settings: Optional[dict] = Field(None, description="Custom user settings")


class UpdateUserNotificationPreferenceRequest(BaseModel):
    """Schema for updating user notification preferences."""
    is_enabled: Optional[bool] = Field(None, description="Enable/disable status")
    channels: Optional[list[str]] = Field(None, description="Notification channels")
    custom_settings: Optional[dict] = Field(None, description="Custom settings")


class UserNotificationPreference(BaseModel):
    """Schema for reading user notification preferences."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    template_id: UUID
    is_enabled: bool
    channels: list[str]
    custom_settings: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# NOTIFICATION EVENT TRIGGER SCHEMAS
# ============================================================================

class CreateNotificationEventTriggerRequest(BaseModel):
    """Schema for creating an event trigger for notifications."""
    template_id: UUID = Field(..., description="Notification template ID")
    event_type: str = Field(..., description="Event type that triggers the notification")
    entity_type: str = Field(..., description="Entity type for the trigger")
    condition_config: Optional[dict] = Field(None, description="Conditions for triggering")
    is_active: bool = Field(default=True, description="Whether the trigger is active")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class UpdateNotificationEventTriggerRequest(BaseModel):
    """Schema for updating an event trigger."""
    event_type: Optional[str] = Field(None, description="Event type")
    entity_type: Optional[str] = Field(None, description="Entity type")
    condition_config: Optional[dict] = Field(None, description="Condition configuration")
    is_active: Optional[bool] = Field(None, description="Active status")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class NotificationEventTrigger(BaseModel):
    """Schema for reading a notification event trigger."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_id: UUID
    event_type: str
    entity_type: str
    condition_config: Optional[dict] = None
    is_active: bool
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class NotificationTemplateListResponse(BaseModel):
    """Response schema for listing notification templates."""
    data: list[NotificationTemplate]
    total: int


class NotificationSubscriptionListResponse(BaseModel):
    """Response schema for listing notification subscriptions."""
    data: list[NotificationSubscription]
    total: int


class ScheduledNotificationListResponse(BaseModel):
    """Response schema for listing scheduled notifications."""
    data: list[ScheduledNotification]
    total: int


class NotificationHistoryListResponse(BaseModel):
    """Response schema for listing notification history."""
    data: list[NotificationHistory]
    total: int


class UserNotificationPreferenceListResponse(BaseModel):
    """Response schema for listing user notification preferences."""
    data: list[UserNotificationPreference]
    total: int

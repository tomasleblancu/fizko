"""Pydantic schemas for WhatsApp router responses."""

from typing import Optional

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Response model for message operations."""

    success: bool
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


class WebhookResponse(BaseModel):
    """Response model for webhook processing."""

    success: bool
    message: str
    conversation_id: Optional[str] = None
    processed_events: int = Field(default=1, description="Number of events processed")


class ConversationResponse(BaseModel):
    """Response model for conversation operations."""

    success: bool
    conversation: Optional[dict] = None
    error: Optional[str] = None


class ContactResponse(BaseModel):
    """Response model for contact operations."""

    success: bool
    contacts: Optional[list] = None
    error: Optional[str] = None

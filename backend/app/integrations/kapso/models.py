"""Data models and enums for Kapso API."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """WhatsApp message types."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    INTERACTIVE = "interactive"
    TEMPLATE = "template"


class InteractiveType(str, Enum):
    """Interactive message types."""

    BUTTON = "button"
    LIST = "list"


class ConversationStatus(str, Enum):
    """Conversation status."""

    ACTIVE = "active"
    ENDED = "ended"


class ConversationSelector(BaseModel):
    """Selector for targeting a conversation."""

    conversation_id: Optional[str] = Field(
        None, description="Kapso conversation ID (UUID)"
    )
    phone_number: Optional[str] = Field(
        None, description="Phone number to find active conversation"
    )


class SendTextRequest(BaseModel):
    """Request model for sending text message."""

    conversation_selector: ConversationSelector
    content: str = Field(..., description="Message text content")
    whatsapp_config_id: Optional[str] = Field(
        None, description="WhatsApp config to send from"
    )
    response_format: Optional[str] = Field("concise", description="Response format")


class SendMediaRequest(BaseModel):
    """Request model for sending media message."""

    conversation_selector: ConversationSelector
    file_url: str = Field(..., description="Public URL to media file")
    message_type: MessageType = Field(..., description="Type of media")
    caption: Optional[str] = Field(None, description="Media caption")
    filename: Optional[str] = Field(None, description="Filename for documents")
    whatsapp_config_id: Optional[str] = None
    response_format: Optional[str] = "concise"


class ButtonItem(BaseModel):
    """Interactive button item."""

    id: str = Field(..., description="Button ID (max 256 chars)")
    title: str = Field(..., description="Button text (max 20 chars)")


class ListSection(BaseModel):
    """List section with rows."""

    title: Optional[str] = Field(None, description="Section title (max 24 chars)")
    rows: list[dict[str, str]] = Field(
        ..., description="Rows with id and title (max 10 rows per section)"
    )


class SendInteractiveRequest(BaseModel):
    """Request model for sending interactive message."""

    conversation_selector: ConversationSelector
    interactive_type: InteractiveType = Field(..., description="Type of interactive")
    body_text: str = Field(..., description="Main body text (max 1024 chars)")
    header_text: Optional[str] = Field(None, description="Header text (max 60 chars)")
    footer_text: Optional[str] = Field(None, description="Footer text (max 60 chars)")
    buttons: Optional[list[ButtonItem]] = Field(
        None, description="Buttons (max 3 for button type)"
    )
    sections: Optional[list[ListSection]] = Field(
        None, description="Sections for list type (max 10 sections)"
    )
    list_button_text: Optional[str] = Field(
        "View Options", description="CTA button text for list (max 20 chars)"
    )
    whatsapp_config_id: Optional[str] = None
    response_format: Optional[str] = "concise"


class SendTemplateRequest(BaseModel):
    """Request model for sending template message."""

    conversation_selector: ConversationSelector
    template_name: str = Field(..., description="Approved template name")
    template_language: Optional[str] = Field("es_CL", description="Language code")
    template_params: Optional[dict[str, Any] | list[Any]] = Field(
        None, description="Template parameters (named or positional)"
    )
    header_type: Optional[str] = Field(None, description="Header type if template has one")
    header_params: Optional[str] = Field(None, description="Header parameter value")
    button_url_params: Optional[dict[str, str]] = Field(
        None, description="URL button parameters by index"
    )
    location_params: Optional[dict[str, Any]] = Field(
        None, description="Location parameters for location header"
    )
    whatsapp_config_id: Optional[str] = None
    response_format: Optional[str] = "concise"


class MessageResponse(BaseModel):
    """Response model for message operations."""

    success: bool
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None

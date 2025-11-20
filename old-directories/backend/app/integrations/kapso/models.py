"""
Modelos de datos para la integración de Kapso
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class MessageType(str, Enum):
    """Tipos de mensajes soportados"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"


class ConversationStatus(str, Enum):
    """Estados de conversación"""
    ACTIVE = "active"
    ENDED = "ended"


class InteractiveType(str, Enum):
    """Tipos de mensajes interactivos"""
    BUTTON = "button"
    LIST = "list"


class WhatsAppMessage(BaseModel):
    """Modelo para mensaje de WhatsApp"""
    model_config = ConfigDict(use_enum_values=True)

    message_type: MessageType
    content: Optional[str] = None
    media_url: Optional[str] = None
    caption: Optional[str] = None
    filename: Optional[str] = None


class TemplateParameter(BaseModel):
    """Parámetro de plantilla"""
    type: str = "text"
    text: str


class TemplateMessage(BaseModel):
    """Mensaje de plantilla de WhatsApp Business"""
    model_config = ConfigDict(use_enum_values=True)

    template_name: str
    template_language: str = "es"
    template_params: Optional[List[str]] = None
    header_params: Optional[str] = None
    button_url_params: Optional[Dict[str, str]] = None
    whatsapp_config_id: str
    phone_number: str


class MediaMessage(BaseModel):
    """Mensaje con media (imagen, video, audio, documento)"""
    model_config = ConfigDict(use_enum_values=True)

    message_type: MessageType
    file_url: str
    caption: Optional[str] = None
    filename: Optional[str] = None


class InteractiveButton(BaseModel):
    """Botón interactivo"""
    id: str
    title: str


class InteractiveSection(BaseModel):
    """Sección de lista interactiva"""
    title: str
    rows: List[Dict[str, str]]


class InteractiveMessage(BaseModel):
    """Mensaje interactivo (botones o lista)"""
    model_config = ConfigDict(use_enum_values=True)

    interactive_type: InteractiveType
    body_text: str
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    buttons: Optional[List[InteractiveButton]] = None
    sections: Optional[List[InteractiveSection]] = None
    list_button_text: Optional[str] = "Ver opciones"


class WhatsAppConversation(BaseModel):
    """Modelo para conversación de WhatsApp"""
    model_config = ConfigDict(use_enum_values=True)

    id: Optional[str] = None
    phone_number: str
    whatsapp_config_id: str
    status: ConversationStatus = ConversationStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationSelector(BaseModel):
    """Selector de conversación"""
    conversation_id: Optional[str] = None
    phone_number: Optional[str] = None


class SendTextRequest(BaseModel):
    """Request para enviar mensaje de texto"""
    conversation_selector: ConversationSelector
    content: str
    whatsapp_config_id: Optional[str] = None


class SendMediaRequest(BaseModel):
    """Request para enviar mensaje con media"""
    model_config = ConfigDict(use_enum_values=True)

    conversation_selector: ConversationSelector
    message_type: MessageType
    file_url: str
    caption: Optional[str] = None
    filename: Optional[str] = None
    whatsapp_config_id: Optional[str] = None


class SendTemplateRequest(BaseModel):
    """Request para enviar plantilla"""
    conversation_selector: ConversationSelector
    template_name: str
    template_language: str = "es"
    template_params: Optional[Any] = None  # Can be list or dict
    header_params: Optional[str] = None
    button_url_params: Optional[Dict[str, str]] = None
    whatsapp_config_id: Optional[str] = None


class SendInteractiveRequest(BaseModel):
    """Request para enviar mensaje interactivo"""
    model_config = ConfigDict(use_enum_values=True)

    conversation_selector: ConversationSelector
    interactive_type: InteractiveType
    body_text: str
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    buttons: Optional[List[Dict[str, str]]] = None
    sections: Optional[List[Dict[str, Any]]] = None
    list_button_text: Optional[str] = "Ver opciones"
    whatsapp_config_id: Optional[str] = None


class WebhookEvent(BaseModel):
    """Evento de webhook de Kapso"""
    event_type: str
    conversation_id: str
    message_id: Optional[str] = None
    payload: Dict[str, Any]
    timestamp: datetime

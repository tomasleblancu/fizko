"""
Pydantic schemas para el router de WhatsApp
"""
from typing import Optional
from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Response para mensajes enviados"""
    success: bool
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


class ConversationResponse(BaseModel):
    """Response para conversaciones"""
    id: str
    phone_number: str
    status: str
    created_at: Optional[str] = None


class ContactResponse(BaseModel):
    """Response para contactos"""
    id: str
    phone_number: str
    display_name: Optional[str] = None
    profile_name: Optional[str] = None

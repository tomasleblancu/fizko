"""
Endpoints para gestión de contactos de WhatsApp
"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.dependencies import get_current_user_id
from app.services.whatsapp import get_whatsapp_service
from app.integrations.kapso.exceptions import KapsoAPIError
from ..schemas import ContactResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/contacts/search", response_model=List[ContactResponse])
async def search_contacts(
    query: str,
    limit: int = 20,
    user_id: UUID = Depends(get_current_user_id),
) -> List[ContactResponse]:
    """
    Busca contactos por nombre o número de teléfono.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.search_contacts(query=query, limit=limit)

        contacts = result.get("nodes") or result.get("contacts", [])

        return [
            ContactResponse(
                id=contact.get("id", ""),
                phone_number=contact.get("phone_number", ""),
                display_name=contact.get("display_name"),
                profile_name=contact.get("profile_name"),
            )
            for contact in contacts
        ]

    except KapsoAPIError as e:
        logger.error(f"Error buscando contactos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/contacts/{identifier}/history")
async def get_contact_history(
    identifier: str,
    message_limit: int = 20,
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Obtiene el historial de mensajes de un contacto.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.get_contact_history(
            identifier=identifier,
            message_limit=message_limit,
        )
        return result

    except KapsoAPIError as e:
        logger.error(f"Error obteniendo historial de contacto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/contacts/{identifier}/note")
async def add_contact_note(
    identifier: str,
    note: str = Body(..., embed=True),
    label: Optional[str] = Body(None, embed=True),
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Añade una nota a un contacto.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.add_note_to_contact(
            contact_identifier=identifier,
            note=note,
            label=label,
        )
        return result

    except KapsoAPIError as e:
        logger.error(f"Error añadiendo nota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/messages/mark-read")
async def mark_messages_as_read(
    conversation_id: Optional[str] = Body(None),
    message_id: Optional[str] = Body(None),
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Marca mensajes como leídos.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.mark_as_read(
            conversation_id=conversation_id,
            message_id=message_id,
        )
        return result

    except KapsoAPIError as e:
        logger.error(f"Error marcando mensajes como leídos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/messages/search")
async def search_messages(
    query: str,
    conversation_id: Optional[str] = None,
    limit: int = 20,
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Busca mensajes por contenido de texto.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.search_messages(
            query=query,
            conversation_id=conversation_id,
            limit=limit,
        )
        return result

    except KapsoAPIError as e:
        logger.error(f"Error buscando mensajes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

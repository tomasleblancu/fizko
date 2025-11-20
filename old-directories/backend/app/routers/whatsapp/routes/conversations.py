"""
Endpoints para gestión de conversaciones de WhatsApp
"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.dependencies import get_current_user_id
from app.services.whatsapp import get_whatsapp_service
from app.integrations.kapso.exceptions import KapsoAPIError
from ..schemas import ConversationResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    whatsapp_config_id: Optional[str] = None,
    limit: int = 50,
    page: int = 1,
    user_id: UUID = Depends(get_current_user_id),
) -> List[ConversationResponse]:
    """
    Lista todas las conversaciones de WhatsApp.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.list_conversations(
            whatsapp_config_id=whatsapp_config_id,
            limit=limit,
            page=page,
        )

        # Adaptar respuesta de Kapso
        conversations = result.get("nodes") or result.get("conversations", [])

        return [
            ConversationResponse(
                id=conv.get("id", ""),
                phone_number=conv.get("phone_number", ""),
                status=conv.get("status", ""),
                created_at=conv.get("created_at"),
            )
            for conv in conversations
        ]

    except KapsoAPIError as e:
        logger.error(f"Error listando conversaciones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Obtiene detalles de una conversación específica.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.get_conversation(conversation_id=conversation_id)
        return result

    except KapsoAPIError as e:
        logger.error(f"Error obteniendo conversación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/conversations/{conversation_id}/end")
async def end_conversation(
    conversation_id: str,
    reason: Optional[str] = Body(None, embed=True),
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Finaliza una conversación activa.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.end_conversation(
            conversation_id=conversation_id,
            reason=reason,
        )
        return result

    except KapsoAPIError as e:
        logger.error(f"Error finalizando conversación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

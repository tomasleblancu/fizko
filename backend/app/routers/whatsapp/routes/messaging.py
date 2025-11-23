"""Messaging routes - send messages via WhatsApp."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.supabase import get_supabase_client
from app.core.auth import get_current_user
from app.integrations.kapso.models import (
    SendTextRequest,
    SendMediaRequest,
    SendInteractiveRequest,
)
from app.services.whatsapp import WhatsAppService
from ..schemas import MessageResponse, SendToPhoneRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def get_whatsapp_service_dep():
    """Dependency to get WhatsAppService."""
    supabase = get_supabase_client()
    return WhatsAppService(supabase)


@router.post("/send/text", response_model=MessageResponse)
async def send_text_message(
    request: SendTextRequest,
    current_user: dict = Depends(get_current_user),
    service: WhatsAppService = Depends(get_whatsapp_service_dep),
):
    """
    Send a text message to a WhatsApp conversation.

    Args:
        request: Text message request
        current_user: Authenticated user dict
        service: WhatsApp service

    Returns:
        MessageResponse with success status and message ID
    """
    user_id = current_user.get("sub")

    try:
        # Get conversation_id from selector
        conversation_id = request.conversation_selector.conversation_id
        phone_number = request.conversation_selector.phone_number

        if not conversation_id and not phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either conversation_id or phone_number is required",
            )

        result = await service.send_text(
            conversation_id=conversation_id or "",
            message=request.content,
            phone_number=phone_number,
            whatsapp_config_id=request.whatsapp_config_id,
        )

        return MessageResponse(
            success=True,
            message_id=result.get("id"),
            conversation_id=result.get("conversation_id"),
            status=result.get("status"),
        )

    except Exception as e:
        logger.error(f"Error sending text message: {e}", exc_info=True)
        return MessageResponse(
            success=False,
            error=str(e),
        )


@router.post("/send/to-phone", response_model=MessageResponse)
async def send_text_to_phone(
    request: SendToPhoneRequest,
    current_user: dict = Depends(get_current_user),
    service: WhatsAppService = Depends(get_whatsapp_service_dep),
):
    """
    Send a text message to a phone number.

    This endpoint automatically finds an active conversation for the phone number.
    If no active conversation exists, it will return an error.

    **Note**: WhatsApp Business API only allows starting new conversations with
    approved templates. Regular messages only work within 24-hour window after
    user message.

    Args:
        request: Phone number and message
        current_user: Authenticated user dict
        service: WhatsApp service

    Returns:
        MessageResponse with success status and message details

    Raises:
        400: If no active conversation found for phone number
    """
    user_id = current_user.get("sub")
    logger.info(f"User {user_id} sending message to phone: {request.phone_number}")

    try:
        result = await service.send_text_to_phone(
            phone_number=request.phone_number,
            message=request.message,
            whatsapp_config_id=request.whatsapp_config_id,
        )

        logger.info(
            f"✅ Message sent to {request.phone_number} | "
            f"conversation: {result.get('conversation_id')}"
        )

        return MessageResponse(
            success=True,
            message_id=result.get("id"),
            conversation_id=result.get("conversation_id"),
            status=result.get("status"),
        )

    except ValueError as e:
        # No active conversation found
        logger.warning(f"No active conversation for {request.phone_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Error sending message to phone: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@router.post("/send/media", response_model=MessageResponse)
async def send_media_message(
    request: SendMediaRequest,
    current_user: dict = Depends(get_current_user),
    service: WhatsAppService = Depends(get_whatsapp_service_dep),
):
    """
    Send a media message (image, video, audio, document).

    Args:
        request: Media message request
        current_user: Authenticated user dict
        service: WhatsApp service

    Returns:
        MessageResponse with success status
    """
    user_id = current_user.get("sub")

    try:
        conversation_id = request.conversation_selector.conversation_id

        if not conversation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="conversation_id is required for media messages",
            )

        result = await service.send_media(
            conversation_id=conversation_id,
            media_url=request.file_url,
            media_type=request.message_type.value,
            caption=request.caption,
            filename=request.filename,
        )

        return MessageResponse(
            success=True,
            message_id=result.get("id"),
            conversation_id=result.get("conversation_id"),
            status=result.get("status"),
        )

    except Exception as e:
        logger.error(f"Error sending media message: {e}", exc_info=True)
        return MessageResponse(
            success=False,
            error=str(e),
        )


@router.post("/send/interactive", response_model=MessageResponse)
async def send_interactive_message(
    request: SendInteractiveRequest,
    current_user: dict = Depends(get_current_user),
    service: WhatsAppService = Depends(get_whatsapp_service_dep),
):
    """
    Send an interactive message (buttons or list).

    Args:
        request: Interactive message request
        current_user: Authenticated user dict
        service: WhatsApp service

    Returns:
        MessageResponse with success status
    """
    user_id = current_user.get("sub")

    try:
        conversation_id = request.conversation_selector.conversation_id

        if not conversation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="conversation_id is required for interactive messages",
            )

        # Convert ButtonItem objects to dicts
        buttons = None
        if request.buttons:
            buttons = [{"id": btn.id, "title": btn.title} for btn in request.buttons]

        # Convert ListSection objects to dicts
        sections = None
        if request.sections:
            sections = [
                {
                    "title": section.title,
                    "rows": section.rows,
                }
                for section in request.sections
            ]

        result = await service.send_interactive(
            conversation_id=conversation_id,
            interactive_type=request.interactive_type.value,
            body_text=request.body_text,
            header_text=request.header_text,
            footer_text=request.footer_text,
            buttons=buttons,
            sections=sections,
            list_button_text=request.list_button_text or "Ver opciones",
        )

        return MessageResponse(
            success=True,
            message_id=result.get("id"),
            conversation_id=result.get("conversation_id"),
            status=result.get("status"),
        )

    except Exception as e:
        logger.error(f"Error sending interactive message: {e}", exc_info=True)
        return MessageResponse(
            success=False,
            error=str(e),
        )

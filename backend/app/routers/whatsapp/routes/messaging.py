"""
Endpoints para envío de mensajes por WhatsApp
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user_id
from app.services.whatsapp import get_whatsapp_service
from app.integrations.kapso.models import (
    SendTextRequest,
    SendMediaRequest,
    SendTemplateRequest,
    SendInteractiveRequest,
)
from app.integrations.kapso.exceptions import (
    KapsoAPIError,
    KapsoAuthenticationError,
    KapsoValidationError,
)
from ..schemas import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/send/text", response_model=MessageResponse)
async def send_text_message(
    request: SendTextRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> MessageResponse:
    """
    Envía un mensaje de texto vía WhatsApp.

    Requiere conversation_id o (phone_number + whatsapp_config_id).
    """
    whatsapp_service = get_whatsapp_service()

    try:
        result = await whatsapp_service.send_text(
            conversation_id=request.conversation_selector.conversation_id,
            phone_number=request.conversation_selector.phone_number,
            message=request.content,
            whatsapp_config_id=request.whatsapp_config_id,
        )

        return MessageResponse(
            success=True,
            message_id=result.get("id"),
            conversation_id=result.get("conversation_id"),
            status=result.get("status"),
        )

    except KapsoValidationError as e:
        logger.error(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except KapsoAuthenticationError as e:
        logger.error(f"Error de autenticación Kapso: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error de autenticación con Kapso API",
        )
    except KapsoAPIError as e:
        logger.error(f"Error de Kapso API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enviando mensaje: {str(e)}",
        )


@router.post("/send/media", response_model=MessageResponse)
async def send_media_message(
    request: SendMediaRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> MessageResponse:
    """
    Envía un mensaje con media (imagen, video, audio, documento).
    """
    whatsapp_service = get_whatsapp_service()

    try:
        if not request.conversation_selector.conversation_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="conversation_id es requerido para enviar media",
            )

        result = await whatsapp_service.send_media(
            conversation_id=request.conversation_selector.conversation_id,
            media_url=request.file_url,
            media_type=request.message_type,
            caption=request.caption,
            filename=request.filename,
        )

        return MessageResponse(
            success=True,
            message_id=result.get("id"),
            conversation_id=result.get("conversation_id"),
            status=result.get("status"),
        )

    except KapsoAPIError as e:
        logger.error(f"Error enviando media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/send/template", response_model=MessageResponse)
async def send_template_message(
    request: SendTemplateRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> MessageResponse:
    """
    Envía un mensaje usando una plantilla de WhatsApp Business.
    Útil para iniciar conversaciones.
    """
    whatsapp_service = get_whatsapp_service()

    try:
        if not request.conversation_selector.phone_number or not request.whatsapp_config_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="phone_number y whatsapp_config_id son requeridos para plantillas",
            )

        result = await whatsapp_service.send_template(
            phone_number=request.conversation_selector.phone_number,
            template_name=request.template_name,
            whatsapp_config_id=request.whatsapp_config_id,
            template_params=request.template_params,
            template_language=request.template_language,
            header_params=request.header_params,
            button_url_params=request.button_url_params,
        )

        return MessageResponse(
            success=True,
            message_id=result.get("id"),
            conversation_id=result.get("conversation_id"),
            status=result.get("status"),
        )

    except KapsoAPIError as e:
        logger.error(f"Error enviando template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/send/interactive", response_model=MessageResponse)
async def send_interactive_message(
    request: SendInteractiveRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> MessageResponse:
    """
    Envía un mensaje interactivo (botones o lista).
    """
    whatsapp_service = get_whatsapp_service()

    try:
        if not request.conversation_selector.conversation_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="conversation_id es requerido para mensajes interactivos",
            )

        result = await whatsapp_service.send_interactive(
            conversation_id=request.conversation_selector.conversation_id,
            interactive_type=request.interactive_type.value,
            body_text=request.body_text,
            header_text=request.header_text,
            footer_text=request.footer_text,
            buttons=request.buttons,
            sections=request.sections,
        )

        return MessageResponse(
            success=True,
            message_id=result.get("id"),
            conversation_id=result.get("conversation_id"),
            status=result.get("status"),
        )

    except KapsoAPIError as e:
        logger.error(f"Error enviando mensaje interactivo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

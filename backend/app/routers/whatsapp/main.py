"""
Router de WhatsApp - Gestión de mensajería vía Kapso
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional, List, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db, AsyncSessionLocal
from app.dependencies import get_current_user_id, require_auth
from app.services.whatsapp import WhatsAppService, authenticate_user_by_whatsapp, get_user_info_by_whatsapp, get_whatsapp_service
from app.db.models import NotificationHistory
from app.integrations.kapso.models import (
    SendTextRequest,
    SendMediaRequest,
    SendTemplateRequest,
    SendInteractiveRequest,
    MessageType,
)
from app.integrations.kapso.exceptions import (
    KapsoAPIError,
    KapsoAuthenticationError,
    KapsoValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/whatsapp",
    tags=["whatsapp"],
    dependencies=[Depends(require_auth)]
)

# Router separado para webhooks (sin autenticación JWT)
webhook_router = APIRouter(
    prefix="/api/whatsapp",
    tags=["whatsapp-webhooks"],
)

# Inicializar servicio de WhatsApp
KAPSO_API_TOKEN = os.getenv("KAPSO_API_TOKEN", "")
KAPSO_API_BASE_URL = os.getenv("KAPSO_API_BASE_URL", "https://app.kapso.ai/api/v1")

whatsapp_service = WhatsAppService(
    api_token=KAPSO_API_TOKEN,
    base_url=KAPSO_API_BASE_URL,
)


# =============================================================================
# Helper Functions - Notification Context
# =============================================================================

async def find_recent_notification(
    db: AsyncSession,
    whatsapp_conversation_id: str,
    hours_ago: int = 48,
) -> Optional[NotificationHistory]:
    """
    Find most recent notification in a WhatsApp conversation.

    Args:
        db: Database session
        whatsapp_conversation_id: The Kapso conversation ID from WhatsApp
        hours_ago: How many hours back to search (default 48)

    Returns:
        NotificationHistory object or None if not found
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select

    cutoff = datetime.utcnow() - timedelta(hours=hours_ago)

    stmt = (
        select(NotificationHistory)
        .where(
            NotificationHistory.whatsapp_conversation_id == whatsapp_conversation_id,
            NotificationHistory.sent_at >= cutoff,
        )
        .order_by(NotificationHistory.sent_at.desc())
        .limit(1)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def get_notification_ui_component(entity_type: Optional[str]) -> str:
    """
    Map notification entity_type to UI Tool component name.

    Args:
        entity_type: The entity type from notification_history (e.g., "calendar_event", "form29")

    Returns:
        UI Tool component name (e.g., "notification_calendar_event", "notification_generic")
    """
    if not entity_type:
        return "notification_generic"

    NOTIFICATION_UI_COMPONENTS = {
        "calendar_event": "notification_calendar_event",
        # Add more mappings as needed:
        # "form29": "notification_form29",
        # "payroll": "notification_payroll",
    }

    return NOTIFICATION_UI_COMPONENTS.get(entity_type, "notification_generic")


# =============================================================================
# Response Models
# =============================================================================

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


# =============================================================================
# Routes - Mensajes
# =============================================================================

@router.post("/send/text", response_model=MessageResponse)
async def send_text_message(
    request: SendTextRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> MessageResponse:
    """
    Envía un mensaje de texto vía WhatsApp.

    Requiere conversation_id o (phone_number + whatsapp_config_id).
    """
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


# =============================================================================
# Routes - Conversaciones
# =============================================================================

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


# =============================================================================
# Routes - Contactos
# =============================================================================

@router.get("/contacts/search", response_model=List[ContactResponse])
async def search_contacts(
    query: str,
    limit: int = 20,
    user_id: UUID = Depends(get_current_user_id),
) -> List[ContactResponse]:
    """
    Busca contactos por nombre o número de teléfono.
    """
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


# =============================================================================
# Routes - Mensajes
# =============================================================================

@router.post("/messages/mark-read")
async def mark_messages_as_read(
    conversation_id: Optional[str] = Body(None),
    message_id: Optional[str] = Body(None),
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Marca mensajes como leídos.
    """
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


# =============================================================================
# Routes - Templates
# =============================================================================

@router.get("/templates")
async def list_templates(
    whatsapp_config_id: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Lista las plantillas de WhatsApp Business disponibles.
    """
    try:
        result = await whatsapp_service.list_templates(
            whatsapp_config_id=whatsapp_config_id,
        )
        return result

    except KapsoAPIError as e:
        logger.error(f"Error listando templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =============================================================================
# Routes - Inbox
# =============================================================================

@router.get("/inbox")
async def get_inbox(
    whatsapp_config_id: str,
    limit: int = 20,
    status_filter: Optional[str] = None,
    user_id: UUID = Depends(get_current_user_id),
) -> Dict[str, Any]:
    """
    Obtiene la bandeja de entrada de conversaciones.
    """
    try:
        result = await whatsapp_service.get_inbox(
            whatsapp_config_id=whatsapp_config_id,
            limit=limit,
            status=status_filter,
        )
        return result

    except KapsoAPIError as e:
        logger.error(f"Error obteniendo inbox: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =============================================================================
# Routes - Webhooks (Sin autenticación JWT - usa firma HMAC)
# =============================================================================

@webhook_router.post("/webhook")
async def handle_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    x_webhook_event: Optional[str] = Header(None, alias="X-Webhook-Event"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    x_webhook_batch: Optional[str] = Header(None, alias="X-Webhook-Batch"),
    x_batch_size: Optional[int] = Header(None, alias="X-Batch-Size"),
) -> Dict[str, Any]:
    """
    Maneja webhooks de Kapso.
    Verifica la firma HMAC-SHA256 y procesa eventos de WhatsApp.

    Este endpoint NO requiere autenticación JWT.
    La autenticación se hace mediante la firma HMAC en el header X-Webhook-Signature.

    Headers esperados de Kapso:
    - X-Webhook-Event: whatsapp.message.received
    - X-Webhook-Signature: <hmac-sha256>
    - X-Idempotency-Key: <unique-key>
    - X-Webhook-Batch: true/false
    - X-Batch-Size: número (si batched)
    """
    try:
        # Log para debug
        client_ip = request.client.host if request.client else 'unknown'
        logger.info(f"📥 Webhook recibido de IP: {client_ip}")
        logger.info(f"📋 Evento: {x_webhook_event}")
        logger.info(f"🔑 Idempotency Key: {x_idempotency_key}")
        if x_webhook_batch:
            logger.info(f"📦 Batch: {x_webhook_batch} (tamaño: {x_batch_size})")

        # Obtener el payload raw
        body = await request.body()
        payload = body.decode("utf-8")

        # Validar firma si está configurado el secreto
        webhook_secret = os.getenv("KAPSO_WEBHOOK_SECRET")

        if webhook_secret:
            # Si hay secreto configurado, requerir y validar firma
            if not x_webhook_signature:
                logger.warning("⚠️ Webhook recibido sin firma X-Webhook-Signature (secreto configurado)")
                logger.warning(f"⚠️ Para testing sin firma, elimina KAPSO_WEBHOOK_SECRET del .env")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing X-Webhook-Signature header",
                )

            is_valid = WhatsAppService.validate_webhook(
                payload=payload,
                signature=x_webhook_signature,
                secret=webhook_secret,
            )

            if not is_valid:
                logger.warning("⚠️ Webhook con firma HMAC inválida")
                logger.warning(f"🔐 Firma recibida: {x_webhook_signature[:20]}...")
                logger.warning(f"🔑 Secret configurado: {webhook_secret[:20]}...")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature",
                )

            logger.info("✅ Firma del webhook validada correctamente")
        else:
            # Sin secreto configurado, permitir webhooks sin firma (modo desarrollo)
            logger.warning("⚠️ KAPSO_WEBHOOK_SECRET no configurado - webhook ACEPTADO sin validación")
            logger.warning("⚠️ En producción, configura KAPSO_WEBHOOK_SECRET para seguridad")

        # Parsear el JSON
        data = json.loads(payload)

        # DEBUG: Log del payload completo para ver la estructura
        logger.info(f"📦 Payload recibido: {json.dumps(data, indent=2)[:500]}...")

        # Manejar webhooks batch (múltiples eventos en un solo request)
        events_to_process = []
        if x_webhook_batch == "true" or isinstance(data, list):
            events_to_process = data if isinstance(data, list) else [data]
            logger.info(f"📦 Procesando batch de {len(events_to_process)} eventos")
        else:
            events_to_process = [data]

        processed_count = 0
        for event_data in events_to_process:
            try:
                # DEBUG: Log de cada evento individual
                logger.info(f"🔍 Event data keys: {list(event_data.keys())}")

                # Extraer datos según la estructura de Kapso
                event_type = event_data.get("event_type") or x_webhook_event

                # Kapso usa esta estructura: {message: {...}, conversation: {...}}
                message_data = event_data.get("message", {})
                conversation_data = event_data.get("conversation", {})

                # Extraer IDs y datos del mensaje
                message_id = message_data.get("id")
                conversation_id = conversation_data.get("id")
                message_content = message_data.get("content", "")
                sender_phone = message_data.get("conversation_phone_number", "")
                contact_name = message_data.get("contact_name", "")
                direction = message_data.get("direction", "")
                message_type = message_data.get("message_type", "text")
                has_media = message_data.get("has_media", False)

                logger.info(f"📥 Procesando evento: {event_type} | Conv: {conversation_id} | Msg: {message_id}")

                # Procesar según tipo de evento
                if event_type in ["message.received", "whatsapp.message.received"]:
                    # Solo procesar mensajes entrantes (inbound)
                    if direction != "inbound":
                        logger.info(f"⏭️ Mensaje saliente, no procesando")
                        processed_count += 1
                        continue

                    logger.info(f"💬 Mensaje {message_type} de {contact_name} ({sender_phone}): {message_content[:100]}")

                    # AUTENTICACIÓN: Identificar usuario por número de WhatsApp
                    authenticated_user_id = None
                    user_info = None
                    company_id = None

                    async with AsyncSessionLocal() as db:
                        authenticated_user_id = await authenticate_user_by_whatsapp(db, sender_phone)

                        if authenticated_user_id:
                            user_info = await get_user_info_by_whatsapp(db, sender_phone)
                            logger.info(f"👤 Usuario autenticado: {authenticated_user_id} - {user_info.get('full_name') or user_info.get('email')}")

                            # Obtener company_id del usuario
                            from app.services.whatsapp.conversation_manager import WhatsAppConversationManager
                            company_id = await WhatsAppConversationManager.get_user_company_id(db, authenticated_user_id)

                            if company_id:
                                logger.info(f"🏢 Company ID obtenido: {company_id}")
                            else:
                                logger.warning(f"⚠️ No se encontró company_id para el usuario: {authenticated_user_id}")
                        else:
                            logger.warning(f"⚠️ Usuario no encontrado para el número: {sender_phone}")

                    # PROCESAMIENTO DEL MENSAJE
                    try:
                        if message_content.strip():  # Solo procesar si hay contenido
                            import time
                            processing_start = time.time()

                            response_message = None
                            display_name = (user_info.get('full_name') or user_info.get('name')) if user_info else contact_name

                            # Obtener servicio de WhatsApp para envío de mensajes
                            whatsapp_service = get_whatsapp_service()
                            if not whatsapp_service:
                                logger.error("❌ WhatsApp service no disponible (KAPSO_API_TOKEN no configurado)")
                                raise HTTPException(
                                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="WhatsApp service not configured"
                                )

                            # USUARIO AUTENTICADO: Invocar agente de IA
                            if authenticated_user_id and company_id:
                                logger.info(f"🤖 Invocando agente de IA para usuario autenticado")
                                agent_start = time.time()

                                try:
                                    from app.services.whatsapp.agent_runner import WhatsAppAgentRunner

                                    # NOTIFICATION CONTEXT DETECTION
                                    # Check if this conversation has a recent notification
                                    ui_context_text = None
                                    async with AsyncSessionLocal() as db:
                                        notification = await find_recent_notification(
                                            db=db,
                                            whatsapp_conversation_id=conversation_id,
                                            hours_ago=48,
                                        )

                                        if notification:
                                            logger.info(f"📬 Notificación encontrada: {notification.id} (entity_type: {notification.entity_type})")

                                            # Dispatch to appropriate UI Tool
                                            try:
                                                from app.agents.ui_tools.core.dispatcher import UIToolDispatcher
                                                from app.agents.ui_tools.core.base import UIToolContext

                                                # Map entity_type to UI Tool component
                                                component_name = get_notification_ui_component(notification.entity_type)
                                                logger.info(f"🎯 Usando UI Tool: {component_name}")

                                                # Create UI Tool context
                                                ui_tool_context = UIToolContext(
                                                    ui_component=component_name,
                                                    user_message=message_content,
                                                    company_id=company_id,
                                                    user_id=str(authenticated_user_id),
                                                    db=db,
                                                    additional_data={
                                                        "notification_id": str(notification.id),
                                                        "entity_id": str(notification.entity_id) if notification.entity_id else None,
                                                    }
                                                )

                                                # Dispatch to UI Tool
                                                dispatcher = UIToolDispatcher()
                                                result = await dispatcher.dispatch(ui_tool_context)

                                                if result.success:
                                                    ui_context_text = result.context_text
                                                    logger.info(f"✅ Contexto de notificación cargado exitosamente ({len(ui_context_text)} chars)")
                                                else:
                                                    logger.warning(f"⚠️ UI Tool falló: {result.error}")

                                            except Exception as e:
                                                logger.error(f"❌ Error cargando contexto de notificación: {e}")
                                                import traceback
                                                logger.error(traceback.format_exc())
                                        else:
                                            logger.debug(f"ℹ️ No se encontró notificación reciente en esta conversación")

                                    # MEDIA PROCESSING
                                    # Check if message has media attachments (images, PDFs, etc.)
                                    attachments = None

                                    if has_media and message_type != "text":
                                        logger.info(f"📎 Media detectado: {message_type}")

                                        # Enviar mensaje de confirmación al usuario ANTES de procesar
                                        try:
                                            # Determinar mensaje según tipo de archivo
                                            processing_messages = {
                                                "image": "📸 Recibí tu imagen, la estoy analizando...",
                                                "video": "🎥 Recibí tu video, lo estoy procesando...",
                                                "audio": "🎵 Recibí tu audio, lo estoy procesando...",
                                                "document": "📄 Recibí tu documento, lo estoy analizando...",
                                            }

                                            processing_msg = processing_messages.get(message_type, "📎 Recibí tu archivo, lo estoy procesando...")

                                            logger.info(f"💬 Enviando mensaje de procesamiento al usuario: {processing_msg}")

                                            # Enviar mensaje inmediato
                                            whatsapp_service = get_whatsapp_service()
                                            if whatsapp_service:
                                                await whatsapp_service.send_text(
                                                    conversation_id=conversation_id,
                                                    message=processing_msg,
                                                )
                                                logger.info(f"✅ Mensaje de procesamiento enviado")
                                        except Exception as e:
                                            logger.warning(f"⚠️ No se pudo enviar mensaje de procesamiento: {e}")
                                            # No fallar el flujo - continuar procesando

                                        # Ahora procesar el archivo
                                        try:
                                            from app.services.whatsapp.media_processor import get_media_processor

                                            processor = get_media_processor()
                                            attachment = await processor.process_inbound_media(message_data)

                                            if attachment:
                                                attachments = [attachment]
                                                logger.info(f"✅ Media procesado: {attachment['attachment_id']}")
                                                logger.info(f"  Type: {attachment['mime_type']}")
                                                logger.info(f"  File: {attachment['filename']}")
                                                logger.info(f"  URL: {attachment['url']}")

                                                # Log especial para PDFs con vector_store
                                                if "vector_store_id" in attachment:
                                                    logger.info(f"  📄 PDF con FileSearch habilitado: {attachment['vector_store_id']}")
                                            else:
                                                logger.warning(f"⚠️ No se pudo procesar media (puede ser error de descarga o tipo no soportado)")

                                        except Exception as e:
                                            logger.error(f"❌ Error procesando media: {e}", exc_info=True)
                                            # No fallar todo el flujo - continuar sin attachment

                                    agent_runner = WhatsAppAgentRunner()
                                    # No guardar assistant message aún - se hará después de enviar
                                    response_message, db_conversation_id = await agent_runner.process_message(
                                        user_id=authenticated_user_id,
                                        company_id=company_id,
                                        message_content=message_content or "Archivo adjunto",  # Fallback si solo hay media sin texto
                                        conversation_id=conversation_id,
                                        message_id=message_id,
                                        save_assistant_message=False,  # Guardamos después de enviar
                                        ui_context_text=ui_context_text,  # Pass notification context to agent
                                        attachments=attachments,  # Pass processed media attachments
                                    )

                                    agent_time = time.time() - agent_start
                                    logger.info(f"✅ Agente generó respuesta ({len(response_message)} chars) en {agent_time:.3f}s")

                                except Exception as e:
                                    logger.error(f"❌ Error ejecutando agente: {e}")
                                    import traceback
                                    logger.error(traceback.format_exc())

                                    # Fallback en caso de error
                                    response_message = (
                                        f"Hola {display_name}, recibí tu mensaje pero tuve un problema al procesarlo. 😔\n\n"
                                        "Por favor, intenta nuevamente o contáctanos en soporte@fizko.ai"
                                    )

                            # USUARIO NO AUTENTICADO: Respuestas predefinidas
                            else:
                                if "hola" in message_content.lower() or "hi" in message_content.lower():
                                    response_message = f"¡Hola {contact_name}! 👋\n\nNo te encontramos en nuestro sistema. Por favor, regístrate en https://app.fizko.ai para acceder a tus datos tributarios y usar el asistente de IA."

                                elif "ayuda" in message_content.lower() or "help" in message_content.lower():
                                    response_message = (
                                        f"Hola {contact_name}, para acceder a ayuda personalizada necesitas estar registrado.\n\n"
                                        "Regístrate en: https://app.fizko.ai\n"
                                        "Para soporte general, escríbenos a soporte@fizko.ai"
                                    )

                                else:
                                    response_message = (
                                        f"Gracias por tu mensaje, {contact_name}. 📩\n\n"
                                        f"No te encontramos en nuestro sistema.\n\n"
                                        "Para acceder a nuestro asistente de IA y tus datos tributarios, regístrate en https://app.fizko.ai"
                                    )

                            # Enviar respuesta
                            if response_message and conversation_id:
                                send_start = time.time()
                                await whatsapp_service.send_text(
                                    conversation_id=conversation_id,
                                    message=response_message
                                )
                                send_time = time.time() - send_start
                                total_time = time.time() - processing_start
                                logger.info(f"✅ Respuesta enviada a {contact_name} (envío: {send_time:.3f}s)")
                                logger.info(f"⏱️  TIEMPO TOTAL (procesamiento + envío): {total_time:.3f}s")

                                # Guardar mensaje del asistente en background (no bloquear)
                                if authenticated_user_id and 'db_conversation_id' in locals():
                                    import asyncio

                                    async def save_assistant_message_bg():
                                        try:
                                            from app.services.whatsapp.conversation_manager import WhatsAppConversationManager
                                            async with AsyncSessionLocal() as db:
                                                await WhatsAppConversationManager.add_message(
                                                    db=db,
                                                    conversation_id=db_conversation_id,
                                                    user_id=authenticated_user_id,
                                                    content=response_message,
                                                    role="assistant",
                                                )
                                                logger.info(f"💾 Assistant message saved in background")
                                        except Exception as e:
                                            logger.error(f"❌ Error guardando assistant message en background: {e}")

                                    # Ejecutar en background sin esperar
                                    asyncio.create_task(save_assistant_message_bg())

                    except Exception as e:
                        logger.error(f"❌ Error procesando mensaje: {e}")
                        import traceback
                        logger.error(traceback.format_exc())

                elif event_type in ["message.sent", "whatsapp.message.sent"]:
                    logger.info(f"✅ Mensaje enviado confirmado: {message_id}")

                elif event_type in ["message.delivered", "whatsapp.message.delivered"]:
                    logger.info(f"📬 Mensaje entregado: {message_id}")

                elif event_type in ["message.read", "whatsapp.message.read"]:
                    logger.info(f"👁️ Mensaje leído: {message_id}")

                elif event_type in ["message.failed", "whatsapp.message.failed"]:
                    error = event_data.get("error", {})
                    logger.error(f"❌ Mensaje falló: {message_id} - Error: {error}")

                else:
                    logger.warning(f"⚠️ Evento desconocido: {event_type}")

                processed_count += 1

            except Exception as e:
                logger.error(f"❌ Error procesando evento individual: {e}")
                # Continuar procesando los demás eventos del batch

        return {
            "status": "ok",
            "message": f"Webhook processed successfully",
            "events_processed": processed_count,
            "idempotency_key": x_idempotency_key,
        }

    except json.JSONDecodeError as e:
        logger.error(f"❌ Error decodificando webhook JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    except HTTPException:
        # Re-raise HTTP exceptions (401, 400, etc)
        raise
    except Exception as e:
        logger.exception(f"❌ Error inesperado procesando webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# =============================================================================
# Routes - Health Check
# =============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Verifica el estado de la conexión con Kapso.
    """
    try:
        result = await whatsapp_service.health_check()
        return result

    except Exception as e:
        logger.error(f"Health check falló: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }

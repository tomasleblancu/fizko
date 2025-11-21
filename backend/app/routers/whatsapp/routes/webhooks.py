"""
Webhook routes - handle incoming WhatsApp messages from Kapso.

This is the core orchestrator for inbound messages.
"""

import json
import logging
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.config.supabase import get_supabase_client
from app.services.whatsapp import (
    WhatsAppAgentRunner,
    WhatsAppService,
    authenticate_user_by_whatsapp,
)
from ..schemas import WebhookResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook", response_model=WebhookResponse)
async def handle_webhook(
    request: Request,
    x_webhook_signature: str = Header(..., description="HMAC signature"),
    x_webhook_batch: str = Header(default="false", description="Batch indicator"),
):
    """
    Handle incoming WhatsApp webhooks from Kapso.

    This endpoint:
    1. Validates HMAC signature
    2. Authenticates user by phone number
    3. Processes the message
    4. Sends response back via WhatsApp

    Args:
        request: FastAPI request
        x_webhook_signature: HMAC signature header
        x_webhook_batch: Batch processing indicator

    Returns:
        WebhookResponse with success status
    """
    # Get raw body for signature validation
    raw_body = await request.body()
    payload_str = raw_body.decode("utf-8")

    # Parse JSON
    try:
        data = json.loads(payload_str)
        print("=" * 80)
        print("WEBHOOK PAYLOAD RECEIVED:")
        print(json.dumps(data, indent=2))
        print("=" * 80)
        logger.info(f"Received webhook payload: {json.dumps(data, indent=2)}")
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Validate webhook signature
    webhook_secret = os.getenv("KAPSO_WEBHOOK_SECRET")
    if webhook_secret:  # Only validate if secret is configured
        is_valid = WhatsAppService.validate_webhook(
            payload=payload_str,
            signature=x_webhook_signature,
            secret=webhook_secret,
        )

        if not is_valid:
            logger.error("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )
    else:
        logger.warning("KAPSO_WEBHOOK_SECRET not set - skipping signature validation")

    # Handle batch processing
    events_to_process = []
    if x_webhook_batch == "true" or isinstance(data, list):
        events_to_process = data if isinstance(data, list) else [data]
    else:
        events_to_process = [data]

    logger.info(f"Processing {len(events_to_process)} webhook event(s)")

    # Get Supabase client
    supabase = get_supabase_client()
    whatsapp_service = WhatsAppService(supabase)

    processed_count = 0
    last_conversation_id = None

    for event_data in events_to_process:
        try:
            result = await _process_single_event(
                event_data=event_data,
                supabase=supabase,
                whatsapp_service=whatsapp_service,
            )
            if result:
                processed_count += 1
                last_conversation_id = result.get("conversation_id")

        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)
            # Continue processing other events

    return WebhookResponse(
        success=True,
        message=f"Processed {processed_count} event(s)",
        conversation_id=last_conversation_id,
        processed_events=processed_count,
    )


async def _process_single_event(
    event_data: dict[str, Any],
    supabase: Any,
    whatsapp_service: WhatsAppService,
) -> dict[str, Any] | None:
    """
    Process a single webhook event.

    Args:
        event_data: Event data from webhook
        supabase: Supabase client
        whatsapp_service: WhatsApp service instance

    Returns:
        Processing result dict or None
    """
    # Extract message and conversation data
    # Kapso sends data directly in root (no event_type wrapper)
    message_data = event_data.get("message", {})
    conversation_data = event_data.get("conversation", {})

    # Check if this is a message event
    if not message_data:
        logger.info("No message data found, skipping event")
        return None

    # Get direction from Kapso metadata
    direction = message_data.get("kapso", {}).get("direction")

    logger.info(f"Processing message with direction: {direction}")

    # Only process inbound messages
    if direction != "inbound":
        logger.info(f"Ignoring {direction} message")
        return None

    # Get message content (V2: text.body, V1: content)
    message_content = ""
    if "text" in message_data and isinstance(message_data["text"], dict):
        message_content = message_data["text"].get("body", "")
    else:
        message_content = message_data.get("content", "")

    if not message_content:
        logger.warning("No message content found")
        return None

    # Get sender phone
    sender_phone = message_data.get("from")
    if not sender_phone:
        logger.error("No sender phone found in message")
        return None

    # Normalize phone (add + prefix if missing)
    if not sender_phone.startswith("+"):
        sender_phone = f"+{sender_phone}"

    # Get conversation ID
    conversation_id = conversation_data.get("id")
    if not conversation_id:
        logger.error("No conversation ID found")
        return None

    # Get message ID
    message_id = message_data.get("id")

    logger.info(f"Processing inbound message from {sender_phone}")

    # Authenticate user by phone
    authenticated_user_id = await authenticate_user_by_whatsapp(supabase, sender_phone)

    if not authenticated_user_id:
        # User not found - send registration message
        logger.warning(f"User not found for phone: {sender_phone}")

        contact_name = conversation_data.get("contact_name", "")
        greeting = f"¡Hola {contact_name}! 👋\n\n" if contact_name else "¡Hola! 👋\n\n"

        response_message = (
            f"{greeting}"
            "No te encontramos en nuestro sistema. "
            "Por favor, regístrate en https://app.fizko.ai para acceder a nuestros servicios."
        )

        await whatsapp_service.send_text(
            conversation_id=conversation_id,
            message=response_message,
        )

        return {"conversation_id": conversation_id, "authenticated": False}

    # Get user's company_id from sessions table (user can have multiple companies)
    client = supabase.client if hasattr(supabase, 'client') else supabase
    try:
        # Get active session for user
        session_response = (
            client.table("sessions")
            .select("company_id, is_active")
            .eq("user_id", str(authenticated_user_id))
            .eq("is_active", True)
            .order("last_accessed_at", desc=True)
            .limit(1)
            .execute()
        )

        # Check if we got data
        if not session_response.data or len(session_response.data) == 0:
            logger.error(f"No active session found for user: {authenticated_user_id}")
            response_message = "No encontramos una sesión activa. Por favor inicia sesión en la app primero."
            await whatsapp_service.send_text(
                conversation_id=conversation_id,
                message=response_message,
            )
            return {"conversation_id": conversation_id, "authenticated": True, "error": "no_session"}

        session = session_response.data[0]
        company_id = session["company_id"]

        if not company_id:
            logger.error(f"No company_id in session for user: {authenticated_user_id}")
            response_message = "Tu sesión no está asociada a una empresa. Por favor contacta a soporte."
            await whatsapp_service.send_text(
                conversation_id=conversation_id,
                message=response_message,
            )
            return {"conversation_id": conversation_id, "authenticated": True, "error": "no_company"}

    except Exception as e:
        logger.error(f"Error loading session for user {authenticated_user_id}: {e}", exc_info=True)
        response_message = "Ocurrió un error al cargar tu sesión. Por favor intenta nuevamente."
        await whatsapp_service.send_text(
            conversation_id=conversation_id,
            message=response_message,
        )
        return {"conversation_id": conversation_id, "authenticated": True, "error": "session_load_error"}

    # Execute agent with message
    logger.info(
        f"🤖 Executing agent for user {authenticated_user_id} | "
        f"company {company_id} | message: {message_content[:50]}..."
    )

    try:
        agent_runner = WhatsAppAgentRunner(supabase=supabase)
        response_message = await agent_runner.run(
            user_id=str(authenticated_user_id),
            company_id=str(company_id),
            thread_id=conversation_id,  # Use conversation_id as thread_id
            message=message_content,
            metadata={
                "phone": sender_phone,
                "conversation_id": conversation_id,
                "message_id": message_id,
            },
        )

        logger.info(
            f"✅ Agent response generated: {len(response_message)} chars | "
            f"conversation {conversation_id}"
        )

    except Exception as e:
        logger.error(f"❌ Error executing agent: {e}", exc_info=True)
        response_message = "Lo siento, ocurrió un error al procesar tu mensaje. Por favor intenta nuevamente."

    # Send response
    logger.info(f"Sending response to conversation {conversation_id}")

    try:
        result = await whatsapp_service.send_text(
            conversation_id=conversation_id,
            message=response_message,
        )
        logger.info(f"Message sent successfully: {result}")
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        raise

    # TODO: Save conversation and messages to database

    logger.info(f"Successfully processed message for user: {authenticated_user_id}")

    return {
        "conversation_id": conversation_id,
        "authenticated": True,
        "user_id": str(authenticated_user_id),
        "company_id": str(company_id),
    }

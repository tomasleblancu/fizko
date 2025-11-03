"""
Webhook handler para mensajes de WhatsApp desde Kapso
Este archivo contiene toda la lógica de procesamiento de webhooks incluyendo:
- Validación HMAC
- Detección de contexto de notificaciones
- Procesamiento de media
- Ejecución del agente de IA
"""
import json
import logging
import os
import time
import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.config.database import AsyncSessionLocal
from app.services.whatsapp import (
    WhatsAppService,
    authenticate_user_by_whatsapp,
    get_user_info_by_whatsapp,
    get_whatsapp_service,
)
from ..helpers import find_recent_notification, get_notification_ui_component

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook")
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

                    # OPTIMIZACIÓN: AUTENTICACIÓN CON CACHÉ
                    # Primero intentar obtener auth desde metadata de conversación existente
                    authenticated_user_id = None
                    user_info = None
                    company_id = None
                    cached_auth_used = False

                    auth_total_start = time.time()
                    async with AsyncSessionLocal() as db:
                        from app.services.whatsapp.conversation_manager import WhatsAppConversationManager
                        from app.db.models import Conversation
                        from sqlalchemy import select

                        # 1. Buscar conversación existente por Kapso conversation_id
                        if conversation_id:
                            lookup_start = time.time()
                            result = await db.execute(
                                select(Conversation).where(
                                    Conversation.meta_data["whatsapp_conversation_id"].astext == conversation_id
                                )
                            )
                            existing_conversation = result.scalar_one_or_none()
                            lookup_time = time.time() - lookup_start

                            if existing_conversation:
                                # Intentar obtener auth cacheada
                                cached_auth = WhatsAppConversationManager.get_cached_auth_from_conversation(existing_conversation)

                                if cached_auth:
                                    authenticated_user_id = cached_auth["user_id"]
                                    company_id = cached_auth["company_id"]
                                    cached_auth_used = True

                                    # Obtener info de usuario (ligera - solo para display_name)
                                    user_info_start = time.time()
                                    user_info = await get_user_info_by_whatsapp(db, sender_phone)
                                    user_info_time = time.time() - user_info_start

                                    auth_total_time = time.time() - auth_total_start
                                    logger.info(f"⚡ Auth cacheada usada: user={authenticated_user_id}, company={company_id}")
                                    logger.info(f"  ⏱️  DB: Cached auth total: {auth_total_time:.3f}s (lookup={lookup_time:.3f}s + user_info={user_info_time:.3f}s)")
                                else:
                                    logger.debug("ℹ️ Conversación existe pero sin auth cacheada")

                        # 2. Si no hay auth cacheada, hacer autenticación completa
                        if not cached_auth_used:
                            full_auth_start = time.time()
                            logger.info("🔍 Realizando autenticación completa (primera vez o cache incompleto)")

                            auth_user_start = time.time()
                            authenticated_user_id = await authenticate_user_by_whatsapp(db, sender_phone)
                            auth_user_time = time.time() - auth_user_start

                            if authenticated_user_id:
                                user_info_start = time.time()
                                user_info = await get_user_info_by_whatsapp(db, sender_phone)
                                user_info_time = time.time() - user_info_start

                                company_start = time.time()
                                company_id = await WhatsAppConversationManager.get_user_company_id(db, authenticated_user_id)
                                company_time = time.time() - company_start

                                full_auth_time = time.time() - full_auth_start
                                logger.info(f"👤 Usuario autenticado: {authenticated_user_id} - {user_info.get('full_name') or user_info.get('email')}")
                                logger.info(f"  ⏱️  DB: Full auth total: {full_auth_time:.3f}s")
                                logger.info(f"    └─ Breakdown: auth={auth_user_time:.3f}s + user_info={user_info_time:.3f}s + company={company_time:.3f}s")

                                if company_id:
                                    logger.info(f"🏢 Company ID obtenido: {company_id}")
                                else:
                                    logger.warning(f"⚠️ No se encontró company_id para el usuario: {authenticated_user_id}")
                            else:
                                logger.warning(f"⚠️ Usuario no encontrado para el número: {sender_phone}")

                    # PROCESAMIENTO DEL MENSAJE
                    try:
                        if message_content.strip() or has_media:  # Procesar si hay contenido o media
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

                                    # ✨ OPTIMIZACIÓN: Notification context ya no se busca aquí
                                    # El contexto fue anclado como mensaje assistant cuando se envió la notificación
                                    # SQLite Session lo cargará automáticamente en el historial

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
                                    # No guardar mensajes aún - se guardarán después de enviar
                                    response_message, db_conversation_id, user_msg_content, user_msg_id = await agent_runner.process_message(
                                        user_id=authenticated_user_id,
                                        company_id=company_id,
                                        message_content=message_content or "Archivo adjunto",  # Fallback si solo hay media sin texto
                                        conversation_id=conversation_id,
                                        message_id=message_id,
                                        phone_number=sender_phone,  # Para cachear en metadata
                                        save_assistant_message=False,  # Guardamos después de enviar
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

                                # Guardar mensajes (usuario + asistente) en background (no bloquear)
                                if authenticated_user_id and db_conversation_id:
                                    # Capturar variables en el closure
                                    _user_id = authenticated_user_id
                                    _conv_id = db_conversation_id
                                    _user_content = user_msg_content
                                    _user_msg_id = user_msg_id
                                    _assistant_content = response_message

                                    async def save_messages_bg():
                                        try:
                                            from app.services.whatsapp.conversation_manager import WhatsAppConversationManager
                                            async with AsyncSessionLocal() as db:
                                                # Guardar mensaje del usuario
                                                await WhatsAppConversationManager.add_message(
                                                    db=db,
                                                    conversation_id=_conv_id,
                                                    user_id=_user_id,
                                                    content=_user_content,
                                                    role="user",
                                                    metadata={"message_id": _user_msg_id},
                                                )
                                                logger.info(f"💾 User message saved in background")

                                                # Guardar mensaje del asistente
                                                await WhatsAppConversationManager.add_message(
                                                    db=db,
                                                    conversation_id=_conv_id,
                                                    user_id=_user_id,
                                                    content=_assistant_content,
                                                    role="assistant",
                                                )
                                                logger.info(f"💾 Assistant message saved in background")
                                        except Exception as e:
                                            logger.error(f"❌ Error guardando mensajes en background: {e}")
                                            import traceback
                                            logger.error(traceback.format_exc())

                                    # Ejecutar en background sin esperar
                                    asyncio.create_task(save_messages_bg())

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

"""
Runner del agente de IA para WhatsApp con sistema multi-agente.
"""
import logging
import os
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from agents import Runner, SQLiteSession
from openai import AsyncOpenAI

from app.agents.orchestration import handoffs_manager
from app.config.database import AsyncSessionLocal
from .conversation_manager import WhatsAppConversationManager

logger = logging.getLogger(__name__)

# In-memory cache for user info (30 minute TTL)
_user_info_cache: Dict[str, tuple[datetime, Dict[str, Any]]] = {}
_USER_CACHE_TTL_SECONDS = 1800  # 30 minutes


async def load_user_info_cached(db, user_id: UUID, use_cache: bool = True) -> Dict[str, Any]:
    """
    Load user profile information with in-memory caching.

    Args:
        db: Database session
        user_id: User UUID
        use_cache: Whether to use cache (default: True)

    Returns:
        Dict with user info
    """
    cache_key = str(user_id)

    # Check cache first
    if use_cache and cache_key in _user_info_cache:
        cached_time, cached_data = _user_info_cache[cache_key]
        cache_age = (datetime.now() - cached_time).total_seconds()

        if cache_age < _USER_CACHE_TTL_SECONDS:
            return cached_data
        else:
            del _user_info_cache[cache_key]

    # Fetch from DB
    from app.db.models import Profile
    from sqlalchemy import select

    result = await db.execute(select(Profile).where(Profile.id == user_id))
    profile = result.scalar_one_or_none()

    if profile:
        user_info = {
            "id": str(profile.id),
            "name": profile.full_name or profile.email or "Usuario",
            "email": profile.email,
            "phone": profile.phone,
        }
    else:
        user_info = {"id": str(user_id), "name": "Usuario", "email": "N/A"}

    # Store in cache
    if use_cache:
        _user_info_cache[cache_key] = (datetime.now(), user_info)

    return user_info


class WhatsAppAgentRunner:
    """
    Ejecuta agentes de Fizko para mensajes de WhatsApp con sistema multi-agente.
    """

    def __init__(self):
        """Inicializa el runner con sistema multi-agente."""
        logger.info("🤖 WhatsAppAgentRunner initialized (multi-agent mode)")

        # Directorio para sesiones del agente
        sessions_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "sessions"
        )
        os.makedirs(sessions_dir, exist_ok=True)
        self.session_file = os.path.join(sessions_dir, "whatsapp_agent_sessions.db")

    async def process_message(
        self,
        user_id: UUID,
        company_id: UUID,
        message_content: str,
        conversation_id: Optional[str] = None,  # Kapso conversation_id
        message_id: Optional[str] = None,  # Kapso message_id
        phone_number: Optional[str] = None,  # Número de WhatsApp para cachear
        save_assistant_message: bool = True,  # Si False, no guarda la respuesta del agente
        attachments: Optional[List[Dict[str, Any]]] = None,  # Attachments procesados (imágenes, PDFs)
    ) -> tuple[str, Optional[UUID]]:
        """
        Procesa un mensaje del usuario y retorna la respuesta del agente.

        Args:
            user_id: ID del usuario autenticado
            company_id: ID de la empresa del usuario
            message_content: Contenido del mensaje
            conversation_id: ID de conversación de Kapso (opcional)
            message_id: ID del mensaje de Kapso (opcional)
            phone_number: Número de WhatsApp para cachear en metadata (opcional)
            save_assistant_message: Si True, guarda el mensaje del asistente (default: True)
            attachments: Lista de attachments procesados por WhatsAppMediaProcessor (opcional)
                Estructura esperada:
                [{
                    "attachment_id": "atc_xxx",
                    "mime_type": "image/jpeg",
                    "filename": "photo.jpg",
                    "url": "https://...",
                    "base64": "..." (para imágenes),
                    "vector_store_id": "vs_xxx" (para PDFs)
                }]

        Returns:
            tuple[str, Optional[UUID]]: (respuesta del agente, conversation_id en DB)
        """
        import time
        process_start = time.time()
        logger.info("=" * 80)
        logger.info(f"🚀 WhatsApp Agent | user={user_id}")

        async with AsyncSessionLocal() as db:
            # 1. Setup: conversation + messages + context (con timing detallado)
            setup_start = time.time()

            # Operación 1: Buscar/crear conversación
            conv_start = time.time()
            conversation = await WhatsAppConversationManager.get_or_create_conversation(
                db=db,
                user_id=user_id,
                company_id=company_id,
                conversation_id=conversation_id,
                phone_number=phone_number,
            )
            conv_time = time.time() - conv_start
            logger.info(f"  ⏱️  DB: get_or_create_conversation: {conv_time:.3f}s")

            # Operación 2: Guardar mensaje del usuario → MOVIDO A BACKGROUND
            # Se guardará después de enviar respuesta al usuario para reducir latencia
            logger.info(f"  ⏱️  DB: add_message(user): skipped (will save in background)")

            # Operación 3: Cargar user_info
            # NOTE: NO LONGER LOADING company_info - agents use search_company_memory() on-demand
            user_start = time.time()
            user_info = await load_user_info_cached(db, user_id)
            user_time = time.time() - user_start
            cache_hit_user = user_time < 0.05
            logger.info(f"  ⏱️  DB: load_user_info_cached: {user_time:.3f}s (cache_hit: {cache_hit_user})")

            setup_time = time.time() - setup_start
            logger.info(f"⏱️  Setup total: {setup_time:.3f}s | conv_id={conversation.id}")
            logger.info(f"    └─ Breakdown: conv={conv_time:.3f}s + user={user_time:.3f}s")

            # 2. Preparar mensaje (sin inyectar company_context aquí - se hace en session_input_callback)
            vector_store_ids = []

            # Add SII FAQ vector store if configured
            sii_faq_vector_id = os.getenv("SII_FAQ_VECTOR_STORE_ID")
            if sii_faq_vector_id:
                vector_store_ids.append(sii_faq_vector_id)

            if attachments:
                vector_store_ids.extend([att["vector_store_id"] for att in attachments if "vector_store_id" in att])
                content_parts = self._build_content_parts_with_attachments(
                    user_info, message_content, attachments
                )
                agent_input = [{"role": "user", "content": content_parts}]

                att_summary = f"{len(attachments)} files"
                if vector_store_ids:
                    att_summary += f" ({len(vector_store_ids)} PDFs)"
                logger.info(f"📎 Message with attachments: {att_summary}")
            else:
                # Construir mensaje simple con user_info (NO company_info)
                user_message = self._build_message_simple(user_info, message_content)
                agent_input = user_message

            # 3. Crear agente (multi-agent system)
            agent_start = time.time()

            agent = await handoffs_manager.get_supervisor_agent(
                thread_id=str(conversation.id), db=db, user_id=str(user_id),
                vector_store_ids=vector_store_ids, channel="whatsapp"
            )
            all_agents = await handoffs_manager.get_all_agents(
                thread_id=str(conversation.id), db=db, user_id=str(user_id),
                vector_store_ids=vector_store_ids, channel="whatsapp"
            )

            if vector_store_ids:
                logger.info(f"📄 Multi-agent with {len(vector_store_ids)} PDF(s)")

            agent_time = time.time() - agent_start
            logger.info(f"⏱️  Agent init: {agent_time:.3f}s")

            # 4. Contexto
            from app.agents.core import FizkoContext
            from chatkit.types import ThreadMetadata
            from datetime import datetime, timezone

            thread_metadata = ThreadMetadata(
                id=str(conversation.id),
                created_at=conversation.created_at or datetime.now(timezone.utc),
                metadata={"channel": "whatsapp"},
            )

            agent_context = FizkoContext(
                thread=thread_metadata, store=None,
                request_context={"user_id": str(user_id), "company_id": str(company_id)},
                current_agent_type="fizko_agent",
            )
            # NOTE: NO LONGER SETTING company_info - agents use search_company_memory() on-demand

            # 5. Sesión
            # Usar conversation.id para mantener historial persistente entre mensajes
            session = SQLiteSession(str(conversation.id), self.session_file)

            logger.info(f"📝 Session created with conversation_id: {conversation.id}")

            # 6. Ejecutar agente con session_input_callback
            runner_start = time.time()
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Runner.run() started")

            # Formatear user_info una sola vez para inyectar en el primer mensaje
            # NOTE: NO LONGER INJECTING company_context - agents use search_company_memory() on-demand
            user_context = f"""<user_info>
Nombre: {user_info.get('name', 'Usuario')}
Email: {user_info.get('email', 'N/A')}
</user_info>

"""

            # Session input callback para mantener historial + inyectar user context
            from agents import RunConfig

            def session_input_callback(history, new_input):
                """
                Merge conversation history with new input.
                On first message, inject user_context only (company context on-demand via memory).
                """
                # Inyectar user_context SOLO en el primer mensaje (history vacío)
                if len(history) == 0:
                    # Solo inyectar user_context (company context on-demand)
                    history = [{
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_context}]
                    }]
                    logger.info(f"📋 Injected user_context into session history ({len(user_context)} chars)")

                # Merge new input
                if isinstance(new_input, list) and len(new_input) > 0:
                    if isinstance(new_input[0], dict) and 'role' in new_input[0]:
                        return history + new_input
                    else:
                        return history + [{"role": "user", "content": new_input}]
                elif isinstance(new_input, str):
                    return history + [{"role": "user", "content": [{"type": "input_text", "text": new_input}]}]
                else:
                    return history + [{"role": "user", "content": [{"type": "input_text", "text": str(new_input)}]}]

            run_config = RunConfig(session_input_callback=session_input_callback)

            result = await Runner.run(
                agent, agent_input, context=agent_context,
                session=session, max_turns=10, run_config=run_config
            )

            runner_time = time.time() - runner_start
            logger.info(f"⏱️  Runner.run(): {runner_time:.3f}s")

            # 7. Extraer y guardar respuesta
            response_text = self._extract_text_from_result(result)

            if save_assistant_message:
                save_start = time.time()
                await WhatsAppConversationManager.add_message(
                    db=db, conversation_id=conversation.id, user_id=user_id,
                    content=response_text, role="assistant", conversation=conversation
                )
                save_time = time.time() - save_start
                logger.info(f"  ⏱️  DB: add_message(assistant): {save_time:.3f}s")

            total_time = time.time() - process_start
            logger.info(f"✅ Complete: {total_time:.3f}s | response={len(response_text)} chars")
            logger.info("=" * 80)

            # Retornar datos adicionales para guardar mensaje del usuario en background
            return (response_text, conversation.id, message_content, message_id)

    async def _cleanup_old_session_history(
        self,
        conversation_id: UUID,
        session: SQLiteSession,
    ) -> None:
        """
        Limpia el historial de mensajes de SQLite si han pasado más de 2 horas
        desde la última actividad en la sesión.

        Esto ayuda a:
        1. Reducir el contexto cuando la conversación ha estado inactiva
        2. Evitar que el agente use información muy antigua
        3. Mantener el contexto fresco y relevante

        Args:
            conversation_id: ID de la conversación de WhatsApp
            session: Sesión SQLite del agente
        """
        from datetime import datetime, timedelta, timezone

        try:
            import sqlite3

            # Abrir conexión SQLite usando el db_path del session
            conn = sqlite3.connect(session.db_path)
            cursor = conn.cursor()

            # Consultar el updated_at de la sesión
            cursor.execute(
                "SELECT updated_at FROM agent_sessions WHERE session_id = ?",
                (str(conversation_id),)
            )
            result = cursor.fetchone()
            conn.close()

            if not result:
                # No hay sesión previa, no hay nada que limpiar
                logger.debug(f"📭 No previous session found for {conversation_id}")
                return

            # Parsear el timestamp (SQLite almacena como string)
            last_activity_str = result[0]
            last_activity_time = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))

            # Asegurar que tiene timezone
            if last_activity_time.tzinfo is None:
                last_activity_time = last_activity_time.replace(tzinfo=timezone.utc)

            # Calcular tiempo transcurrido
            now = datetime.now(timezone.utc)
            time_since_last_activity = now - last_activity_time
            threshold = timedelta(hours=2)

            if time_since_last_activity > threshold:
                # Han pasado más de 2 horas, limpiar el historial
                hours_passed = time_since_last_activity.total_seconds() / 3600
                logger.info(f"🧹 Cleaning session history for {conversation_id}")
                logger.info(f"   Time since last activity: {hours_passed:.1f} hours (threshold: 2h)")

                # Limpiar el historial de SQLite usando el método correcto
                session.clear_session()

                logger.info(f"✅ Session history cleared (fresh context started)")
            else:
                # Todavía dentro de las 2 horas, mantener el historial
                minutes_passed = time_since_last_activity.total_seconds() / 60
                logger.debug(f"⏱️  Time since last activity: {minutes_passed:.1f} minutes (keeping history)")

        except Exception as e:
            # Si hay error consultando SQLite, no bloquear - solo log
            logger.warning(f"⚠️ Failed to check session history age: {e}")
            logger.debug(f"   Continuing without cleanup")

    def _build_message_simple(
        self, user_info: dict, message: str
    ) -> str:
        """
        Construye el mensaje SIN contexto de company ni user_info (se inyectan en session_input_callback).
        Solo incluye el mensaje del usuario.

        Nota: El contexto de notificaciones ya está anclado como mensaje assistant
        en el historial, por lo que el agente lo verá automáticamente.
        """
        # Ya no inyectamos user_context aquí - se hace en session_input_callback
        return message

    def _build_content_parts_with_attachments(
        self,
        user_info: dict,
        message: str,
        attachments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Construye content_parts con attachments para el agente (formato OpenAI).
        SIN inyectar company_context ni user_info (se hacen en session_input_callback).

        Nota: El contexto de notificaciones ya está anclado como mensaje assistant
        en el historial.

        Args:
            user_info: Información del usuario (no usado, mantenido por compatibilidad)
            message: Mensaje de texto del usuario
            attachments: Lista de attachments procesados por WhatsAppMediaProcessor

        Returns:
            Lista de content_parts en formato OpenAI Agents:
            [
                {"type": "input_text", "text": "..."},
                {"type": "input_image", "image_url": "data:image/jpeg;base64,..."},
                ...
            ]
        """
        content_parts = []

        # 1. Agregar mensaje de usuario (ya no agregamos user_context - se hace en session_input_callback)
        content_parts.append({
            "type": "input_text",
            "text": message
        })

        # 2. Agregar attachments según su tipo
        for att in attachments:
            mime_type = att.get("mime_type", "")
            filename = att.get("filename", "archivo")

            if mime_type.startswith("image/"):
                base64_data = att.get("base64")

                if base64_data:
                    data_url = f"data:{mime_type};base64,{base64_data}"
                    content_parts.append({
                        "type": "input_image",
                        "image_url": data_url
                    })
                else:
                    content_parts.append({
                        "type": "input_text",
                        "text": f"[Imagen no disponible: {filename}]"
                    })

            elif mime_type == "application/pdf":
                vector_store_id = att.get("vector_store_id")

                if vector_store_id:
                    content_parts.append({
                        "type": "input_text",
                        "text": f"El usuario ha adjuntado el documento PDF '{filename}'. Usa la herramienta file_search para leer y analizar su contenido."
                    })
                else:
                    content_parts.append({
                        "type": "input_text",
                        "text": f"[Documento PDF adjunto: {filename}]"
                    })

            else:
                content_parts.append({
                    "type": "input_text",
                    "text": f"[Archivo adjunto: {filename} ({mime_type})]"
                })

        return content_parts

    def _extract_text_from_result(self, result) -> str:
        """
        Extrae el texto de result.new_items.
        Ignora widgets y reasoning (solo extrae MessageOutputItem).
        """
        text_parts: List[str] = []

        # Iterar sobre los nuevos items generados
        for item in result.new_items:
            item_type = type(item).__name__

            # Procesar MessageOutputItem (respuestas del asistente)
            if item_type == "MessageOutputItem":
                if hasattr(item, "raw_item") and hasattr(item.raw_item, "content"):
                    for content_part in item.raw_item.content:
                        # Extraer texto
                        if hasattr(content_part, "text") and content_part.text:
                            text_parts.append(content_part.text)

        # Consolidar y limpiar
        full_text = "".join(text_parts).strip()

        if not full_text:
            return "Lo siento, no pude procesar tu mensaje. ¿Puedes reformularlo?"

        return full_text

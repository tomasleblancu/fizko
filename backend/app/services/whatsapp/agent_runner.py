"""
Runner del agente de IA para WhatsApp
Soporta tanto el agente unificado (legacy) como el nuevo sistema multi-agente
"""
import logging
import os
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from agents import Runner, SQLiteSession
from openai import AsyncOpenAI

from app.agents.orchestration import create_unified_agent, handoffs_manager
from app.agents.core import load_company_info, format_company_context
from app.config.database import AsyncSessionLocal
from .conversation_manager import WhatsAppConversationManager

logger = logging.getLogger(__name__)

# In-memory cache for user info (30 minute TTL)
_user_info_cache: Dict[str, tuple[datetime, Dict[str, Any]]] = {}
_USER_CACHE_TTL_SECONDS = 1800  # 30 minutes

# In-memory cache for company info (30 minute TTL)
_company_info_cache: Dict[str, tuple[datetime, Dict[str, Any]]] = {}
_COMPANY_CACHE_TTL_SECONDS = 1800  # 30 minutes


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


async def load_company_info_cached(db, company_id: UUID, use_cache: bool = True) -> Dict[str, Any]:
    """
    Load company information with in-memory caching.

    Args:
        db: Database session
        company_id: Company UUID
        use_cache: Whether to use cache (default: True)

    Returns:
        Dict with company info (same structure as load_company_info from app.agents.core)
    """
    cache_key = str(company_id)

    # Check cache first
    if use_cache and cache_key in _company_info_cache:
        cached_time, cached_data = _company_info_cache[cache_key]
        cache_age = (datetime.now() - cached_time).total_seconds()

        if cache_age < _COMPANY_CACHE_TTL_SECONDS:
            return cached_data
        else:
            del _company_info_cache[cache_key]

    # Fetch from DB using the existing load_company_info function
    company_info = await load_company_info(db, company_id)

    # Store in cache
    if use_cache:
        _company_info_cache[cache_key] = (datetime.now(), company_info)

    return company_info


class WhatsAppAgentRunner:
    """
    Ejecuta agentes de Fizko para mensajes de WhatsApp.

    Soporta dos modos:
    - unified: Agente único con todas las tools (legacy)
    - multi_agent: Sistema de handoffs con supervisor + agentes especializados (nuevo)
    """

    def __init__(self, mode: str = "multi_agent"):
        """
        Inicializa el runner.

        Args:
            mode: "unified" (agente único) o "multi_agent" (sistema con handoffs)
        """
        self.mode = mode
        logger.info(f"🤖 WhatsAppAgentRunner initialized in '{mode}' mode")

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
        logger.info(f"🚀 WhatsApp Agent | user={user_id} | mode={self.mode}")

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

            # Operación 3: Cargar company_info
            company_start = time.time()
            company_info = await load_company_info_cached(db, company_id)
            company_time = time.time() - company_start
            cache_hit_company = company_time < 0.05
            logger.info(f"  ⏱️  DB: load_company_info_cached: {company_time:.3f}s (cache_hit: {cache_hit_company})")

            # Operación 4: Cargar user_info
            user_start = time.time()
            user_info = await load_user_info_cached(db, user_id)
            user_time = time.time() - user_start
            cache_hit_user = user_time < 0.05
            logger.info(f"  ⏱️  DB: load_user_info_cached: {user_time:.3f}s (cache_hit: {cache_hit_user})")

            setup_time = time.time() - setup_start
            logger.info(f"⏱️  Setup total: {setup_time:.3f}s | conv_id={conversation.id}")
            logger.info(f"    └─ Breakdown: conv={conv_time:.3f}s + company={company_time:.3f}s + user={user_time:.3f}s")

            # 2. Preparar mensaje (sin inyectar company_context aquí - se hace en session_input_callback)
            vector_store_ids = []
            if attachments:
                vector_store_ids = [att["vector_store_id"] for att in attachments if "vector_store_id" in att]
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

            # 3. Crear agente
            agent_start = time.time()
            openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            if self.mode == "multi_agent":
                agent = await handoffs_manager.get_supervisor_agent(
                    thread_id=str(conversation.id), db=db, user_id=str(user_id),
                    vector_store_ids=vector_store_ids
                )
                all_agents = await handoffs_manager.get_all_agents(
                    thread_id=str(conversation.id), db=db, user_id=str(user_id),
                    vector_store_ids=vector_store_ids
                )

                if vector_store_ids:
                    logger.info(f"📄 Multi-agent with {len(vector_store_ids)} PDF(s)")
            else:
                agent = create_unified_agent(
                    db=db, openai_client=openai_client,
                    vector_store_ids=vector_store_ids if vector_store_ids else None,
                    channel="whatsapp"
                )
                all_agents = None

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
            agent_context.company_info = company_info

            # 5. Sesión
            # Usar conversation.id para mantener historial persistente entre mensajes
            session = SQLiteSession(str(conversation.id), self.session_file)
            logger.info(f"📝 Session created with conversation_id: {conversation.id}")

            # 6. Ejecutar agente con session_input_callback
            runner_start = time.time()
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Runner.run() started")

            # Preparar company_context para inyectar en el primer mensaje
            from app.agents.core import format_company_context
            company_context = format_company_context(company_info)

            # Session input callback para mantener historial + inyectar contexto
            from agents import RunConfig

            def session_input_callback(history, new_input):
                """
                Merge conversation history with new input.
                On first message, inject company_context as system-level context.
                """
                # Inyectar company_context en el primer mensaje (history vacío)
                if len(history) == 0 and company_context:
                    history = [{
                        "role": "user",
                        "content": [{"type": "input_text", "text": company_context}]
                    }]
                    logger.debug(f"📋 Injected company_context into session history ({len(company_context)} chars)")

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

    def _build_message_simple(
        self, user_info: dict, message: str
    ) -> str:
        """
        Construye el mensaje SIN contexto de company (se inyecta en session_input_callback).
        Solo incluye user_info + mensaje del usuario.

        Nota: El contexto de notificaciones ya está anclado como mensaje assistant
        en el historial, por lo que el agente lo verá automáticamente.
        """
        # Contexto de usuario (específico de WhatsApp)
        user_context = f"""<user_info>
Nombre: {user_info.get('name', 'Usuario')}
Email: {user_info.get('email', 'N/A')}
</user_info>

"""

        return f"{user_context}{message}"

    def _build_content_parts_with_attachments(
        self,
        user_info: dict,
        message: str,
        attachments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Construye content_parts con attachments para el agente (formato OpenAI).
        SIN inyectar company_context (se hace en session_input_callback).

        Nota: El contexto de notificaciones ya está anclado como mensaje assistant
        en el historial.

        Args:
            user_info: Información del usuario
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

        # 1. Construir contexto de usuario (SIN company)
        user_context = f"""<user_info>
Nombre: {user_info.get('name', 'Usuario')}
Email: {user_info.get('email', 'N/A')}
</user_info>

"""

        # Agregar contexto como primer content part
        content_parts.append({
            "type": "input_text",
            "text": user_context
        })

        # 2. Agregar mensaje de usuario
        content_parts.append({
            "type": "input_text",
            "text": message
        })

        # 3. Agregar attachments según su tipo
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

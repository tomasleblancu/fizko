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
        save_assistant_message: bool = True,  # Si False, no guarda la respuesta del agente
        ui_context_text: Optional[str] = None,  # Contexto de UI Tools (ej: notificaciones)
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
            save_assistant_message: Si True, guarda el mensaje del asistente (default: True)
            ui_context_text: Contexto adicional de UI Tools (ej: notificaciones)
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
            # 1. Setup: conversation + messages + context (paralelo internamente)
            setup_start = time.time()

            conversation = await WhatsAppConversationManager.get_or_create_conversation(
                db=db, user_id=user_id, conversation_id=conversation_id
            )

            await WhatsAppConversationManager.add_message(
                db=db, conversation_id=conversation.id, user_id=user_id,
                content=message_content, role="user", message_id=message_id,
                conversation=conversation
            )

            company_info = await load_company_info(db, company_id)
            user_info = await load_user_info_cached(db, user_id)

            setup_time = time.time() - setup_start
            logger.info(f"⏱️  Setup: {setup_time:.3f}s | conv_id={conversation.id}")

            # 2. Preparar mensaje
            vector_store_ids = []
            if attachments:
                vector_store_ids = [att["vector_store_id"] for att in attachments if "vector_store_id" in att]
                content_parts = self._build_content_parts_with_attachments(
                    company_info, user_info, message_content, ui_context_text, attachments
                )
                agent_input = [{"role": "user", "content": content_parts}]

                att_summary = f"{len(attachments)} files"
                if vector_store_ids:
                    att_summary += f" ({len(vector_store_ids)} PDFs)"
                logger.info(f"📎 Message with attachments: {att_summary}")
            else:
                user_message = self._build_message_with_context(
                    company_info, user_info, message_content, ui_context_text
                )
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
            # TEMPORAL: Nueva sesión para evitar historial
            logger.warning("⚠️  TEMP: Using fresh session (no history)")
            import uuid
            temp_session_id = str(uuid.uuid4())
            session = SQLiteSession(temp_session_id, self.session_file)

            # 6. Ejecutar agente
            runner_start = time.time()
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Runner.run() started")

            # Para content_parts necesitamos session_input_callback (como ChatKit)
            if attachments:
                from agents import RunConfig

                def session_input_callback(history, new_input):
                    """Merge conversation history with new input."""
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
            else:
                result = await Runner.run(
                    agent, agent_input, context=agent_context,
                    session=session, max_turns=10
                )

            runner_time = time.time() - runner_start
            logger.info(f"⏱️  Runner.run(): {runner_time:.3f}s")

            # 7. Extraer y guardar respuesta
            response_text = self._extract_text_from_result(result)

            if save_assistant_message:
                await WhatsAppConversationManager.add_message(
                    db=db, conversation_id=conversation.id, user_id=user_id,
                    content=response_text, role="assistant", conversation=conversation
                )

            total_time = time.time() - process_start
            logger.info(f"✅ Complete: {total_time:.3f}s | response={len(response_text)} chars")
            logger.info("=" * 80)

            return (response_text, conversation.id)

    def _build_message_with_context(
        self, company_info: dict, user_info: dict, message: str, ui_context_text: Optional[str] = None
    ) -> str:
        """
        Construye el mensaje con contexto completo.
        Usa el mismo formato que ChatKit para consistencia.
        """
        from app.agents.core import format_company_context

        # Contexto de empresa (mismo formato que ChatKit)
        company_context = format_company_context(company_info)

        # Contexto de usuario (específico de WhatsApp)
        user_context = f"""<user_info>
Nombre: {user_info.get('name', 'Usuario')}
Email: {user_info.get('email', 'N/A')}
</user_info>

"""

        # Contexto adicional de UI Tools (si existe)
        ui_context = ""
        if ui_context_text:
            ui_context = f"""<ui_context>
{ui_context_text}
</ui_context>

"""

        return f"{company_context}{user_context}{ui_context}{message}"

    def _build_content_parts_with_attachments(
        self,
        company_info: dict,
        user_info: dict,
        message: str,
        ui_context_text: Optional[str],
        attachments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Construye content_parts con attachments para el agente (formato OpenAI).
        Similar a _convert_attachments_to_content de ChatKit pero adaptado para WhatsApp.

        Args:
            company_info: Información de la empresa
            user_info: Información del usuario
            message: Mensaje de texto del usuario
            ui_context_text: Contexto de UI Tools (opcional)
            attachments: Lista de attachments procesados por WhatsAppMediaProcessor

        Returns:
            Lista de content_parts en formato OpenAI Agents:
            [
                {"type": "input_text", "text": "..."},
                {"type": "input_image", "image_url": "data:image/jpeg;base64,..."},
                ...
            ]
        """
        from app.agents.core import format_company_context

        content_parts = []

        # 1. Construir contexto completo (empresa + usuario + UI)
        company_context = format_company_context(company_info)

        user_context = f"""<user_info>
Nombre: {user_info.get('name', 'Usuario')}
Email: {user_info.get('email', 'N/A')}
</user_info>

"""

        ui_context = ""
        if ui_context_text:
            ui_context = f"""<ui_context>
{ui_context_text}
</ui_context>

"""

        # Combinar contextos
        full_context = f"{company_context}{user_context}{ui_context}"

        # Agregar contexto como primer content part si existe
        if full_context.strip():
            content_parts.append({
                "type": "input_text",
                "text": full_context
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

"""
Runner del agente de IA para WhatsApp
Invoca el agente unificado directamente (sin pasar por ChatKit)
"""
import logging
import os
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from agents import Runner, SQLiteSession
from openai import AsyncOpenAI

from app.agents.unified_agent import create_unified_agent
from app.agents.context_loader import load_company_info, format_company_context
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
    import time
    load_start = time.time()

    cache_key = str(user_id)

    # Check cache first
    if use_cache and cache_key in _user_info_cache:
        cached_time, cached_data = _user_info_cache[cache_key]
        cache_age = (datetime.now() - cached_time).total_seconds()

        if cache_age < _USER_CACHE_TTL_SECONDS:
            logger.info(f"  💾 User cache HIT: {cache_age:.1f}s old ({(time.time() - load_start):.3f}s)")
            return cached_data
        else:
            logger.info(f"  💾 User cache EXPIRED: {cache_age:.1f}s old")
            del _user_info_cache[cache_key]

    logger.info(f"  💾 User cache MISS - fetching from DB")

    # Fetch from DB
    from app.db.models import Profile
    from sqlalchemy import select

    query_start = time.time()
    result = await db.execute(select(Profile).where(Profile.id == user_id))
    profile = result.scalar_one_or_none()
    logger.info(f"  🔍 User query: {(time.time() - query_start):.3f}s")

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
        logger.info(f"  💾 User info cached for {_USER_CACHE_TTL_SECONDS}s")

    return user_info


class WhatsAppAgentRunner:
    """
    Ejecuta el agente unificado de Fizko para mensajes de WhatsApp.
    Comparte el mismo agente y herramientas que el canal web.
    """

    def __init__(self):
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

        Returns:
            tuple[str, Optional[UUID]]: (respuesta del agente, conversation_id en DB)
        """
        import time
        process_start = time.time()
        logger.info("=" * 80)
        logger.info("🚀 [WHATSAPP AGENT START]")
        logger.info(f"⏱️  [+0.000s] Process started")

        async with AsyncSessionLocal() as db:
            # 1. Obtener o crear conversación
            step_start = time.time()
            conversation = await WhatsAppConversationManager.get_or_create_conversation(
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            )
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Conversation loaded ({time.time() - step_start:.3f}s)")

            # 2. Guardar mensaje del usuario (pasar conversación para evitar query adicional)
            step_start = time.time()
            await WhatsAppConversationManager.add_message(
                db=db,
                conversation_id=conversation.id,
                user_id=user_id,
                content=message_content,
                role="user",
                message_id=message_id,
                conversation=conversation,  # Pasar conversación para optimización
            )
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] User message saved ({time.time() - step_start:.3f}s)")

            # 3. Cargar info de empresa (mismo método que ChatKit)
            step_start = time.time()
            company_info = await load_company_info(db, company_id)
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Company info loaded ({time.time() - step_start:.3f}s)")

            # 4. Cargar info de usuario con caché
            step_start = time.time()
            user_info = await load_user_info_cached(db, user_id)
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] User info loaded ({time.time() - step_start:.3f}s)")

            # 5. Preparar mensaje con contexto completo
            step_start = time.time()
            user_message = self._build_message_with_context(
                company_info, user_info, message_content
            )
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Message with context built ({time.time() - step_start:.3f}s)")

            # 6. Crear cliente OpenAI
            step_start = time.time()
            openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] OpenAI client created ({time.time() - step_start:.3f}s)")

            # 7. Crear agente unificado (mismo que usa el web)
            step_start = time.time()
            agent = create_unified_agent(db=db, openai_client=openai_client)
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Agent created ({time.time() - step_start:.3f}s)")

            # 8. Crear contexto del agente (mismo que ChatKit)
            step_start = time.time()
            from app.agents.context import FizkoContext
            from chatkit.types import ThreadMetadata
            from datetime import datetime, timezone

            # Crear thread metadata mínimo para WhatsApp
            thread_metadata = ThreadMetadata(
                id=str(conversation.id),
                created_at=conversation.created_at or datetime.now(timezone.utc),
                metadata={"channel": "whatsapp"},
            )

            agent_context = FizkoContext(
                thread=thread_metadata,
                store=None,   # WhatsApp no usa store de ChatKit
                request_context={
                    "user_id": str(user_id),
                    "company_id": str(company_id),
                },
                current_agent_type="fizko_agent",
            )
            agent_context.company_info = company_info
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Agent context created ({time.time() - step_start:.3f}s)")

            # Log para debug
            logger.info(f"🔍 WhatsApp Agent Context: user_id={user_id}, company_id={company_id}")
            logger.info(f"📋 Company info loaded: {bool(company_info and 'company' in company_info)}")

            # 9. Crear sesión para historial
            step_start = time.time()
            session = SQLiteSession(str(conversation.id), self.session_file)
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Session created ({time.time() - step_start:.3f}s)")

            # Log del mensaje completo para debug
            logger.info(f"📝 Mensaje enviado al agente (primeros 500 chars): {user_message[:500]}")

            # TEMPORAL: Limpiar historial para forzar nueva conversación
            logger.warning("⚠️ TEMPORAL: Creando nueva sesión para evitar historial previo")
            import uuid
            temp_session_id = str(uuid.uuid4())
            session = SQLiteSession(temp_session_id, self.session_file)
            logger.info(f"🆕 Usando sesión temporal: {temp_session_id}")

            # 10. Ejecutar agente con el contexto correcto
            step_start = time.time()
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Runner.run() started")
            result = await Runner.run(
                agent,
                user_message,
                context=agent_context,
                session=session,
                max_turns=10,
            )
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Runner.run() completed ({time.time() - step_start:.3f}s)")

            # 11. Extraer texto del resultado
            step_start = time.time()
            response_text = self._extract_text_from_result(result)
            logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Text extracted ({time.time() - step_start:.3f}s)")
            logger.info(f"💬 Response length: {len(response_text)} chars")

            # 12. Guardar respuesta del agente (opcional - se puede hacer después de enviar)
            if save_assistant_message:
                step_start = time.time()
                await WhatsAppConversationManager.add_message(
                    db=db,
                    conversation_id=conversation.id,
                    user_id=user_id,
                    content=response_text,
                    role="assistant",
                    conversation=conversation,  # Pasar conversación para optimización
                )
                logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Assistant message saved ({time.time() - step_start:.3f}s)")
            else:
                logger.info(f"⏱️  [+{time.time() - process_start:.3f}s] Assistant message save skipped (will save after send)")

            total_time = time.time() - process_start
            logger.info(f"✅ [WHATSAPP AGENT COMPLETE] Total time: {total_time:.3f}s")
            logger.info("=" * 80)

            return (response_text, conversation.id)

    def _build_message_with_context(
        self, company_info: dict, user_info: dict, message: str
    ) -> str:
        """
        Construye el mensaje con contexto completo.
        Usa el mismo formato que ChatKit para consistencia.
        """
        from app.agents.context_loader import format_company_context

        # Contexto de empresa (mismo formato que ChatKit)
        company_context = format_company_context(company_info)

        # Contexto de usuario (específico de WhatsApp)
        user_context = f"""<user_info>
Nombre: {user_info.get('name', 'Usuario')}
Email: {user_info.get('email', 'N/A')}
</user_info>

"""

        return f"{company_context}{user_context}{message}"

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

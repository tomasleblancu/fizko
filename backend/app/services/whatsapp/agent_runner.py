"""
Runner del agente de IA para WhatsApp
Invoca el agente unificado directamente (sin pasar por ChatKit)
"""
import logging
import os
from typing import Optional, List
from uuid import UUID

from agents import Runner, SQLiteSession
from openai import AsyncOpenAI

from app.agents.unified_agent import create_unified_agent
from app.agents.context_loader import load_company_info, format_company_context
from app.config.database import AsyncSessionLocal
from .conversation_manager import WhatsAppConversationManager

logger = logging.getLogger(__name__)


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
    ) -> str:
        """
        Procesa un mensaje del usuario y retorna la respuesta del agente.

        Args:
            user_id: ID del usuario autenticado
            company_id: ID de la empresa del usuario
            message_content: Contenido del mensaje
            conversation_id: ID de conversación de Kapso (opcional)
            message_id: ID del mensaje de Kapso (opcional)

        Returns:
            str: Respuesta del agente (texto consolidado)
        """

        async with AsyncSessionLocal() as db:
            # 1. Obtener o crear conversación
            conversation = await WhatsAppConversationManager.get_or_create_conversation(
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            )

            # 2. Guardar mensaje del usuario
            await WhatsAppConversationManager.add_message(
                db=db,
                conversation_id=conversation.id,
                user_id=user_id,
                content=message_content,
                role="user",
                message_id=message_id,
            )

            # 3. Cargar info de empresa (mismo método que ChatKit)
            company_info = await load_company_info(db, company_id)

            # 4. Cargar info de usuario (usando módulo compartido para user también)
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

            # 5. Preparar mensaje con contexto completo
            user_message = self._build_message_with_context(
                company_info, user_info, message_content
            )

            # 6. Crear cliente OpenAI
            openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # 7. Crear agente unificado (mismo que usa el web)
            agent = create_unified_agent(db=db, openai_client=openai_client)

            # 8. Crear contexto del agente (mismo que ChatKit)
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

            # Log para debug
            logger.info(f"🔍 WhatsApp Agent Context: user_id={user_id}, company_id={company_id}")
            logger.info(f"📋 Company info loaded: {bool(company_info and 'company' in company_info)}")

            # 9. Crear sesión para historial
            session = SQLiteSession(str(conversation.id), self.session_file)

            # Log del mensaje completo para debug
            logger.info(f"📝 Mensaje enviado al agente (primeros 500 chars): {user_message[:500]}")

            # TEMPORAL: Limpiar historial para forzar nueva conversación
            logger.warning("⚠️ TEMPORAL: Creando nueva sesión para evitar historial previo")
            import uuid
            temp_session_id = str(uuid.uuid4())
            session = SQLiteSession(temp_session_id, self.session_file)
            logger.info(f"🆕 Usando sesión temporal: {temp_session_id}")

            # 10. Ejecutar agente con el contexto correcto
            result = await Runner.run(
                agent,
                user_message,
                context=agent_context,
                session=session,
                max_turns=10,
            )

            # 11. Extraer texto del resultado
            response_text = self._extract_text_from_result(result)

            # 12. Guardar respuesta del agente
            await WhatsAppConversationManager.add_message(
                db=db,
                conversation_id=conversation.id,
                user_id=user_id,
                content=response_text,
                role="assistant",
            )

            return response_text

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

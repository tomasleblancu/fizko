"""
Gestión de conversaciones de WhatsApp en Supabase
Utiliza las mismas tablas que ChatKit (conversations, messages)
Se diferencia por el campo metadata
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Message, Session, Profile, Company
from app.config.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class WhatsAppConversationManager:
    """
    Gestiona conversaciones de WhatsApp usando las tablas existentes de Supabase.
    Se diferencia de conversaciones web mediante metadata.
    """

    @staticmethod
    async def get_or_create_conversation(
        db: AsyncSession,
        user_id: UUID,
        company_id: UUID,
        conversation_id: Optional[str] = None,  # Kapso conversation_id
        phone_number: Optional[str] = None,
    ) -> Conversation:
        """
        Busca o crea una conversación de WhatsApp.
        OPTIMIZADO: Cachea user_id y company_id en metadata para evitar autenticación.

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario autenticado
            company_id: ID de la empresa del usuario
            conversation_id: ID de conversación de Kapso (opcional)
            phone_number: Número de teléfono del usuario (opcional)

        Returns:
            Conversation: Conversación existente o nueva
        """
        import time

        # Si tenemos conversation_id de Kapso, buscar directamente por ID
        if conversation_id:
            query_start = time.time()
            result = await db.execute(
                select(Conversation).where(Conversation.id == UUID(conversation_id))
            )
            existing_conv = result.scalar_one_or_none()
            query_time = time.time() - query_start

            if existing_conv:
                logger.debug(f"    ⏱️  Found existing conversation by ID (query: {query_time:.3f}s)")
                return existing_conv

        # Si no hay conversation_id o no existe, buscar conversación reciente del usuario
        query_start = time.time()
        result = await db.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.meta_data.op("->>")(
                        "channel"
                    ) == "whatsapp",
                )
            )
            .order_by(desc(Conversation.updated_at))
            .limit(1)
        )
        recent_conv = result.scalar_one_or_none()
        query_time = time.time() - query_start

        if recent_conv:
            recent_conv.updated_at = datetime.now(timezone.utc)
            await db.commit()
            logger.debug(f"    ⏱️  Using recent conversation (query: {query_time:.3f}s)")
            return recent_conv

        # Crear nueva conversación con metadata completo (cachea auth)
        # Use Kapso conversation_id as our Conversation.id if available
        create_start = time.time()
        metadata = {
            "channel": "whatsapp",
            "created_via": "whatsapp_webhook",
            "user_id": str(user_id),  # Cachear para evitar autenticación
            "company_id": str(company_id),  # Cachear company_id
        }

        if phone_number:
            metadata["phone_number"] = phone_number

        # If we have conversation_id, use it as the UUID primary key
        if conversation_id:
            new_conversation = Conversation(
                id=UUID(conversation_id),  # Use Kapso ID directly!
                user_id=user_id,
                meta_data=metadata,
            )
        else:
            # No conversation_id, let PostgreSQL generate UUID
            new_conversation = Conversation(
                user_id=user_id,
                meta_data=metadata,
            )

        db.add(new_conversation)
        await db.flush()  # Flush para obtener el ID
        await db.commit()  # Commit para que esté disponible en otras sesiones (background tasks)
        create_time = time.time() - create_start

        logger.debug(f"    ⏱️  Created new conversation (create+flush+commit: {create_time:.3f}s)")
        return new_conversation

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
        content: str,
        role: str,  # "user" o "assistant"
        message_id: Optional[str] = None,  # Kapso message_id
        metadata: Optional[Dict[str, Any]] = None,
        conversation: Optional[Conversation] = None,  # Pasar conversación si ya la tenemos
    ) -> Message:
        """
        Guarda un mensaje en la conversación.
        OPTIMIZADO: Acepta conversación como parámetro para evitar query adicional.

        Args:
            db: Sesión de base de datos
            conversation_id: ID de conversación en Supabase
            user_id: ID del usuario
            content: Contenido del mensaje
            role: "user" o "assistant"
            message_id: ID del mensaje de Kapso (opcional)
            metadata: Metadata adicional (opcional)
            conversation: Objeto Conversation si ya está cargado (opcional)

        Returns:
            Message: Mensaje guardado
        """
        import time

        # Preparar metadata
        prep_start = time.time()
        msg_metadata = metadata or {}
        msg_metadata["channel"] = "whatsapp"

        if message_id:
            msg_metadata["whatsapp_message_id"] = message_id

        new_message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=content,
            role=role,
            message_metadata=msg_metadata,
        )

        db.add(new_message)
        prep_time = time.time() - prep_start

        # Actualizar timestamp de conversación
        update_start = time.time()
        if conversation:
            conversation.updated_at = datetime.now(timezone.utc)
        else:
            # Solo hacer query si no tenemos la conversación
            result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conv = result.scalar_one_or_none()
            if conv:
                conv.updated_at = datetime.now(timezone.utc)
            else:
                logger.warning(f"⚠️  Conversation {conversation_id} not found for timestamp update")
        update_time = time.time() - update_start

        # Commit
        commit_start = time.time()
        await db.commit()
        commit_time = time.time() - commit_start

        total_time = prep_time + update_time + commit_time
        logger.debug(f"    ⏱️  add_message({role}) breakdown: prep={prep_time:.3f}s + update={update_time:.3f}s + commit={commit_time:.3f}s = {total_time:.3f}s")

        return new_message

    @staticmethod
    async def get_conversation_history(
        db: AsyncSession,
        conversation_id: UUID,
        limit: int = 20,
    ) -> List[Message]:
        """
        Obtiene el historial de mensajes de una conversación.

        Args:
            db: Sesión de base de datos
            conversation_id: ID de conversación en Supabase
            limit: Número máximo de mensajes a retornar

        Returns:
            List[Message]: Lista de mensajes ordenados por fecha
        """
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(limit)
        )

        messages = result.scalars().all()

        return list(messages)

    @staticmethod
    async def get_user_company_id(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[UUID]:
        """
        Obtiene el company_id del usuario desde la última sesión activa.

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario

        Returns:
            UUID: company_id si existe, None si no
        """
        # Intentar desde sessions (última sesión activa)
        result = await db.execute(
            select(Session)
            .where(and_(Session.user_id == user_id, Session.is_active == True))
            .order_by(desc(Session.last_accessed_at))
            .limit(1)
        )
        session = result.scalar_one_or_none()

        if session and session.company_id:
            return session.company_id

        # Fallback: Obtener cualquier sesión del usuario
        result = await db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(desc(Session.created_at))
            .limit(1)
        )
        session = result.scalar_one_or_none()

        if session and session.company_id:
            return session.company_id

        return None

    @staticmethod
    def get_cached_auth_from_conversation(conversation: Conversation) -> Optional[Dict[str, UUID]]:
        """
        Extrae autenticación cacheada desde metadata de conversación.
        Esto evita queries a BD para autenticar en mensajes subsecuentes.

        Args:
            conversation: Objeto Conversation

        Returns:
            Dict con user_id y company_id, o None si no está cacheado
        """
        if not conversation.meta_data:
            return None

        user_id_str = conversation.meta_data.get("user_id")
        company_id_str = conversation.meta_data.get("company_id")

        if user_id_str and company_id_str:
            try:
                return {
                    "user_id": UUID(user_id_str),
                    "company_id": UUID(company_id_str),
                }
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ Error parsing cached auth from metadata: {e}")
                return None

        return None

    @staticmethod
    async def add_notification_context_message(
        db: AsyncSession,
        conversation_id: UUID,
        notification_context: str,
    ) -> Message:
        """
        Inserta contexto de notificación como mensaje assistant.
        Esto permite que el agente vea el contexto automáticamente en el historial.

        El contexto se guarda como un mensaje assistant con metadata especial.
        Cuando el usuario responde, el agente ya tiene el contexto en su historial.

        Args:
            db: Sesión de base de datos
            conversation_id: ID de la conversación (UUID interno, no Kapso ID)
            notification_context: Texto del contexto (XML o texto estructurado)

        Returns:
            Message: Mensaje guardado
        """
        # Obtener user_id de la conversación
        result = await db.execute(
            select(Conversation.user_id).where(Conversation.id == conversation_id)
        )
        user_id = result.scalar_one()

        # Crear mensaje assistant con metadata especial
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=notification_context,
            message_metadata={
                "channel": "whatsapp",
                "is_notification_context": True,
            },
        )

        db.add(message)
        await db.commit()

        logger.info(f"📌 Contexto de notificación anclado como mensaje assistant")

        return message

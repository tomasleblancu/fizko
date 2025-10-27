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
        conversation_id: Optional[str] = None,  # Kapso conversation_id
    ) -> Conversation:
        """
        Busca o crea una conversación de WhatsApp.
        OPTIMIZADO: Una sola query para buscar por Kapso ID o conversación reciente.

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario autenticado
            conversation_id: ID de conversación de Kapso (opcional)

        Returns:
            Conversation: Conversación existente o nueva
        """
        # Una sola query: buscar por Kapso ID o conversación reciente de WhatsApp
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
            .limit(5)  # Obtener últimas 5 para buscar por Kapso ID
        )
        conversations = result.scalars().all()

        # Primero buscar por Kapso conversation_id si existe
        if conversation_id:
            for conv in conversations:
                if conv.meta_data and conv.meta_data.get("whatsapp_conversation_id") == conversation_id:
                    # No necesitamos commit aquí, solo retornar
                    return conv

        # Si no hay match por Kapso ID, usar la más reciente
        if conversations:
            recent = conversations[0]
            # Actualizar Kapso ID si aplica (sin commit inmediato, se hará con el mensaje)
            if conversation_id and recent.meta_data:
                recent.meta_data = {**recent.meta_data, "whatsapp_conversation_id": conversation_id}
            recent.updated_at = datetime.now(timezone.utc)
            return recent

        # Crear nueva conversación solo si no existe ninguna
        metadata = {
            "channel": "whatsapp",
            "created_via": "whatsapp_webhook",
        }

        if conversation_id:
            metadata["whatsapp_conversation_id"] = conversation_id

        new_conversation = Conversation(
            user_id=user_id,
            meta_data=metadata,
        )

        db.add(new_conversation)
        # No hacer commit aquí - se hará junto con el mensaje
        await db.flush()  # Solo flush para obtener el ID

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

        # Actualizar timestamp de conversación
        # Si ya tenemos el objeto conversation, usarlo directamente
        if conversation:
            conversation.updated_at = datetime.now(timezone.utc)
        else:
            # Solo hacer query si no tenemos la conversación
            result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conv = result.scalar_one()
            conv.updated_at = datetime.now(timezone.utc)

        await db.commit()
        # No necesitamos refresh - el mensaje ya tiene su ID después del commit

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

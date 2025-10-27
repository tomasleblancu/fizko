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

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario autenticado
            conversation_id: ID de conversación de Kapso (opcional)

        Returns:
            Conversation: Conversación existente o nueva
        """
        # Buscar conversación existente por Kapso conversation_id
        if conversation_id:
            result = await db.execute(
                select(Conversation).where(
                    and_(
                        Conversation.user_id == user_id,
                        Conversation.meta_data.op("->>")(
                            "whatsapp_conversation_id"
                        ) == conversation_id,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                return existing

        # Buscar conversación activa reciente del usuario (últimas 24h)
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
        recent = result.scalar_one_or_none()

        if recent:
            # Reusar conversación reciente y actualizar Kapso ID si aplica
            if conversation_id and recent.meta_data:
                recent.meta_data["whatsapp_conversation_id"] = conversation_id

            recent.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(recent)

            return recent

        # Crear nueva conversación
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
        await db.commit()
        await db.refresh(new_conversation)

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
    ) -> Message:
        """
        Guarda un mensaje en la conversación.

        Args:
            db: Sesión de base de datos
            conversation_id: ID de conversación en Supabase
            user_id: ID del usuario
            content: Contenido del mensaje
            role: "user" o "assistant"
            message_id: ID del mensaje de Kapso (opcional)
            metadata: Metadata adicional (opcional)

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
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one()
        conversation.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(new_message)

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

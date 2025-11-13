"""
Servicio de WhatsApp para Fizko
Capa de abstracción sobre el cliente de Kapso
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.integrations.kapso import KapsoClient
from app.integrations.kapso.models import (
    MessageType,
    ConversationStatus,
    SendTextRequest,
    SendMediaRequest,
    SendTemplateRequest,
    SendInteractiveRequest,
)
from app.integrations.kapso.exceptions import (
    KapsoAPIError,
    KapsoAuthenticationError,
    KapsoValidationError,
    KapsoTimeoutError,
)

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Servicio de alto nivel para gestión de WhatsApp en Fizko.
    Envuelve el cliente de Kapso y añade lógica de negocio específica.
    """

    def __init__(self, api_token: str, base_url: Optional[str] = None):
        """
        Inicializa el servicio de WhatsApp

        Args:
            api_token: Token de API de Kapso
            base_url: URL base de la API (opcional)
        """
        self.client = KapsoClient(api_token=api_token, base_url=base_url)

    # ========== Mensajería ==========

    async def send_text(
        self,
        conversation_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        message: str = "",
        whatsapp_config_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Envía un mensaje de texto.
        Si no existe conversation_id, intenta encontrar/crear conversación por teléfono.

        Args:
            conversation_id: ID de conversación existente
            phone_number: Número de teléfono (si no hay conversation_id)
            message: Contenido del mensaje
            whatsapp_config_id: ID de configuración de WhatsApp

        Returns:
            Resultado del envío
        """
        try:
            # Si no hay conversation_id, buscar por teléfono
            if not conversation_id and phone_number and whatsapp_config_id:
                conv = await self._get_or_create_conversation(
                    phone_number=phone_number,
                    whatsapp_config_id=whatsapp_config_id,
                )
                conversation_id = conv.get("id")

            if not conversation_id:
                raise KapsoValidationError(
                    "Se requiere conversation_id o (phone_number + whatsapp_config_id)"
                )

            # Use modular client (client.messages.send_text)
            result = await self.client.messages.send_text(
                conversation_id=conversation_id,
                message=message,
            )

            # Asegurar que conversation_id esté en el resultado
            # (Kapso API puede no incluirlo en la respuesta)
            if "conversation_id" not in result:
                result["conversation_id"] = conversation_id

            logger.info(f"📱 Mensaje de texto enviado a conversación {conversation_id}")
            return result

        except KapsoAPIError as e:
            logger.error(f"❌ Error enviando mensaje de texto: {e}")
            raise

    async def send_media(
        self,
        conversation_id: str,
        media_url: str,
        media_type: MessageType,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Envía un mensaje con media

        Args:
            conversation_id: ID de la conversación
            media_url: URL pública del archivo
            media_type: Tipo de media
            caption: Texto adicional
            filename: Nombre del archivo

        Returns:
            Resultado del envío
        """
        try:
            # Use modular client (client.messages.send_media)
            result = await self.client.messages.send_media(
                conversation_id=conversation_id,
                media_url=media_url,
                media_type=media_type,
                caption=caption,
                filename=filename,
            )

            logger.info(f"📷 Media {media_type} enviado a conversación {conversation_id}")
            return result

        except KapsoAPIError as e:
            logger.error(f"❌ Error enviando media: {e}")
            raise

    async def send_template(
        self,
        phone_number: str,
        template_name: str,
        phone_number_id: str,
        components: Optional[List[Dict[str, Any]]] = None,
        template_language: str = "es_CL",
        whatsapp_config_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Envía una plantilla de WhatsApp Business via Meta API directa.

        Args:
            phone_number: Número de destino (sin +, ej: 56975389973)
            template_name: Nombre de la plantilla aprobada
            phone_number_id: Phone Number ID de WhatsApp Business
            components: Lista de componentes en formato Meta API (header, body, etc.)
            template_language: Código de idioma (ej: es_CL)
            whatsapp_config_id: ID de configuración de WhatsApp (para buscar conversación)

        Returns:
            Resultado del envío con conversation_id agregado
        """
        try:
            # Use modular client (client.templates.send_with_components)
            result = await self.client.templates.send_with_components(
                phone_number=phone_number,
                template_name=template_name,
                phone_number_id=phone_number_id,
                components=components,
                template_language=template_language,
            )

            logger.info(f"📋 Template '{template_name}' enviado a {phone_number}")

            # IMPORTANT: Meta API doesn't return conversation_id when sending templates
            # We need to fetch it by searching for the active conversation
            if whatsapp_config_id:
                try:
                    # Normalize phone number for comparison
                    normalized_phone = phone_number.lstrip('+') if phone_number.startswith('+') else phone_number

                    # List recent conversations for this config
                    conversations = await self.client.conversations.list(
                        whatsapp_config_id=whatsapp_config_id,
                        limit=50,
                    )

                    # Extract conversation list (handle different response formats)
                    nodes = (
                        conversations.get("data") or
                        conversations.get("nodes") or
                        conversations.get("conversations") or
                        conversations.get("items") or
                        []
                    )

                    # Find active conversation matching this phone number
                    for conv in nodes:
                        conv_phone = conv.get("phone_number", "").lstrip('+')
                        conv_status = conv.get("status", "")

                        if conv_phone == normalized_phone and conv_status == "active":
                            conversation_id = conv.get("id")
                            result["conversation_id"] = conversation_id
                            break
                    else:
                        logger.warning(f"⚠️ No active conversation found for {phone_number} after sending template")

                except Exception as e:
                    logger.warning(f"⚠️ Error fetching conversation_id after template send: {e}")
                    # Don't fail the send operation, just log the warning

            return result

        except KapsoAPIError as e:
            logger.error(f"❌ Error enviando template: {e}")
            raise

    async def send_interactive(
        self,
        conversation_id: str,
        interactive_type: str,
        body_text: str,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        buttons: Optional[List[Dict]] = None,
        sections: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Envía un mensaje interactivo (botones o lista)

        Args:
            conversation_id: ID de conversación
            interactive_type: "button" o "list"
            body_text: Texto principal
            header_text: Encabezado
            footer_text: Pie de página
            buttons: Botones (para type=button)
            sections: Secciones (para type=list)

        Returns:
            Resultado del envío
        """
        try:
            result = await self.client.messages.send_interactive(
                conversation_id=conversation_id,
                interactive_type=interactive_type,
                body_text=body_text,
                header_text=header_text,
                footer_text=footer_text,
                buttons=buttons,
                sections=sections,
            )

            logger.info(f"🔘 Mensaje interactivo enviado a {conversation_id}")
            return result

        except KapsoAPIError as e:
            logger.error(f"❌ Error enviando mensaje interactivo: {e}")
            raise

    # ========== Conversaciones ==========

    async def _get_or_create_conversation(
        self,
        phone_number: str,
        whatsapp_config_id: str,
    ) -> Dict[str, Any]:
        """
        Busca una conversación activa existente.

        IMPORTANTE: Para sandbox de Kapso, NO se pueden crear conversaciones nuevas.
        Solo se pueden usar conversaciones que ya existen (iniciadas por el usuario).

        Args:
            phone_number: Número de teléfono (será normalizado automáticamente)
            whatsapp_config_id: ID de configuración

        Returns:
            Conversación existente activa

        Raises:
            ValueError: Si no se encuentra conversación activa
        """
        try:
            # Normalizar número (remover '+' si existe)
            normalized_phone = phone_number.lstrip('+') if phone_number.startswith('+') else phone_number

            # Buscar conversaciones activas (aumentar límite para encontrar el número)
            conversations = await self.client.conversations.list(
                whatsapp_config_id=whatsapp_config_id,
                limit=50,  # Buscar en más conversaciones
            )

            # Buscar en diferentes formatos de respuesta
            nodes = (
                conversations.get("data") or
                conversations.get("nodes") or
                conversations.get("conversations") or
                conversations.get("items") or
                []
            )

            # Buscar conversación activa que coincida con el número
            for conv in nodes:
                conv_phone = conv.get("phone_number", "").lstrip('+')
                conv_status = conv.get("status", "")

                if conv_phone == normalized_phone and conv_status == "active":
                    logger.info(f"✅ Conversación activa encontrada para {normalized_phone}")
                    return conv

            # Si no se encuentra, lanzar error explicativo
            raise ValueError(
                f"No se encontró conversación activa para {normalized_phone}. "
                f"El usuario debe iniciar primero una conversación enviando un mensaje."
            )

        except Exception as e:
            logger.error(f"Error buscando conversación: {e}")
            raise

    async def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtiene detalles de una conversación

        Args:
            conversation_id: ID de la conversación

        Returns:
            Datos de la conversación
        """
        return await self.client.conversations.get(conversation_id=conversation_id)

    async def list_conversations(
        self,
        whatsapp_config_id: Optional[str] = None,
        limit: int = 50,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Lista conversaciones

        Args:
            whatsapp_config_id: Filtrar por configuración
            limit: Límite de resultados
            page: Página

        Returns:
            Lista de conversaciones
        """
        return await self.client.conversations.list(
            whatsapp_config_id=whatsapp_config_id,
            limit=limit,
            page=page,
        )

    async def end_conversation(
        self,
        conversation_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Finaliza una conversación

        Args:
            conversation_id: ID de la conversación
            reason: Razón de finalización

        Returns:
            Conversación actualizada
        """
        return await self.client.conversations.update_status(
            conversation_id=conversation_id,
            status=ConversationStatus.ENDED,
            reason=reason,
        )

    # ========== Contactos ==========

    async def search_contacts(
        self,
        query: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Busca contactos por nombre o teléfono

        Args:
            query: Texto a buscar
            limit: Límite de resultados

        Returns:
            Lista de contactos
        """
        return await self.client.contacts.search(query=query, limit=limit)

    async def get_contact_history(
        self,
        identifier: str,
        message_limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Obtiene el historial de un contacto

        Args:
            identifier: ID o teléfono del contacto
            message_limit: Límite de mensajes

        Returns:
            Historial del contacto
        """
        return await self.client.contacts.get_context(
            identifier=identifier,
            include_recent_messages=True,
            recent_message_limit=message_limit,
        )

    async def add_note_to_contact(
        self,
        contact_identifier: str,
        note: str,
        label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Añade una nota a un contacto

        Args:
            contact_identifier: ID o teléfono
            note: Contenido de la nota
            label: Etiqueta

        Returns:
            Nota creada
        """
        return await self.client.contacts.add_note(
            contact_identifier=contact_identifier,
            content=note,
            name=label,
        )

    # ========== Mensajes ==========

    async def mark_as_read(
        self,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Marca mensajes como leídos

        Args:
            conversation_id: ID de conversación
            message_id: ID de mensaje específico

        Returns:
            Resultado
        """
        return await self.client.messages.mark_as_read(
            conversation_id=conversation_id,
            message_id=message_id,
        )

    async def search_messages(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Busca mensajes por contenido

        Args:
            query: Texto a buscar
            conversation_id: Filtrar por conversación
            limit: Límite de resultados

        Returns:
            Mensajes encontrados
        """
        return await self.client.messages.search(
            query=query,
            conversation_id=conversation_id,
            limit=limit,
        )

    # ========== Templates ==========

    async def list_templates(
        self,
        whatsapp_config_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Lista plantillas disponibles

        Args:
            whatsapp_config_id: Filtrar por configuración

        Returns:
            Lista de plantillas
        """
        return await self.client.templates.list(
            whatsapp_config_id=whatsapp_config_id,
        )

    # ========== Inbox ==========

    async def get_inbox(
        self,
        whatsapp_config_id: str,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene la bandeja de entrada

        Args:
            whatsapp_config_id: ID de configuración
            limit: Límite de conversaciones
            status: Filtrar por estado

        Returns:
            Conversaciones del inbox
        """
        return await self.client.config.get_inbox(
            whatsapp_config_id=whatsapp_config_id,
            limit=limit,
            status=status,
        )

    # ========== Utilidades ==========

    @staticmethod
    def validate_webhook(payload: str, signature: str, secret: str) -> bool:
        """
        Valida la firma de un webhook de Kapso

        Args:
            payload: Payload como string
            signature: Firma recibida
            secret: Secreto del webhook

        Returns:
            True si válido
        """
        # Use modular client (WebhooksAPI has static validation method)
        from app.integrations.kapso.api.webhooks import WebhooksAPI
        return WebhooksAPI.validate_signature(
            payload=payload,
            signature=signature,
            secret=secret,
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado del servicio

        Returns:
            Estado del servicio
        """
        return await self.client.health_check()

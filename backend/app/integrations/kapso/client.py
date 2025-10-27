"""
Cliente para la API de Kapso WhatsApp Business
Adaptado para FastAPI con httpx (async)
"""
import logging
import hmac
import hashlib
from typing import Dict, List, Optional, Any
import httpx

from .models import (
    WhatsAppMessage,
    WhatsAppConversation,
    MessageType,
    ConversationStatus,
)
from .exceptions import (
    KapsoAPIError,
    KapsoAuthenticationError,
    KapsoValidationError,
    KapsoTimeoutError,
    KapsoNotFoundError,
)

logger = logging.getLogger(__name__)


class KapsoClient:
    """
    Cliente para interactuar con la API de Kapso WhatsApp Business.
    Soporta operaciones asíncronas con httpx.

    Ejemplo de uso:
        client = KapsoClient(api_token="your-token")

        # Enviar mensaje de texto
        result = await client.send_text_message(
            conversation_id="conv-123",
            message="Hola, ¿cómo estás?"
        )

        # Enviar plantilla
        result = await client.send_template_message(
            phone_number="+56912345678",
            template_name="welcome_message",
            template_params=["Juan"],
            whatsapp_config_id="config-123"
        )
    """

    def __init__(
        self,
        api_token: str,
        base_url: str = "https://app.kapso.ai/api/v1",
        timeout: int = 30,
    ):
        """
        Inicializa el cliente de Kapso

        Args:
            api_token: Token de API de Kapso
            base_url: URL base de la API
            timeout: Timeout por defecto en segundos
        """
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "X-API-Key": api_token,
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Realiza una petición HTTP a la API de Kapso

        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint de la API (sin base_url)
            data: Datos para enviar en el body
            params: Parámetros de query
            timeout: Timeout personalizado

        Returns:
            Respuesta de la API como dict

        Raises:
            KapsoAPIError: Si hay error en la petición
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout_val = timeout or self.timeout

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=timeout_val,
                )

                # Manejar códigos de estado
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 401:
                    raise KapsoAuthenticationError(
                        "Error de autenticación con Kapso API",
                        status_code=response.status_code,
                        response_data=response.text,
                    )
                elif response.status_code == 404:
                    raise KapsoNotFoundError(
                        "Recurso no encontrado",
                        status_code=response.status_code,
                        response_data=response.text,
                    )
                elif response.status_code == 422:
                    raise KapsoValidationError(
                        f"Error de validación: {response.text[:200]}",
                        status_code=response.status_code,
                        response_data=response.text,
                    )
                else:
                    raise KapsoAPIError(
                        f"Error en Kapso API {response.status_code}: {response.text[:200]}",
                        status_code=response.status_code,
                        response_data=response.text,
                    )

        except httpx.TimeoutException:
            raise KapsoTimeoutError(
                f"Timeout conectando con Kapso API después de {timeout_val}s"
            )
        except (KapsoAPIError, KapsoAuthenticationError, KapsoValidationError, KapsoTimeoutError, KapsoNotFoundError):
            # Re-raise excepciones de Kapso
            raise
        except Exception as e:
            logger.exception(f"Error inesperado en petición a Kapso: {e}")
            raise KapsoAPIError(f"Error inesperado: {str(e)}")

    # ========== Mensajes ==========

    async def send_text_message(
        self,
        conversation_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Envía un mensaje de texto

        Args:
            conversation_id: ID de la conversación
            message: Contenido del mensaje

        Returns:
            Respuesta de la API con detalles del mensaje enviado
        """
        payload = {
            "message": {
                "content": message,
                "message_type": "text",
            }
        }

        result = await self._make_request(
            method="POST",
            endpoint=f"whatsapp_conversations/{conversation_id}/whatsapp_messages",
            data=payload,
        )

        logger.info(f"✅ Mensaje de texto enviado (conv: {conversation_id})")
        return result

    async def send_media_message(
        self,
        conversation_id: str,
        media_url: str,
        media_type: MessageType,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Envía un mensaje con media (imagen, video, audio, documento)

        Args:
            conversation_id: ID de la conversación
            media_url: URL pública del archivo
            media_type: Tipo de media (image, video, audio, document)
            caption: Texto adicional (opcional)
            filename: Nombre del archivo para documentos

        Returns:
            Respuesta de la API
        """
        payload = {
            "message": {
                "message_type": media_type.value if isinstance(media_type, MessageType) else media_type,
                "media_url": media_url,
            }
        }

        if caption:
            payload["message"]["caption"] = caption
        if filename and media_type == MessageType.DOCUMENT:
            payload["message"]["filename"] = filename

        result = await self._make_request(
            method="POST",
            endpoint=f"whatsapp_conversations/{conversation_id}/whatsapp_messages",
            data=payload,
            timeout=60,  # Timeout mayor para media
        )

        logger.info(f"✅ Media {media_type} enviado (conv: {conversation_id})")
        return result

    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        whatsapp_config_id: str,
        template_params: Optional[Any] = None,
        template_language: str = "es",
        header_params: Optional[str] = None,
        button_url_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Envía un mensaje usando una plantilla de WhatsApp Business

        Args:
            phone_number: Número de teléfono del destinatario
            template_name: Nombre de la plantilla aprobada
            whatsapp_config_id: ID de configuración de WhatsApp
            template_params: Parámetros de la plantilla (lista o dict)
            template_language: Código de idioma (ej: es, en_US)
            header_params: Parámetros del header
            button_url_params: Parámetros de botones con URL

        Returns:
            Respuesta de la API
        """
        payload = {
            "conversation_selector": {
                "phone_number": phone_number,
            },
            "template_name": template_name,
            "template_language": template_language,
            "whatsapp_config_id": whatsapp_config_id,
        }

        if template_params:
            payload["template_params"] = template_params
        if header_params:
            payload["header_params"] = header_params
        if button_url_params:
            payload["button_url_params"] = button_url_params

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp/send_template",
            data=payload,
        )

        logger.info(f"✅ Template '{template_name}' enviado a {phone_number}")
        return result

    async def send_interactive_message(
        self,
        conversation_id: str,
        interactive_type: str,
        body_text: str,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        buttons: Optional[List[Dict]] = None,
        sections: Optional[List[Dict]] = None,
        list_button_text: str = "Ver opciones",
    ) -> Dict[str, Any]:
        """
        Envía un mensaje interactivo (botones o lista)

        Args:
            conversation_id: ID de la conversación
            interactive_type: Tipo (button o list)
            body_text: Texto principal
            header_text: Texto del encabezado
            footer_text: Texto del pie
            buttons: Lista de botones (para type=button)
            sections: Secciones de lista (para type=list)
            list_button_text: Texto del botón de lista

        Returns:
            Respuesta de la API
        """
        payload = {
            "conversation_selector": {
                "conversation_id": conversation_id,
            },
            "interactive_type": interactive_type,
            "body_text": body_text,
        }

        if header_text:
            payload["header_text"] = header_text
        if footer_text:
            payload["footer_text"] = footer_text
        if buttons:
            payload["buttons"] = buttons
        if sections:
            payload["sections"] = sections
        if interactive_type == "list":
            payload["list_button_text"] = list_button_text

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp/send_interactive",
            data=payload,
        )

        logger.info(f"✅ Mensaje interactivo {interactive_type} enviado (conv: {conversation_id})")
        return result

    # ========== Conversaciones ==========

    async def create_conversation(
        self,
        phone_number: str,
        whatsapp_config_id: str,
    ) -> Dict[str, Any]:
        """
        Crea una nueva conversación

        Args:
            phone_number: Número de teléfono del contacto
            whatsapp_config_id: ID de configuración de WhatsApp

        Returns:
            Información de la conversación creada
        """
        payload = {
            "phone_number": phone_number,
            "whatsapp_config_id": whatsapp_config_id,
        }

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp_conversations",
            data=payload,
        )

        logger.info(f"✅ Conversación creada para {phone_number}")
        return result

    async def get_conversation(
        self,
        conversation_id: str,
    ) -> Dict[str, Any]:
        """
        Obtiene información de una conversación

        Args:
            conversation_id: ID de la conversación

        Returns:
            Información de la conversación
        """
        result = await self._make_request(
            method="GET",
            endpoint=f"whatsapp_conversations/{conversation_id}",
        )

        return result

    async def list_conversations(
        self,
        whatsapp_config_id: Optional[str] = None,
        limit: int = 50,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Lista conversaciones

        Args:
            whatsapp_config_id: Filtrar por configuración de WhatsApp
            limit: Límite de resultados
            page: Página

        Returns:
            Lista de conversaciones
        """
        params = {
            "limit": limit,
            "page": page,
        }

        if whatsapp_config_id:
            params["whatsapp_config_id"] = whatsapp_config_id

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp_conversations",
            params=params,
        )

        return result

    async def update_conversation_status(
        self,
        conversation_id: str,
        status: ConversationStatus,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Actualiza el estado de una conversación

        Args:
            conversation_id: ID de la conversación
            status: Nuevo estado (active o ended)
            reason: Razón del cambio

        Returns:
            Conversación actualizada
        """
        payload = {
            "conversation_id": conversation_id,
            "status": status.value if isinstance(status, ConversationStatus) else status,
        }

        if reason:
            payload["reason"] = reason

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp/conversation_set_status",
            data=payload,
        )

        logger.info(f"✅ Conversación {conversation_id} actualizada a {status}")
        return result

    # ========== Contactos ==========

    async def search_contacts(
        self,
        query: str,
        limit: int = 20,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Busca contactos por nombre o teléfono

        Args:
            query: Texto a buscar
            limit: Límite de resultados
            page: Página

        Returns:
            Lista de contactos
        """
        params = {
            "query": query,
            "limit": limit,
            "page": page,
        }

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/search_contacts",
            params=params,
        )

        return result

    async def get_contact_context(
        self,
        identifier: str,
        include_recent_messages: bool = True,
        recent_message_limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Obtiene contexto de un contacto con mensajes recientes

        Args:
            identifier: ID del contacto o número de teléfono
            include_recent_messages: Incluir mensajes recientes
            recent_message_limit: Límite de mensajes

        Returns:
            Contexto del contacto
        """
        params = {
            "identifier": identifier,
            "include_recent_messages": include_recent_messages,
            "recent_message_limit": recent_message_limit,
        }

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/get_contact_context",
            params=params,
        )

        return result

    async def add_contact_note(
        self,
        contact_identifier: str,
        content: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Añade una nota a un contacto

        Args:
            contact_identifier: ID del contacto o número
            content: Contenido de la nota
            name: Nombre/etiqueta de la nota
            metadata: Metadatos adicionales

        Returns:
            Nota creada
        """
        payload = {
            "contact_identifier": contact_identifier,
            "content": content,
        }

        if name:
            payload["name"] = name
        if metadata:
            payload["metadata"] = metadata

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp/contact_add_note",
            data=payload,
        )

        logger.info(f"✅ Nota añadida a contacto {contact_identifier}")
        return result

    # ========== Mensajes ==========

    async def mark_messages_as_read(
        self,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Marca mensajes como leídos

        Args:
            conversation_id: ID de conversación (para marcar todos)
            message_id: ID de mensaje específico
            before: Timestamp ISO para marcar mensajes anteriores

        Returns:
            Resultado de la operación
        """
        payload = {}

        if conversation_id:
            payload["conversation_id"] = conversation_id
        if message_id:
            payload["message_id"] = message_id
        if before:
            payload["before"] = before

        result = await self._make_request(
            method="POST",
            endpoint="whatsapp/mark_inbound_read",
            data=payload,
        )

        return result

    async def search_messages(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Busca mensajes por contenido

        Args:
            query: Texto a buscar
            conversation_id: Filtrar por conversación
            limit: Límite de resultados
            page: Página

        Returns:
            Mensajes que coinciden
        """
        params = {
            "query": query,
            "limit": limit,
            "page": page,
        }

        if conversation_id:
            params["conversation_id"] = conversation_id

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/search_messages",
            params=params,
        )

        return result

    # ========== Templates ==========

    async def list_templates(
        self,
        whatsapp_config_id: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Lista plantillas disponibles

        Args:
            whatsapp_config_id: Filtrar por configuración
            limit: Límite de resultados
            page: Página

        Returns:
            Lista de plantillas
        """
        params = {
            "limit": limit,
            "page": page,
        }

        if whatsapp_config_id:
            params["whatsapp_config_id"] = whatsapp_config_id

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/templates",
            params=params,
        )

        return result

    # ========== Configuración ==========

    async def list_whatsapp_configs(
        self,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Lista configuraciones de WhatsApp

        Args:
            customer_id: Filtrar por cliente

        Returns:
            Lista de configuraciones
        """
        params = {}
        if customer_id:
            params["customer_id"] = customer_id

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/configs_overview",
            params=params,
        )

        return result

    async def get_inbox(
        self,
        whatsapp_config_id: str,
        limit: int = 20,
        page: int = 1,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene la bandeja de entrada de una configuración

        Args:
            whatsapp_config_id: ID de configuración
            limit: Límite de resultados
            page: Página
            status: Filtrar por estado (active/ended)

        Returns:
            Conversaciones del inbox
        """
        params = {
            "whatsapp_config_id": whatsapp_config_id,
            "limit": limit,
            "page": page,
        }

        if status:
            params["status"] = status

        result = await self._make_request(
            method="GET",
            endpoint="whatsapp/inbox",
            params=params,
        )

        return result

    # ========== Webhooks ==========

    @staticmethod
    def validate_webhook_signature(
        payload: str,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Valida la firma de un webhook de Kapso

        Args:
            payload: Payload del webhook como string
            signature: Firma recibida en el header
            secret: Secreto compartido del webhook

        Returns:
            True si la firma es válida
        """
        try:
            expected_signature = hmac.new(
                secret.encode("utf-8"),
                payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Error validando firma de webhook: {e}")
            return False

    # ========== Health Check ==========

    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado del servicio Kapso

        Returns:
            Estado del servicio
        """
        try:
            start_time = httpx.get("https://httpbin.org/get").elapsed.total_seconds()

            result = await self._make_request(
                method="GET",
                endpoint="health",
                timeout=10,
            )

            return {
                "status": "healthy",
                "response_time": start_time,
                "details": result,
            }

        except Exception as e:
            logger.error(f"Health check falló: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

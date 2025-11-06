"""
Procesador de media para mensajes de WhatsApp
Maneja la descarga y almacenamiento de archivos adjuntos desde Kapso
Reutiliza la infraestructura de attachments de ChatKit
"""
import logging
import httpx
import base64
from typing import Dict, Optional, Any
from uuid import uuid4

from app.services.storage.attachment_storage import get_attachment_storage
from app.services.openai_files import get_openai_files_service
from app.agents.core import (
    generate_attachment_id,
    store_attachment_content,
)

logger = logging.getLogger(__name__)


class WhatsAppMediaProcessor:
    """
    Procesa media de webhooks de Kapso usando la infraestructura de ChatKit.

    Flujo:
    1. Extrae info de media del webhook
    2. Descarga el archivo desde Kapso
    3. Sube a Supabase Storage (reutiliza AttachmentStorage)
    4. Para PDFs: sube a OpenAI Files + crea Vector Store
    5. Para imágenes: guarda base64 en memoria
    6. Retorna metadata del attachment
    """

    def __init__(self):
        """Inicializa el procesador con los servicios necesarios"""
        self.storage = get_attachment_storage()
        self.openai_service = get_openai_files_service()

        logger.info("📱 WhatsAppMediaProcessor initialized")

    async def process_inbound_media(
        self,
        message_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Procesa media de un mensaje inbound de Kapso.

        Args:
            message_data: Datos del mensaje del webhook de Kapso
                Estructura esperada:
                {
                    "message_type": "image|video|audio|document",
                    "has_media": true,
                    "media_url": "https://...",  # URL de Kapso para descargar
                    "media_mime_type": "image/jpeg",
                    "media_caption": "...",
                    "media_filename": "photo.jpg",
                }

        Returns:
            Dict con metadata del attachment procesado:
            {
                "attachment_id": "atc_xxx",
                "mime_type": "image/jpeg",
                "filename": "photo.jpg",
                "url": "https://supabase.../atc_xxx.jpg",
                "base64": "..." (solo para imágenes),
                "vector_store_id": "vs_xxx" (solo para PDFs)
            }

            None si falla el procesamiento
        """
        try:
            # 1. Extraer info de media
            media_info = self._extract_media_info(message_data)

            if not media_info:
                logger.warning("⚠️ No se pudo extraer info de media del mensaje")
                return None

            logger.info(f"📎 Procesando media: {media_info['type']} ({media_info['mime_type']})")

            # 2. Descargar media desde Kapso
            content = await self._download_media(media_info["url"])

            if not content:
                logger.error(f"❌ No se pudo descargar media desde {media_info['url']}")
                return None

            logger.info(f"✅ Media descargado: {len(content)} bytes")

            # 3. Generar attachment_id único
            attachment_id = generate_attachment_id("atc")

            # 4. Subir a Supabase Storage (reutiliza AttachmentStorage)
            success, public_url, error = self.storage.upload_attachment(
                attachment_id=attachment_id,
                content=content,
                mime_type=media_info["mime_type"],
                filename=media_info["filename"]
            )

            if not success:
                logger.error(f"❌ Error subiendo a Supabase: {error}")
                return None

            logger.info(f"✅ Media subido a Supabase: {public_url}")

            # 5. Construir metadata base del attachment
            attachment_metadata = {
                "attachment_id": attachment_id,
                "mime_type": media_info["mime_type"],
                "filename": media_info["filename"],
                "url": public_url,
                "size": len(content),
            }

            # 6. Procesamiento específico por tipo

            # Para imágenes: guardar base64 en memoria (para el agente)
            if media_info["mime_type"].startswith("image/"):
                base64_content = base64.b64encode(content).decode('utf-8')

                # Store en memoria global (reutiliza MemoryAttachmentStore)
                store_attachment_content(attachment_id, content)

                attachment_metadata["base64"] = base64_content
                logger.info(f"📸 Imagen almacenada en memoria: {len(base64_content)} chars base64")

            # Para PDFs: subir a OpenAI Files + crear Vector Store
            elif media_info["mime_type"] == "application/pdf":
                openai_result = await self._process_pdf(
                    content=content,
                    filename=media_info["filename"],
                    attachment_id=attachment_id
                )

                if openai_result:
                    attachment_metadata["vector_store_id"] = openai_result["vector_store_id"]
                    attachment_metadata["openai_file_id"] = openai_result["file_id"]
                    logger.info(f"📄 PDF procesado: vector_store={openai_result['vector_store_id']}")

            # Para otros tipos: solo URL
            else:
                logger.info(f"📦 Archivo almacenado: {media_info['type']}")

            return attachment_metadata

        except Exception as e:
            logger.error(f"❌ Error procesando media: {e}", exc_info=True)
            return None

    def _extract_media_info(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extrae información de media del webhook de Kapso.

        Args:
            message_data: Datos del mensaje del webhook

        Returns:
            Dict con: {type, url, mime_type, filename, caption}
            None si no hay media o falta información
        """
        try:
            # Kapso V2 usa: message.type = "image"|"document"|"video"|"audio"
            # y luego message.image = {id, link, mime_type, sha256}
            message_type = message_data.get("type", "text")

            # Si type = "text", no hay media
            if message_type == "text":
                return None

            # Intentar extraer media según el tipo
            media_url = None
            mime_type = None
            filename = None
            caption = None

            # V2 format: message.image, message.document, etc.
            if message_type == "image" and "image" in message_data:
                media_info = message_data["image"]
                media_url = media_info.get("link")
                mime_type = media_info.get("mime_type") or "image/jpeg"
                caption = media_info.get("caption")
                filename = f"image_{media_info.get('id', 'unknown')}.jpg"

            elif message_type == "document" and "document" in message_data:
                media_info = message_data["document"]
                media_url = media_info.get("link")
                mime_type = media_info.get("mime_type") or "application/pdf"
                filename = media_info.get("filename", f"document_{media_info.get('id', 'unknown')}.pdf")
                caption = media_info.get("caption")

            elif message_type == "video" and "video" in message_data:
                media_info = message_data["video"]
                media_url = media_info.get("link")
                mime_type = media_info.get("mime_type") or "video/mp4"
                caption = media_info.get("caption")
                filename = f"video_{media_info.get('id', 'unknown')}.mp4"

            elif message_type == "audio" and "audio" in message_data:
                media_info = message_data["audio"]
                media_url = media_info.get("link")
                mime_type = media_info.get("mime_type") or "audio/ogg"
                filename = f"audio_{media_info.get('id', 'unknown')}.ogg"

            # Fallback: try old V1 format
            if not media_url:
                has_media = message_data.get("has_media", False)
                if not has_media:
                    return None

                # Kapso puede enviar la URL en diferentes campos según la versión
                # Intentamos varios campos posibles
                media_url = (
                    message_data.get("media_url") or
                    message_data.get("media", {}).get("url") or
                    message_data.get("content_url")
                )

            # Si no encontramos URL directa, intentar extraer del campo content
            # Kapso a veces envía: "Document attached (...) URL: https://..."
            if not media_url:
                content = message_data.get("content", "")
                if "URL:" in content:
                    # Extraer URL después de "URL: "
                    import re
                    url_match = re.search(r'URL:\s*(https?://[^\s]+)', content)
                    if url_match:
                        media_url = url_match.group(1)
                        logger.info(f"📎 URL extraída del campo content: {media_url[:100]}...")

            if not media_url:
                logger.warning("⚠️ No se encontró URL de media")
                logger.debug(f"  message_data keys: {list(message_data.keys())}")
                logger.debug(f"  type: {message_type}")
                return None

            # Solo intentar extraer V1 fields si no tenemos mime_type/filename del V2
            if not mime_type:
                # Extraer mime_type (desde content si está disponible)
                mime_type = (
                    message_data.get("media_mime_type") or
                    message_data.get("media", {}).get("mime_type") or
                    message_data.get("mime_type")
                )

                # Si no hay mime_type, intentar extraer del content
                # Formato: "Document attached (...) [Size: ... | Type: application/pdf]"
                if not mime_type:
                    content = message_data.get("content", "")
                    if "Type:" in content:
                        import re
                        type_match = re.search(r'Type:\s*([^\]]+)', content)
                        if type_match:
                            mime_type = type_match.group(1).strip()
                            logger.info(f"📎 MIME type extraído del content: {mime_type}")

                # Fallback: adivinar por message_type
                if not mime_type:
                    mime_type = self._guess_mime_type(message_type)

            if not filename:
                # Extraer filename (desde content si está disponible)
                filename = (
                    message_data.get("media_filename") or
                    message_data.get("media", {}).get("filename") or
                    message_data.get("filename")
                )

                # Si no hay filename, intentar extraer del content
                # Formato: "Document attached (_FAE077919 (1).pdf)"
                if not filename:
                    content = message_data.get("content", "")
                    if "attached (" in content or "attached (_" in content:
                        import re
                        # Buscar texto entre paréntesis después de "attached"
                        filename_match = re.search(r'attached \(_?([^)]+)\)', content)
                        if filename_match:
                            filename = filename_match.group(1).strip()
                            logger.info(f"📎 Filename extraído del content: {filename}")

                # Fallback: generar filename
                if not filename:
                    filename = f"{message_type}_{uuid4().hex[:8]}{self._get_extension(mime_type)}"

            if not caption:
                # Extraer caption (opcional)
                caption = (
                    message_data.get("media_caption") or
                    message_data.get("caption") or
                    message_data.get("media", {}).get("caption")
                )

            return {
                "type": message_type,
                "url": media_url,
                "mime_type": mime_type,
                "filename": filename,
                "caption": caption,
            }

        except Exception as e:
            logger.error(f"❌ Error extrayendo info de media: {e}", exc_info=True)
            return None

    async def _download_media(self, url: str, timeout: int = 30) -> Optional[bytes]:
        """
        Descarga media desde una URL de Kapso.

        Args:
            url: URL del archivo a descargar
            timeout: Timeout en segundos

        Returns:
            Contenido del archivo en bytes, o None si falla
        """
        try:
            logger.info(f"📥 Descargando media desde: {url[:100]}...")

            # httpx sigue redirects automáticamente por defecto (follow_redirects=True)
            # Configuramos para seguir hasta 10 redirects
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                content = response.content
                logger.info(f"✅ Media descargado: {len(content)} bytes (después de {len(response.history)} redirect(s))")

                return content

        except httpx.TimeoutException:
            logger.error(f"⏱️ Timeout descargando media desde {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error descargando media: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"❌ Error descargando media: {e}", exc_info=True)
            return None

    async def _process_pdf(
        self,
        content: bytes,
        filename: str,
        attachment_id: str
    ) -> Optional[Dict[str, str]]:
        """
        Procesa un PDF: sube a OpenAI Files y crea Vector Store.

        Args:
            content: Contenido del PDF
            filename: Nombre del archivo
            attachment_id: ID del attachment (para tracking)

        Returns:
            Dict con file_id y vector_store_id, o None si falla
        """
        try:
            logger.info(f"📄 Procesando PDF para OpenAI: {filename}")

            # 1. Subir a OpenAI Files API
            success, file_id, error = self.openai_service.upload_file_for_file_search(
                file_content=content,
                filename=filename,
                mime_type="application/pdf"
            )

            if not success or not file_id:
                logger.error(f"❌ Error subiendo PDF a OpenAI: {error}")
                return None

            logger.info(f"✅ PDF subido a OpenAI: {file_id}")

            # 2. Crear Vector Store
            success_vs, vector_store_id, error_vs = self.openai_service.create_vector_store_with_file(
                file_id=file_id,
                store_name=filename
            )

            if not success_vs or not vector_store_id:
                logger.error(f"❌ Error creando Vector Store: {error_vs}")
                # No retornar None - el PDF está en OpenAI aunque no tenga VS
                return {"file_id": file_id, "vector_store_id": None}

            logger.info(f"✅ Vector Store creado: {vector_store_id}")

            # 3. Guardar metadata en MemoryAttachmentStore para persistencia
            # Esto permite que el attachment_store.get_openai_metadata() funcione
            from app.agents.core import MemoryAttachmentStore

            # TODO: Considerar hacer esto más elegante con singleton o inyección
            # Por ahora usamos una instancia temporal para set_openai_metadata
            temp_store = MemoryAttachmentStore()
            temp_store.set_openai_metadata(
                attachment_id=attachment_id,
                file_id=file_id,
                vector_store_id=vector_store_id
            )

            return {
                "file_id": file_id,
                "vector_store_id": vector_store_id
            }

        except Exception as e:
            logger.error(f"❌ Error procesando PDF: {e}", exc_info=True)
            return None

    def _guess_mime_type(self, message_type: str) -> str:
        """
        Adivina el MIME type basado en el message_type.

        Args:
            message_type: Tipo de mensaje (image, video, audio, document)

        Returns:
            MIME type estimado
        """
        mime_map = {
            "image": "image/jpeg",
            "video": "video/mp4",
            "audio": "audio/ogg",
            "document": "application/pdf",
        }

        return mime_map.get(message_type, "application/octet-stream")

    def _get_extension(self, mime_type: str) -> str:
        """
        Obtiene la extensión de archivo basada en el MIME type.

        Args:
            mime_type: MIME type del archivo

        Returns:
            Extensión con punto (ej: ".jpg", ".pdf")
        """
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/mpeg": ".mpeg",
            "audio/ogg": ".ogg",
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
            "application/pdf": ".pdf",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        }

        return ext_map.get(mime_type, ".bin")


# Singleton instance
_media_processor: Optional[WhatsAppMediaProcessor] = None


def get_media_processor() -> WhatsAppMediaProcessor:
    """
    Obtiene la instancia singleton del procesador de media.

    Returns:
        Instancia de WhatsAppMediaProcessor
    """
    global _media_processor

    if _media_processor is None:
        _media_processor = WhatsAppMediaProcessor()

    return _media_processor

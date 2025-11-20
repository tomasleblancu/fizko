"""
Servicio para almacenar attachments de ChatKit en Supabase Storage
"""
import logging
import os
import mimetypes
from typing import Optional, Tuple
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class AttachmentStorage:
    """
    Servicio para gestionar almacenamiento de attachments en Supabase Storage

    Estructura de carpetas:
    chatkit-attachments/
        {attachment_id}.{extension}

    Ejemplo:
        chatkit-attachments/atc_1c31e6175c8c.png
    """

    BUCKET_NAME = "chatkit-attachments"

    def __init__(self):
        """Inicializa el cliente de Supabase"""
        supabase_url = os.getenv("SUPABASE_URL")
        # Usar SERVICE_ROLE_KEY para operaciones del backend (bypassa RLS)
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) must be set")

        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info(f"📦 AttachmentStorage initialized for bucket: {self.BUCKET_NAME}")

    def _get_file_extension(self, mime_type: str, filename: str | None = None) -> str:
        """
        Obtiene la extensión del archivo basada en el MIME type o filename

        Args:
            mime_type: MIME type del archivo
            filename: Nombre del archivo (opcional)

        Returns:
            Extensión del archivo (ej: '.png', '.pdf')
        """
        # Intentar obtener extensión del filename primero
        if filename:
            _, ext = os.path.splitext(filename)
            if ext:
                return ext

        # Fallback: usar mimetypes para obtener extensión
        ext = mimetypes.guess_extension(mime_type)
        if ext:
            return ext

        # Default por tipo
        type_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "application/pdf": ".pdf",
            "text/plain": ".txt",
        }

        return type_map.get(mime_type, ".bin")

    def upload_attachment(
        self,
        attachment_id: str,
        content: bytes,
        mime_type: str,
        filename: str | None = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Sube un attachment al bucket de Supabase Storage

        Args:
            attachment_id: ID único del attachment (ej: 'atc_1c31e6175c8c')
            content: Contenido del archivo en bytes
            mime_type: MIME type del archivo
            filename: Nombre original del archivo (opcional)

        Returns:
            Tupla (success, url, error_message)
            - success: True si se subió correctamente
            - url: URL pública del archivo (si success=True)
            - error_message: Mensaje de error (si success=False)
        """
        try:
            # Generar path del archivo
            extension = self._get_file_extension(mime_type, filename)
            file_path = f"{attachment_id}{extension}"

            logger.info(f"📤 Uploading attachment to: {self.BUCKET_NAME}/{file_path}")

            # Subir archivo
            response = self.client.storage.from_(self.BUCKET_NAME).upload(
                path=file_path,
                file=content,
                file_options={
                    "content-type": mime_type,
                    "upsert": "true"  # Sobrescribir si ya existe
                }
            )

            # Generar URL pública (el bucket es público, no necesitamos firma)
            public_url = self.client.storage.from_(self.BUCKET_NAME).get_public_url(file_path)

            logger.info(f"✅ Attachment uploaded successfully: {public_url}")
            return True, public_url, None

        except Exception as e:
            error_msg = f"Failed to upload attachment: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, None, error_msg

    def get_attachment_url(
        self,
        attachment_id: str,
        extension: str = "",
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Obtiene una URL firmada para descargar el attachment

        Args:
            attachment_id: ID único del attachment
            extension: Extensión del archivo (ej: '.png')
            expires_in: Tiempo de expiración en segundos (default: 1 hora)

        Returns:
            URL firmada del attachment, o None si no existe
        """
        try:
            file_path = f"{attachment_id}{extension}"

            response = self.client.storage.from_(self.BUCKET_NAME).create_signed_url(
                path=file_path,
                expires_in=expires_in
            )

            logger.info(f"🔍 Supabase signed URL response: {response}")

            # Try different possible keys
            signed_url = response.get('signedURL') or response.get('signedUrl') or response.get('signed_url')

            if not signed_url:
                logger.error(f"❌ No signed URL found in response: {response}")
                return None

            logger.info(f"✅ Got signed URL: {signed_url[:100]}...")
            return signed_url

        except Exception as e:
            logger.error(f"❌ Failed to get attachment URL: {e}", exc_info=True)
            return None

    def delete_attachment(
        self,
        attachment_id: str,
        extension: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """
        Elimina un attachment del bucket

        Args:
            attachment_id: ID único del attachment
            extension: Extensión del archivo

        Returns:
            Tupla (success, error_message)
        """
        try:
            file_path = f"{attachment_id}{extension}"

            self.client.storage.from_(self.BUCKET_NAME).remove([file_path])

            logger.info(f"🗑️  Attachment deleted: {file_path}")
            return True, None

        except Exception as e:
            error_msg = f"Failed to delete attachment: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg


# Singleton instance
_attachment_storage_instance: Optional[AttachmentStorage] = None


def get_attachment_storage() -> AttachmentStorage:
    """
    Obtiene la instancia singleton del servicio de almacenamiento

    Returns:
        Instancia de AttachmentStorage
    """
    global _attachment_storage_instance

    if _attachment_storage_instance is None:
        _attachment_storage_instance = AttachmentStorage()

    return _attachment_storage_instance

"""
Servicio para almacenar screenshots y HTML de debugging en Supabase Storage
"""
import logging
import os
from typing import Optional, Tuple
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class DebugStorage:
    """
    Servicio para gestionar almacenamiento de screenshots y HTML de debugging en Supabase Storage

    Estructura de carpetas:
    debug-screenshots/
        f29/
            {context}/
                {folio}_{timestamp}.png
                {folio}_{timestamp}.html

    Ejemplo:
        debug-screenshots/f29/click_intercepted/8104678626_1738000000.png
        debug-screenshots/f29/click_intercepted/8104678626_1738000000.html
    """

    BUCKET_NAME = "debug-screenshots"

    def __init__(self):
        """Inicializa el cliente de Supabase"""
        supabase_url = os.getenv("SUPABASE_URL")
        # Usar SERVICE_ROLE_KEY para operaciones del backend (bypassa RLS)
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) must be set")

        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info(f"📦 DebugStorage initialized for bucket: {self.BUCKET_NAME}")

    def _get_file_path(
        self,
        process: str,
        context: str,
        folio: str,
        timestamp: int,
        extension: str
    ) -> str:
        """
        Genera el path del archivo en el bucket

        Args:
            process: Proceso (ej: 'f29', 'compras', 'ventas')
            context: Contexto del error (ej: 'click_intercepted', 'invalid_session')
            folio: Folio del formulario o identificador
            timestamp: Timestamp unix
            extension: Extensión del archivo ('png' o 'html')

        Returns:
            Path completo del archivo

        Example:
            >>> storage._get_file_path('f29', 'click_intercepted', '8104678626', 1738000000, 'png')
            'f29/click_intercepted/8104678626_1738000000.png'
        """
        return f"{process}/{context}/{folio}_{timestamp}.{extension}"

    def upload_screenshot(
        self,
        process: str,
        context: str,
        folio: str,
        timestamp: int,
        screenshot_bytes: bytes
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Sube un screenshot al bucket de Supabase Storage

        Args:
            process: Proceso (ej: 'f29')
            context: Contexto del error
            folio: Folio del formulario
            timestamp: Timestamp unix
            screenshot_bytes: Contenido del screenshot en bytes (PNG)

        Returns:
            Tupla (success, url, error_message)
        """
        try:
            file_path = self._get_file_path(process, context, folio, timestamp, "png")

            logger.debug(f"📤 Uploading screenshot to: {self.BUCKET_NAME}/{file_path}")

            # Subir archivo
            self.client.storage.from_(self.BUCKET_NAME).upload(
                path=file_path,
                file=screenshot_bytes,
                file_options={
                    "content-type": "image/png",
                    "upsert": "true"
                }
            )

            # Generar URL firmada (7 días)
            url_response = self.client.storage.from_(self.BUCKET_NAME).create_signed_url(
                path=file_path,
                expires_in=604800  # 7 días en segundos
            )

            public_url = url_response.get('signedURL')

            logger.info(f"✅ Screenshot uploaded: {public_url}")
            return True, public_url, None

        except Exception as e:
            error_msg = f"Failed to upload screenshot: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, None, error_msg

    def upload_html(
        self,
        process: str,
        context: str,
        folio: str,
        timestamp: int,
        html_content: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Sube HTML source al bucket de Supabase Storage

        Args:
            process: Proceso (ej: 'f29')
            context: Contexto del error
            folio: Folio del formulario
            timestamp: Timestamp unix
            html_content: Contenido HTML como string

        Returns:
            Tupla (success, url, error_message)
        """
        try:
            file_path = self._get_file_path(process, context, folio, timestamp, "html")

            logger.debug(f"📤 Uploading HTML to: {self.BUCKET_NAME}/{file_path}")

            # Convertir string a bytes
            html_bytes = html_content.encode('utf-8')

            # Subir archivo
            self.client.storage.from_(self.BUCKET_NAME).upload(
                path=file_path,
                file=html_bytes,
                file_options={
                    "content-type": "text/html",
                    "upsert": "true"
                }
            )

            # Generar URL firmada (7 días)
            url_response = self.client.storage.from_(self.BUCKET_NAME).create_signed_url(
                path=file_path,
                expires_in=604800
            )

            public_url = url_response.get('signedURL')

            logger.info(f"✅ HTML uploaded: {public_url}")
            return True, public_url, None

        except Exception as e:
            error_msg = f"Failed to upload HTML: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, None, error_msg


# Singleton instance
_debug_storage_instance: Optional[DebugStorage] = None


def get_debug_storage() -> DebugStorage:
    """
    Obtiene la instancia singleton del servicio de almacenamiento de debug

    Returns:
        Instancia de DebugStorage
    """
    global _debug_storage_instance

    if _debug_storage_instance is None:
        _debug_storage_instance = DebugStorage()

    return _debug_storage_instance

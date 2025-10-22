"""
Servicio para almacenar PDFs de F29 en Supabase Storage
"""
import logging
import os
from typing import Optional, Tuple
from uuid import UUID
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class F29PDFStorage:
    """
    Servicio para gestionar almacenamiento de PDFs de F29 en Supabase Storage

    Estructura de carpetas:
    f29-pdfs/
        {company_id}/
            {year}/
                f29_{period}_{folio}.pdf

    Ejemplo:
        f29-pdfs/550e8400-e29b-41d4-a716-446655440000/2024/f29_2024-01_7904207766.pdf
    """

    BUCKET_NAME = "f29-pdfs"

    def __init__(self):
        """Inicializa el cliente de Supabase"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")  # Service role key para backend

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info(f"📦 F29PDFStorage initialized for bucket: {self.BUCKET_NAME}")

    def _get_file_path(
        self,
        company_id: UUID,
        year: int,
        period: str,
        folio: str
    ) -> str:
        """
        Genera el path del archivo en el bucket

        Args:
            company_id: UUID de la compañía
            year: Año del período
            period: Período en formato YYYY-MM
            folio: Folio del formulario

        Returns:
            Path completo del archivo

        Example:
            >>> storage._get_file_path(
            ...     UUID('550e8400-e29b-41d4-a716-446655440000'),
            ...     2024,
            ...     '2024-01',
            ...     '7904207766'
            ... )
            '550e8400-e29b-41d4-a716-446655440000/2024/f29_2024-01_7904207766.pdf'
        """
        return f"{company_id}/{year}/f29_{period}_{folio}.pdf"

    def upload_pdf(
        self,
        company_id: UUID,
        year: int,
        period: str,
        folio: str,
        pdf_bytes: bytes
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Sube un PDF al bucket de Supabase Storage

        Args:
            company_id: UUID de la compañía
            year: Año del período
            period: Período en formato YYYY-MM
            folio: Folio del formulario
            pdf_bytes: Contenido del PDF en bytes

        Returns:
            Tupla (success, url, error_message)
            - success: True si se subió correctamente
            - url: URL pública del archivo (si success=True)
            - error_message: Mensaje de error (si success=False)

        Example:
            >>> success, url, error = storage.upload_pdf(
            ...     company_id=UUID('...'),
            ...     year=2024,
            ...     period='2024-01',
            ...     folio='7904207766',
            ...     pdf_bytes=pdf_content
            ... )
            >>> if success:
            ...     print(f"PDF uploaded: {url}")
        """
        try:
            # Generar path del archivo
            file_path = self._get_file_path(company_id, year, period, folio)

            logger.info(f"📤 Uploading PDF to: {self.BUCKET_NAME}/{file_path}")

            # Subir archivo
            response = self.client.storage.from_(self.BUCKET_NAME).upload(
                path=file_path,
                file=pdf_bytes,
                file_options={
                    "content-type": "application/pdf",
                    "upsert": "true"  # Sobrescribir si ya existe
                }
            )

            # Generar URL pública (firmada por 1 año)
            url_response = self.client.storage.from_(self.BUCKET_NAME).create_signed_url(
                path=file_path,
                expires_in=31536000  # 1 año en segundos
            )

            public_url = url_response.get('signedURL')

            logger.info(f"✅ PDF uploaded successfully: {public_url}")
            return True, public_url, None

        except Exception as e:
            error_msg = f"Failed to upload PDF: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, None, error_msg

    def get_pdf_url(
        self,
        company_id: UUID,
        year: int,
        period: str,
        folio: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Obtiene una URL firmada para descargar el PDF

        Args:
            company_id: UUID de la compañía
            year: Año del período
            period: Período en formato YYYY-MM
            folio: Folio del formulario
            expires_in: Tiempo de expiración en segundos (default: 1 hora)

        Returns:
            URL firmada del PDF, o None si no existe
        """
        try:
            file_path = self._get_file_path(company_id, year, period, folio)

            response = self.client.storage.from_(self.BUCKET_NAME).create_signed_url(
                path=file_path,
                expires_in=expires_in
            )

            return response.get('signedURL')

        except Exception as e:
            logger.error(f"❌ Failed to get PDF URL: {e}")
            return None

    def delete_pdf(
        self,
        company_id: UUID,
        year: int,
        period: str,
        folio: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Elimina un PDF del bucket

        Args:
            company_id: UUID de la compañía
            year: Año del período
            period: Período en formato YYYY-MM
            folio: Folio del formulario

        Returns:
            Tupla (success, error_message)
        """
        try:
            file_path = self._get_file_path(company_id, year, period, folio)

            self.client.storage.from_(self.BUCKET_NAME).remove([file_path])

            logger.info(f"🗑️  PDF deleted: {file_path}")
            return True, None

        except Exception as e:
            error_msg = f"Failed to delete PDF: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    def list_pdfs_for_company(
        self,
        company_id: UUID,
        year: Optional[int] = None
    ) -> list:
        """
        Lista todos los PDFs de una compañía

        Args:
            company_id: UUID de la compañía
            year: Año opcional para filtrar

        Returns:
            Lista de archivos
        """
        try:
            path = f"{company_id}/{year}" if year else f"{company_id}"

            response = self.client.storage.from_(self.BUCKET_NAME).list(path)

            return response

        except Exception as e:
            logger.error(f"❌ Failed to list PDFs: {e}")
            return []


# Singleton instance
_pdf_storage_instance: Optional[F29PDFStorage] = None


def get_pdf_storage() -> F29PDFStorage:
    """
    Obtiene la instancia singleton del servicio de almacenamiento

    Returns:
        Instancia de F29PDFStorage
    """
    global _pdf_storage_instance

    if _pdf_storage_instance is None:
        _pdf_storage_instance = F29PDFStorage()

    return _pdf_storage_instance

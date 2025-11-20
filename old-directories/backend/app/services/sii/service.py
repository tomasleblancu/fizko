"""
SIIService - Facade que unifica todos los servicios SII
Mantiene compatibilidad con código existente delegando a servicios especializados
"""
import logging
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .base_service import BaseSIIService
from .form_service import FormService
from .document_service import DocumentService

logger = logging.getLogger(__name__)


class SIIService(BaseSIIService):
    """
    Servicio facade que unifica todos los servicios SII.

    Este servicio mantiene compatibilidad con el código existente
    mientras delega la funcionalidad a servicios especializados:

    - FormService: Manejo de formularios (F29, F22, etc.)
    - DocumentService: Manejo de documentos tributarios (DTEs, compras, ventas)

    IMPORTANTE: Este servicio usa operaciones SÍNCRONAS de DB cuando trabaja con Selenium
    para evitar conflictos entre async/sync contexts.
    """

    def __init__(self, db: Union[AsyncSession, Session]):
        """
        Inicializa el servicio facade

        Args:
            db: Sesión de base de datos (async o sync)
        """
        super().__init__(db)

        # Inicializar servicios especializados
        self._form_service = FormService(db)
        self._document_service = DocumentService(db)

    # =============================================================================
    # DOCUMENT SERVICE - Delegación
    # =============================================================================

    async def extract_contribuyente(
        self,
        session_id: Union[str, UUID],
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """Extrae información del contribuyente - Delega a DocumentService"""
        return await self._document_service.extract_contribuyente(
            session_id=session_id,
            force_new_login=force_new_login
        )

    async def extract_compras(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        tipo_doc: str = "33",
        estado_contab: str = "REGISTRO",
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """Extrae DTEs de compra - Delega a DocumentService"""
        return await self._document_service.extract_compras(
            session_id=session_id,
            periodo=periodo,
            tipo_doc=tipo_doc,
            estado_contab=estado_contab,
            force_new_login=force_new_login
        )

    async def extract_ventas(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        tipo_doc: str = "33",
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """Extrae DTEs de venta - Delega a DocumentService"""
        return await self._document_service.extract_ventas(
            session_id=session_id,
            periodo=periodo,
            tipo_doc=tipo_doc,
            force_new_login=force_new_login
        )

    async def extract_resumen(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """Extrae resumen de compras y ventas - Delega a DocumentService"""
        return await self._document_service.extract_resumen(
            session_id=session_id,
            periodo=periodo,
            force_new_login=force_new_login
        )

    async def extract_boletas_diarias(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        tipo_doc: str,
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """Extrae boletas o comprobantes diarios - Delega a DocumentService"""
        return await self._document_service.extract_boletas_diarias(
            session_id=session_id,
            periodo=periodo,
            tipo_doc=tipo_doc,
            force_new_login=force_new_login
        )

    # =============================================================================
    # FORM SERVICE - Delegación
    # =============================================================================

    async def extract_boletas_honorarios(
        self,
        session_id: Union[str, UUID],
        mes: str,
        anio: str
    ) -> Dict[str, Any]:
        """
        Extrae boletas de honorarios - Delega a DocumentService

        Args:
            session_id: ID de sesión con credenciales SII
            mes: Mes (1-12)
            anio: Año (YYYY)

        Returns:
            Dict con boletas y totales
        """
        return await self._document_service.extract_boletas_honorarios(
            session_id=session_id,
            mes=mes,
            anio=anio
        )

    async def extract_f29_lista(
        self,
        session_id: Union[str, UUID],
        anio: str,
        company_id: Optional[Union[str, UUID]] = None
    ) -> List[Dict[str, Any]]:
        """Extrae lista de formularios F29 - Delega a FormService"""
        return await self._form_service.extract_f29_lista(
            session_id=session_id,
            anio=anio,
            company_id=company_id
        )

    async def save_f29_downloads(
        self,
        company_id: Union[str, UUID],
        formularios: List[Dict[str, Any]]
    ) -> List:
        """Guarda registros de F29 - Delega a FormService"""
        return await self._form_service.save_f29_downloads(
            company_id=company_id,
            formularios=formularios
        )

    async def get_pending_f29_downloads(
        self,
        company_id: Union[str, UUID],
        limit: int = 10
    ) -> List:
        """Obtiene F29 pendientes de descarga - Delega a FormService"""
        return await self._form_service.get_pending_f29_downloads(
            company_id=company_id,
            limit=limit
        )

    async def download_and_save_f29_pdf(
        self,
        download_id: Union[str, UUID],
        session_id: Union[str, UUID],
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """Descarga PDF de F29 - Delega a FormService"""
        return await self._form_service.download_and_save_f29_pdf(
            download_id=download_id,
            session_id=session_id,
            max_retries=max_retries
        )

    async def list_f29_forms(
        self,
        company_id: Union[str, UUID],
        form_type: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
        pdf_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Lista formularios F29 con filtros - Delega a FormService"""
        return await self._form_service.list_f29_forms(
            company_id=company_id,
            form_type=form_type,
            year=year,
            status=status,
            pdf_status=pdf_status
        )

    async def download_f29_pdfs_for_session(
        self,
        session_id: Union[str, UUID],
        company_id: Optional[Union[str, UUID]] = None,
        max_per_company: int = 10
    ) -> Dict[str, Any]:
        """
        Descarga PDFs de F29 para una sesión - Delega a FormService

        Este método encapsula toda la lógica de negocio para descarga masiva de PDFs.
        """
        return await self._form_service.download_f29_pdfs_for_session(
            session_id=session_id,
            company_id=company_id,
            max_per_company=max_per_company
        )

    async def get_propuesta_f29(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene la propuesta de declaración F29 pre-calculada por el SII.

        Args:
            session_id: ID de la sesión SII activa
            periodo: Período tributario en formato YYYYMM (ej: "202510")
            force_new_login: Si True, fuerza nuevo login incluso con sesión válida

        Returns:
            Dict con la propuesta completa del F29 incluyendo códigos pre-calculados

        Raises:
            Exception: Si falla la obtención de la propuesta

        Example:
            >>> propuesta = await sii_service.get_propuesta_f29(
            ...     session_id=session_id,
            ...     periodo="202510"
            ... )
            >>> codigos = propuesta['data']['listCodPropuestos']
        """
        return await self._form_service.get_propuesta_f29(
            session_id=session_id,
            periodo=periodo,
            force_new_login=force_new_login
        )

    async def get_tasa_ppmo(
        self,
        session_id: Union[str, UUID],
        periodo: str,
        categoria_tributaria: int = 1,
        tipo_formulario: str = "FMNINT",
        force_new_login: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene la tasa de PPMO (Pagos Provisionales Mensuales Obligatorios).

        Args:
            session_id: ID de la sesión SII activa
            periodo: Período tributario en formato YYYYMM (ej: "202510")
            categoria_tributaria: Categoría tributaria (default: 1)
            tipo_formulario: Tipo de formulario (default: "FMNINT")
            force_new_login: Si True, fuerza nuevo login

        Returns:
            Dict con información de tasa PPMO

        Example:
            >>> tasa_info = await sii_service.get_tasa_ppmo(
            ...     session_id=session_id,
            ...     periodo="202510"
            ... )
            >>> tasa = tasa_info['data']['cod115']  # Tasa PPM
            >>> ingresos = tasa_info['data']['cod563']  # Ingresos brutos
        """
        return await self._form_service.get_tasa_ppmo(
            session_id=session_id,
            periodo=periodo,
            categoria_tributaria=categoria_tributaria,
            tipo_formulario=tipo_formulario,
            force_new_login=force_new_login
        )


# Funciones helper para usar en routers
async def get_sii_service(db: AsyncSession) -> SIIService:
    """Dependency injection para FastAPI"""
    return SIIService(db)


# Funciones helper para acceso directo a servicios especializados
async def get_form_service(db: AsyncSession) -> FormService:
    """Dependency injection para FormService"""
    return FormService(db)


async def get_document_service(db: AsyncSession) -> DocumentService:
    """Dependency injection para DocumentService"""
    return DocumentService(db)

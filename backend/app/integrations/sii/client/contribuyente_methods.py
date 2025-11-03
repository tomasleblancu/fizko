"""
Métodos relacionados con información del contribuyente
"""
import logging
from typing import Dict, Any

from .base import SIIClientBase
from ..extractors import ContribuyenteExtractor

logger = logging.getLogger(__name__)


class ContribuyenteMethods(SIIClientBase):
    """
    Métodos para obtener información del contribuyente
    """

    def get_contribuyente(self) -> Dict[str, Any]:
        """
        Obtiene información completa del contribuyente

        Estrategia:
        1. Si el cliente se inicializó con cookies, las usa directamente (sin RPA)
        2. Si no hay cookies o fallan, hace login con RPA
        3. Extrae datos via API usando las cookies

        Returns:
            Dict con:
            - rut: str
            - razon_social: str
            - nombre: str
            - direccion: str
            - comuna: str
            - email: str
            - telefono: str
            - actividad_economica: str
            - fecha_inicio_actividades: str

        Raises:
            ExtractionError: Si falla la extracción
        """
        self._ensure_initialized()

        # Lazy loading del extractor
        if not self._contribuyente_extractor:
            self._contribuyente_extractor = ContribuyenteExtractor(self._driver)

        # PASO 1: Intentar con cookies en memoria (sin RPA)
        if self._current_cookies:
            logger.debug("🍪 Using provided cookies for contribuyente extraction (no RPA needed)")
            try:
                # Intentar extraer con cookies provistas
                return self._contribuyente_extractor.extract(
                    tax_id=self.tax_id,
                    cookies=self._current_cookies
                )
            except Exception as e:
                logger.warning(f"⚠️ Provided cookies failed: {e}. Will retry with fresh login.")
                # Si falla, continuar con login

        # PASO 2: Si no hay cookies válidas o fallaron, hacer login con RPA
        logger.debug("🔐 No valid cookies - performing RPA login")
        if not self._authenticated:
            self.login()

        # Extraer con cookies frescas del driver
        return self._contribuyente_extractor.extract(self.tax_id)

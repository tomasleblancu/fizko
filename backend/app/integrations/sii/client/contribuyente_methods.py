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

        # Verificar y refrescar sesión si es necesario
        # Nota: get_contribuyente() es el método usado internamente por verify_session(),
        # así que solo validamos si hay cookies para evitar recursión infinita
        if self._current_cookies:
            # Ya tenemos cookies, validar que sean válidas
            cookie_names = [c.get('name') for c in self._current_cookies]
            # logger.info(f"🍪 Using {len(self._current_cookies)} provided cookies: {cookie_names}")
            try:
                # Intentar extraer con cookies provistas
                return self._contribuyente_extractor.extract(
                    tax_id=self.tax_id,
                    cookies=self._current_cookies
                )
            except Exception as e:
                logger.warning(f"⚠️ Provided cookies failed: {e}. Will retry with fresh login.")
                # Si falla, continuar con login

        # Si no hay cookies válidas o fallaron, hacer login con RPA
        logger.info("🔐 No valid cookies - performing RPA login")
        if not self._authenticated:
            self.login()

        # Obtener cookies del driver después del login
        driver_cookies = self._driver.get_cookies() if self._driver else []
        cookie_names = [c.get('name') for c in driver_cookies]
        logger.info(f"🔄 Extracting with {len(driver_cookies)} cookies from driver: {cookie_names}")

        # Extraer con cookies frescas del driver
        return self._contribuyente_extractor.extract(self.tax_id)

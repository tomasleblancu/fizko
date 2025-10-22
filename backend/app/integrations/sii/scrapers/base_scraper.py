"""
Clase base abstracta para scrapers especializados
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from selenium.webdriver.common.by import By

from ..core.selenium_driver import SeleniumDriver
from ..exceptions import ScrapingException, ElementNotFoundException

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Clase base abstracta para scrapers especializados

    Define la interfaz común que todos los scrapers deben implementar
    """

    def __init__(self, driver: SeleniumDriver):
        """
        Inicializa el scraper

        Args:
            driver: Instancia del SeleniumDriver
        """
        self.driver = driver
        logger.info(f"📋 {self.__class__.__name__} initialized")

    @abstractmethod
    def scrape(self, **kwargs) -> Dict[str, Any]:
        """
        Método principal de scraping

        Debe retornar dict con al menos:
        - 'status': 'success' o 'error'
        - 'data': datos extraídos

        Args:
            **kwargs: Parámetros específicos del scraper

        Returns:
            Dict con resultado del scraping
        """
        pass

    def validate_page_loaded(
        self,
        selector: str,
        by: str = By.CSS_SELECTOR,
        timeout: int = 10
    ) -> bool:
        """
        Valida que la página haya cargado verificando un selector

        Args:
            selector: Selector del elemento a verificar
            by: Tipo de selector (default: CSS_SELECTOR)
            timeout: Tiempo máximo de espera

        Returns:
            True si el elemento está presente

        Raises:
            ScrapingException: Si el elemento no se encuentra
        """
        try:
            self.driver.wait_for_element(by, selector, timeout)
            logger.info(f"✅ Page loaded - found: {selector}")
            return True
        except Exception as e:
            msg = f"Page validation failed for selector: {selector}"
            logger.error(f"❌ {msg}")
            raise ScrapingException(msg) from e

    def extract_text(
        self,
        selector: str,
        by: str = By.CSS_SELECTOR,
        default: str = ""
    ) -> str:
        """
        Extrae texto de un elemento

        Args:
            selector: Selector del elemento
            by: Tipo de selector
            default: Valor por defecto si no se encuentra

        Returns:
            Texto del elemento o valor por defecto
        """
        try:
            return self.driver.get_element_text(by, selector)
        except ElementNotFoundException:
            logger.warning(f"⚠️ Element not found: {selector}, using default: '{default}'")
            return default

    def extract_attribute(
        self,
        selector: str,
        attribute: str,
        by: str = By.CSS_SELECTOR,
        default: str = ""
    ) -> str:
        """
        Extrae un atributo de un elemento

        Args:
            selector: Selector del elemento
            attribute: Nombre del atributo
            by: Tipo de selector
            default: Valor por defecto

        Returns:
            Valor del atributo o valor por defecto
        """
        try:
            return self.driver.get_element_attribute(by, selector, attribute)
        except ElementNotFoundException:
            logger.warning(f"⚠️ Element not found: {selector}, using default: '{default}'")
            return default

    def extract_table_data(
        self,
        table_selector: str,
        by: str = By.CSS_SELECTOR
    ) -> Dict[str, Any]:
        """
        Extrae datos de una tabla HTML

        Args:
            table_selector: Selector de la tabla
            by: Tipo de selector

        Returns:
            Dict con headers y rows
        """
        try:
            # Aquí se puede implementar lógica genérica de extracción de tablas
            # o delegar a un TableParser especializado
            raise NotImplementedError("Table extraction not implemented in base class")
        except Exception as e:
            logger.error(f"❌ Error extracting table: {e}")
            raise ScrapingException(f"Table extraction failed") from e

    def build_result(
        self,
        status: str,
        data: Any = None,
        message: Optional[str] = None,
        **extras
    ) -> Dict[str, Any]:
        """
        Construye resultado estandarizado

        Args:
            status: 'success' o 'error'
            data: Datos extraídos
            message: Mensaje opcional
            **extras: Campos adicionales

        Returns:
            Dict con resultado
        """
        result = {
            'status': status,
            'data': data,
        }

        if message:
            result['message'] = message

        result.update(extras)
        return result

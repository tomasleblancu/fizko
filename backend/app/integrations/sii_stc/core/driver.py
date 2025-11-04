"""
Selenium Driver para SII STC con capacidad de interceptar requests
"""
import logging
import time
from typing import Optional, List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from seleniumwire import webdriver as wire_webdriver

from ..config import (
    DEFAULT_PAGE_LOAD_TIMEOUT,
    DEFAULT_WINDOW_SIZE
)
from ..exceptions import STCException

logger = logging.getLogger(__name__)


class STCDriver:
    """
    Selenium Driver con capacidad de interceptar requests

    Usa selenium-wire para interceptar requests HTTP y capturar
    el token de reCAPTCHA.

    Features:
    - Intercepta requests a Google reCAPTCHA
    - Captura cookies del navegador
    - Navegación a portal STC del SII
    """

    def __init__(
        self,
        headless: bool = True,
        custom_config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa el driver de Selenium

        Args:
            headless: Ejecutar en modo headless (sin ventana visible)
            custom_config: Configuración personalizada
        """
        self.headless = headless
        self.custom_config = custom_config or {}
        self.driver: Optional[wire_webdriver.Chrome] = None
        self._started = False

        logger.debug(f"🔧 STCDriver initialized (headless={headless})")

    def start(self) -> None:
        """Inicia el driver de Selenium con selenium-wire"""
        if self._started:
            logger.warning("⚠️ Driver already started")
            return

        logger.info("🚀 Starting selenium-wire Chrome driver...")

        # Configurar opciones de Chrome
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")

        # Opciones estándar
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(f"--window-size={DEFAULT_WINDOW_SIZE}")

        # User agent para evitar detección
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        # Deshabilitar automatización detectada
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Configuración de selenium-wire (proxy interno para interceptar requests)
        seleniumwire_options = {
            'disable_encoding': True,  # No comprimir responses
            'verify_ssl': True,
        }

        try:
            # Crear driver con selenium-wire
            self.driver = wire_webdriver.Chrome(
                options=chrome_options,
                seleniumwire_options=seleniumwire_options
            )

            # Configurar timeouts
            timeout = self.custom_config.get('timeout', DEFAULT_PAGE_LOAD_TIMEOUT)
            self.driver.set_page_load_timeout(timeout)

            # Ejecutar script para ocultar webdriver
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            self._started = True
            logger.info("✅ Selenium-wire driver started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start driver: {e}")
            raise STCException(f"Failed to start Selenium driver: {str(e)}")

    def navigate_to(self, url: str, wait_seconds: int = 3) -> None:
        """
        Navega a una URL

        Args:
            url: URL de destino
            wait_seconds: Segundos a esperar después de navegar
        """
        if not self._started or not self.driver:
            raise STCException("Driver not started")

        logger.info(f"🌐 Navigating to: {url}")

        try:
            self.driver.get(url)
            time.sleep(wait_seconds)
            logger.debug(f"✅ Navigation complete (waited {wait_seconds}s)")
        except TimeoutException:
            logger.warning(f"⚠️ Timeout navigating to {url}")
            raise
        except Exception as e:
            logger.error(f"❌ Navigation error: {e}")
            raise STCException(f"Navigation failed: {str(e)}")

    def get_cookies(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las cookies del navegador

        Returns:
            Lista de cookies en formato dict
        """
        if not self._started or not self.driver:
            raise STCException("Driver not started")

        cookies = self.driver.get_cookies()
        if cookies is None:
            cookies = []
        logger.debug(f"🍪 Retrieved {len(cookies)} cookies")
        return cookies

    def get_requests(self, pattern: Optional[str] = None) -> List[Any]:
        """
        Obtiene los requests interceptados por selenium-wire

        Args:
            pattern: Patrón opcional para filtrar URLs (ej: "recaptcha")

        Returns:
            Lista de requests
        """
        if not self._started or not self.driver:
            raise STCException("Driver not started")

        requests = self.driver.requests

        if pattern:
            requests = [r for r in requests if pattern in r.url]
            logger.debug(f"🔍 Found {len(requests)} requests matching '{pattern}'")
        else:
            logger.debug(f"🔍 Found {len(requests)} total requests")

        return requests

    def clear_requests(self) -> None:
        """Limpia el historial de requests interceptados"""
        if not self._started or not self.driver:
            raise STCException("Driver not started")

        del self.driver.requests
        logger.debug("🧹 Cleared request history")

    def wait_for_element(
        self,
        by: By,
        value: str,
        timeout: int = 10
    ) -> Any:
        """
        Espera a que un elemento esté presente

        Args:
            by: Tipo de selector (By.ID, By.XPATH, etc)
            value: Valor del selector
            timeout: Timeout en segundos

        Returns:
            Elemento encontrado
        """
        if not self._started or not self.driver:
            raise STCException("Driver not started")

        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            logger.debug(f"✅ Element found: {by}={value}")
            return element
        except TimeoutException:
            logger.warning(f"⏰ Timeout waiting for element: {by}={value}")
            raise

    def execute_script(self, script: str, *args) -> Any:
        """
        Ejecuta JavaScript en el navegador

        Args:
            script: Código JavaScript a ejecutar
            *args: Argumentos opcionales para el script

        Returns:
            Resultado del script
        """
        if not self._started or not self.driver:
            raise STCException("Driver not started")

        return self.driver.execute_script(script, *args)

    def get_current_url(self) -> str:
        """Obtiene la URL actual"""
        if not self._started or not self.driver:
            raise STCException("Driver not started")

        return self.driver.current_url

    def quit(self) -> None:
        """Cierra el driver"""
        if self.driver:
            logger.info("🔴 Closing driver...")
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"⚠️ Error closing driver: {e}")
            finally:
                self.driver = None
                self._started = False
                logger.info("✅ Driver closed")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.quit()

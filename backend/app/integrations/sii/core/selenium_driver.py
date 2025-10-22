"""
Selenium WebDriver mejorado con mejor abstracción y manejo de errores
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional, Any, Callable, List
import logging
import os

from ..exceptions import (
    DriverNotStartedException,
    DriverTimeoutException,
    ElementNotFoundException
)

logger = logging.getLogger(__name__)


class DriverConfig:
    """Configuración del WebDriver"""

    def __init__(
        self,
        DEFAULT_TIMEOUT: int = 30,
        LONG_TIMEOUT: int = 60,
        PAGE_LOAD_TIMEOUT: int = 60,
        IMPLICIT_WAIT: int = 5,
        HEADLESS: bool = True,
        CHROME_BINARY_PATH: Optional[str] = None,
        CHROME_DRIVER_PATH: Optional[str] = None,
        WINDOW_SIZE: str = "1920,1080",
        CHROME_OPTIONS: Optional[List[str]] = None
    ):
        self.DEFAULT_TIMEOUT = DEFAULT_TIMEOUT
        self.LONG_TIMEOUT = LONG_TIMEOUT
        self.PAGE_LOAD_TIMEOUT = PAGE_LOAD_TIMEOUT
        self.IMPLICIT_WAIT = IMPLICIT_WAIT
        self.HEADLESS = HEADLESS
        self.CHROME_BINARY_PATH = CHROME_BINARY_PATH
        self.CHROME_DRIVER_PATH = CHROME_DRIVER_PATH
        self.WINDOW_SIZE = WINDOW_SIZE
        self.CHROME_OPTIONS = CHROME_OPTIONS or [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-extensions",
            "--disable-blink-features=AutomationControlled",
        ]


class SeleniumDriver:
    """
    Selenium WebDriver con mejor abstracción y manejo de errores
    """

    def __init__(self, config: Optional[DriverConfig] = None):
        self.config = config or DriverConfig()
        self.driver: Optional[webdriver.Chrome] = None
        self._wait: Optional[WebDriverWait] = None
        self._last_error: Optional[str] = None

    def start(self) -> None:
        """Inicializa el WebDriver"""
        if self.driver is not None:
            logger.warning("Driver already started")
            return

        logger.debug("🚀 Starting SeleniumDriver")

        try:
            options = self._get_chrome_options()
            service = self._get_chrome_service()

            self.driver = webdriver.Chrome(service=service, options=options)
            self._wait = WebDriverWait(self.driver, self.config.DEFAULT_TIMEOUT)

            # Configurar timeouts
            self.driver.set_page_load_timeout(self.config.PAGE_LOAD_TIMEOUT)
            self.driver.implicitly_wait(self.config.IMPLICIT_WAIT)

            logger.debug("✅ SeleniumDriver started successfully")

        except Exception as e:
            self._last_error = str(e)
            logger.error(f"❌ Error starting driver: {e}")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            self.driver = None
            self._wait = None
            raise

    def quit(self) -> None:
        """Cierra el WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("🔴 SeleniumDriver closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing driver: {e}")
            finally:
                self.driver = None
                self._wait = None

    def _get_chrome_options(self) -> Options:
        """Configura opciones de Chrome"""
        options = Options()

        if self.config.HEADLESS:
            options.add_argument("--headless=new")

        # Detectar ambiente Docker
        is_docker = self._is_docker_environment()

        # Opciones comunes
        for opt in self.config.CHROME_OPTIONS:
            options.add_argument(opt)

        options.add_argument(f"--window-size={self.config.WINDOW_SIZE}")

        # Opciones específicas para Docker
        if is_docker:
            options.add_argument("--single-process")
            options.add_argument("--disable-setuid-sandbox")

        # Habilitar performance logging para capturar headers de requests
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        # Configurar binario Chrome
        chrome_binary = self.config.CHROME_BINARY_PATH or os.getenv('CHROME_BINARY_PATH')

        if chrome_binary and os.path.exists(chrome_binary):
            options.binary_location = chrome_binary
            logger.info(f"Using Chrome binary: {chrome_binary}")
        elif is_docker:
            # Buscar en rutas comunes de Docker
            for path in ["/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"]:
                if os.path.exists(path):
                    options.binary_location = path
                    logger.info(f"Found Chrome in Docker: {path}")
                    break

        return options

    def _get_chrome_service(self) -> Service:
        """Configura el servicio ChromeDriver"""
        driver_path = self.config.CHROME_DRIVER_PATH or os.getenv('CHROME_DRIVER_PATH')

        if driver_path and os.path.exists(driver_path):
            logger.info(f"Using ChromeDriver: {driver_path}")
            return Service(driver_path)

        # Buscar en rutas Docker
        if self._is_docker_environment():
            for path in ["/usr/bin/chromedriver", "/usr/lib/chromium-browser/chromedriver"]:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    logger.info(f"Found ChromeDriver in Docker: {path}")
                    return Service(path)

        # Fallback a webdriver-manager
        try:
            logger.info("Using webdriver-manager for ChromeDriver")
            chromedriver_path = ChromeDriverManager().install()
            return Service(chromedriver_path)
        except Exception as e:
            logger.error(f"webdriver-manager failed: {e}")
            raise Exception("No valid ChromeDriver found")

    @staticmethod
    def _is_docker_environment() -> bool:
        """Detecta si está corriendo en Docker"""
        return (
            os.getenv('DOCKER_ENV') is not None or
            os.path.exists('/.dockerenv') or
            os.getenv('DOCKER_CONTAINER') is not None
        )

    def _ensure_started(self):
        """Verifica que el driver esté iniciado"""
        if not self.driver:
            raise DriverNotStartedException("Driver not started. Call start() first.")

    # === Métodos de espera ===

    def wait_for_element(
        self,
        by: str,
        selector: str,
        timeout: Optional[int] = None
    ) -> WebElement:
        """Espera a que un elemento esté presente"""
        self._ensure_started()
        timeout = timeout or self.config.DEFAULT_TIMEOUT

        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, selector)))
            return element
        except TimeoutException as e:
            msg = f"Timeout waiting for element: {selector}"
            self._last_error = msg
            logger.error(msg)
            raise DriverTimeoutException(msg, selector=selector, timeout=timeout) from e

    def wait_for_clickable(
        self,
        by: str,
        selector: str,
        timeout: Optional[int] = None
    ) -> WebElement:
        """Espera a que un elemento sea clickeable"""
        self._ensure_started()
        timeout = timeout or self.config.DEFAULT_TIMEOUT

        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable((by, selector)))
            return element
        except TimeoutException as e:
            msg = f"Timeout waiting for clickable element: {selector}"
            self._last_error = msg
            logger.error(msg)
            raise DriverTimeoutException(msg, selector=selector, timeout=timeout) from e

    def wait_for_elements(
        self,
        by: str,
        selector: str,
        timeout: Optional[int] = None
    ) -> List[WebElement]:
        """Espera a que múltiples elementos estén presentes"""
        self._ensure_started()
        timeout = timeout or self.config.DEFAULT_TIMEOUT

        try:
            wait = WebDriverWait(self.driver, timeout)
            elements = wait.until(EC.presence_of_all_elements_located((by, selector)))
            return elements
        except TimeoutException as e:
            msg = f"Timeout waiting for elements: {selector}"
            self._last_error = msg
            logger.error(msg)
            raise DriverTimeoutException(msg, selector=selector, timeout=timeout) from e

    def wait_for_condition(
        self,
        condition: Callable,
        timeout: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Any:
        """Espera genérica para una condición"""
        self._ensure_started()
        timeout = timeout or self.config.DEFAULT_TIMEOUT

        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(condition)
        except TimeoutException as e:
            msg = error_message or f"Timeout waiting for condition"
            self._last_error = msg
            logger.error(msg)
            raise DriverTimeoutException(msg, timeout=timeout) from e

    # === Métodos de interacción ===

    def click(self, element: WebElement) -> None:
        """Click en un elemento con manejo de errores"""
        try:
            element.click()
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            raise

    def send_keys(self, element: WebElement, text: str, clear_first: bool = True) -> None:
        """Envía texto a un elemento"""
        try:
            if clear_first:
                element.clear()
            element.send_keys(text)
        except Exception as e:
            logger.error(f"Error sending keys: {e}")
            raise

    def select_option_by_value(self, element: WebElement, value: str) -> None:
        """Selecciona opción en un dropdown por valor"""
        try:
            select = Select(element)
            select.select_by_value(value)
        except Exception as e:
            logger.error(f"Error selecting option {value}: {e}")
            raise

    def select_option_by_text(self, element: WebElement, text: str) -> None:
        """Selecciona opción en un dropdown por texto"""
        try:
            select = Select(element)
            select.select_by_visible_text(text)
        except Exception as e:
            logger.error(f"Error selecting option {text}: {e}")
            raise

    # === Métodos de obtención de información ===

    def get_element_text(self, by: str, selector: str) -> str:
        """Obtiene el texto de un elemento"""
        try:
            element = self.driver.find_element(by, selector)
            return element.text.strip()
        except NoSuchElementException:
            raise ElementNotFoundException(f"Element not found: {selector}", selector=selector)

    def get_element_attribute(self, by: str, selector: str, attribute: str) -> str:
        """Obtiene un atributo de un elemento"""
        try:
            element = self.driver.find_element(by, selector)
            return element.get_attribute(attribute) or ""
        except NoSuchElementException:
            raise ElementNotFoundException(f"Element not found: {selector}", selector=selector)

    def get_current_url(self) -> str:
        """Obtiene la URL actual"""
        self._ensure_started()
        return self.driver.current_url

    def get_page_source(self) -> str:
        """Obtiene el código fuente de la página"""
        self._ensure_started()
        return self.driver.page_source

    def get_cookies(self) -> List[dict]:
        """Obtiene las cookies actuales"""
        self._ensure_started()
        return self.driver.get_cookies()

    def set_extra_http_headers(self, headers: dict) -> None:
        """
        Establece headers HTTP adicionales usando Chrome DevTools Protocol

        Args:
            headers: Dict de headers a establecer

        Note:
            Estos headers se aplicarán a todas las requests subsecuentes
        """
        self._ensure_started()
        try:
            if headers:
                self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': headers})
                logger.info(f"📋 Set {len(headers)} extra HTTP headers via CDP")
        except Exception as e:
            logger.warning(f"⚠️ Could not set extra headers (CDP may not be available): {e}")

    # === Métodos de navegación ===

    def navigate_to(self, url: str) -> None:
        """Navega a una URL"""
        self._ensure_started()
        logger.debug(f"🌐 Navigating to: {url}")
        self.driver.get(url)

    def execute_script(self, script: str, *args) -> Any:
        """Ejecuta JavaScript"""
        self._ensure_started()
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            raise

    # === Utilidades ===

    def take_screenshot(self, filename: str) -> bool:
        """Toma screenshot"""
        self._ensure_started()
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"📸 Screenshot saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return False

    def get_last_error(self) -> Optional[str]:
        """Retorna el último error"""
        return self._last_error

    def find_element(self, *args, **kwargs):
        """Expone find_element del driver interno para compatibilidad"""
        return self.driver.find_element(*args, **kwargs)

    def find_elements(self, *args, **kwargs):
        """Expone find_elements del driver interno para compatibilidad"""
        return self.driver.find_elements(*args, **kwargs)

    # === Context manager ===

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

"""
Cliente para consultas STC (Sin Autenticación) del SII

Este cliente permite consultar el estado de proveedores y documentos
tributarios sin necesidad de autenticación.

Uso:
    from app.integrations.sii_stc import STCClient

    with STCClient() as client:
        result = client.consultar_documento(
            rut="77794858",
            dv="K"
        )
"""
import logging
import time
import json
import requests
from typing import Dict, Any, Optional, List

from .core import STCDriver, RecaptchaInterceptor
from .config import (
    STC_PORTAL_URL,
    STC_API_URL,
    DEFAULT_PAGE_LOAD_TIMEOUT,
    DEFAULT_RECAPTCHA_WAIT_TIMEOUT,
    DEFAULT_QUERY_TIMEOUT
)
from .exceptions import (
    STCException,
    STCRecaptchaError,
    STCQueryError,
    STCTimeoutError
)

logger = logging.getLogger(__name__)


class STCClient:
    """
    Cliente para consultas STC del SII sin autenticación

    Flujo:
    1. Navegar al portal STC
    2. Capturar cookies del navegador
    3. Interceptar token reCAPTCHA (rresp)
    4. Realizar consulta con cookies + token
    """

    def __init__(
        self,
        headless: bool = True,
        custom_config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa el cliente STC

        Args:
            headless: Ejecutar navegador en modo headless
            custom_config: Configuración personalizada
        """
        self.headless = headless
        self.custom_config = custom_config or {}

        # Componentes (lazy initialization)
        self._driver: Optional[STCDriver] = None
        self._recaptcha_interceptor: Optional[RecaptchaInterceptor] = None

        # Estado
        self._initialized = False
        self._cookies: Optional[List[Dict]] = None
        self._recaptcha_token: Optional[str] = None

        logger.debug("🚀 STCClient initialized")

    def _ensure_initialized(self):
        """Asegura que el cliente esté inicializado"""
        if not self._initialized:
            self._initialize()

    def _initialize(self):
        """Inicializa los componentes"""
        if self._initialized:
            return

        logger.debug("🔧 Initializing STCClient components...")

        # Inicializar driver
        self._driver = STCDriver(
            headless=self.headless,
            custom_config=self.custom_config
        )
        self._driver.start()

        # Inicializar interceptor de reCAPTCHA
        self._recaptcha_interceptor = RecaptchaInterceptor(self._driver)

        self._initialized = True
        logger.debug("✅ STCClient components initialized")

    def prepare(
        self,
        recaptcha_timeout: int = DEFAULT_RECAPTCHA_WAIT_TIMEOUT
    ) -> Dict[str, Any]:
        """
        Prepara el cliente: navega al portal, captura cookies y token reCAPTCHA

        Args:
            recaptcha_timeout: Segundos a esperar por el token reCAPTCHA

        Returns:
            Dict con información de preparación:
            {
                "success": bool,
                "cookies_count": int,
                "recaptcha_token": str (primeros 20 chars)
            }

        Raises:
            STCException: Si falla la preparación
        """
        self._ensure_initialized()

        logger.info("🚀 Preparing STC client...")

        try:
            # 1. Navegar al portal STC
            logger.info(f"🌐 Navigating to STC portal: {STC_PORTAL_URL}")
            self._driver.navigate_to(STC_PORTAL_URL, wait_seconds=5)

            # 2. Capturar cookies
            self._cookies = self._driver.get_cookies()
            logger.info(f"🍪 Captured {len(self._cookies)} cookies")

            # 3. Intentar interactuar con el formulario para trigger reCAPTCHA
            try:
                from selenium.webdriver.common.by import By
                logger.info("👆 Attempting to interact with form to trigger reCAPTCHA...")

                # Intentar hacer click en el campo RUT
                rut_field = self._driver.wait_for_element(
                    By.ID,
                    "rut",
                    timeout=10
                )
                rut_field.click()
                logger.info("✅ Clicked on RUT field")

                # Esperar un poco para que reCAPTCHA se cargue
                time.sleep(3)
            except Exception as e:
                logger.warning(f"⚠️ Could not interact with form: {e}. Continuing anyway...")

            # 4. Esperar e interceptar token reCAPTCHA
            logger.info("⏳ Waiting for reCAPTCHA token...")
            self._recaptcha_token = self._recaptcha_interceptor.wait_and_capture_token(
                timeout=recaptcha_timeout
            )
            logger.info(f"✅ reCAPTCHA token captured: {self._recaptcha_token[:20]}...")

            return {
                "success": True,
                "cookies_count": len(self._cookies),
                "recaptcha_token": self._recaptcha_token[:20] + "..."
            }

        except STCTimeoutError as e:
            logger.error(f"⏰ Timeout during preparation: {e}")
            raise
        except STCRecaptchaError as e:
            logger.error(f"🤖 reCAPTCHA error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Preparation failed: {e}", exc_info=True)
            raise STCException(f"Failed to prepare STC client: {str(e)}")

    def consultar_documento(
        self,
        rut: str,
        dv: str,
        auto_prepare: bool = True,
        timeout: int = DEFAULT_QUERY_TIMEOUT
    ) -> Dict[str, Any]:
        """
        Consulta el estado de un proveedor y sus documentos tributarios

        Args:
            rut: RUT del proveedor (sin DV, sin puntos, solo números)
            dv: Dígito verificador
            auto_prepare: Si True, ejecuta prepare() automáticamente si no se ha hecho
            timeout: Timeout para la consulta en segundos

        Returns:
            Dict con resultado de la consulta desde la API del SII

        Raises:
            STCException: Si no se ha preparado el cliente
            STCQueryError: Si falla la consulta
        """
        self._ensure_initialized()

        # Auto-preparar si es necesario
        if auto_prepare and (not self._cookies or not self._recaptcha_token):
            logger.info("🔄 Auto-preparing client...")
            self.prepare()

        # Validar que tenemos cookies y token
        if not self._cookies or not self._recaptcha_token:
            raise STCException(
                "Client not prepared. Call prepare() first or use auto_prepare=True"
            )

        logger.info(f"🔍 Querying document for RUT: {rut}-{dv}")

        try:
            # Preparar payload
            payload = {
                "rut": rut,
                "dv": dv.upper(),
                "reAction": "consultaSTC",
                "reToken": self._recaptcha_token
            }

            # Preparar headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://www2.sii.cl",
                "Referer": STC_PORTAL_URL,
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }

            # Convertir cookies de Selenium a formato requests
            cookies_dict = {c['name']: c['value'] for c in self._cookies}

            # Realizar consulta
            logger.debug(f"📤 Sending query to: {STC_API_URL}")
            logger.debug(f"📦 Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                STC_API_URL,
                json=payload,
                headers=headers,
                cookies=cookies_dict,
                timeout=timeout
            )

            # Validar respuesta
            logger.debug(f"📥 Response status: {response.status_code}")

            if response.status_code != 200:
                raise STCQueryError(
                    f"API returned status {response.status_code}: {response.text}"
                )

            # Parsear respuesta JSON
            try:
                result = response.json()
                logger.info(f"✅ Query successful for RUT {rut}-{dv}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response.text[:500]}")
                raise STCQueryError(f"Invalid JSON response: {str(e)}")

        except requests.Timeout:
            logger.error(f"⏰ Query timeout after {timeout}s")
            raise STCTimeoutError(f"Query timeout after {timeout}s")
        except requests.RequestException as e:
            logger.error(f"❌ Request error: {e}")
            raise STCQueryError(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error during query: {e}", exc_info=True)
            raise STCQueryError(f"Query failed: {str(e)}")

    def get_cookies(self) -> Optional[List[Dict]]:
        """
        Obtiene las cookies capturadas

        Returns:
            Lista de cookies o None si no se han capturado
        """
        return self._cookies

    def get_recaptcha_token(self) -> Optional[str]:
        """
        Obtiene el token reCAPTCHA capturado

        Returns:
            Token o None si no se ha capturado
        """
        return self._recaptcha_token

    def is_prepared(self) -> bool:
        """
        Verifica si el cliente está preparado (tiene cookies y token)

        Returns:
            True si está preparado
        """
        return bool(self._cookies and self._recaptcha_token)

    def close(self) -> None:
        """Cierra el cliente y libera recursos"""
        logger.debug("🔴 Closing STCClient...")

        if self._driver:
            self._driver.quit()

        self._driver = None
        self._recaptcha_interceptor = None
        self._cookies = None
        self._recaptcha_token = None
        self._initialized = False

        logger.debug("✅ STCClient closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

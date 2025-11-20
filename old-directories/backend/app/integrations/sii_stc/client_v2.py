"""
Cliente STC v2 - Workaround: Llenar formulario e interceptar payload

En lugar de interceptar reCAPTCHA directamente, este cliente:
1. Llena el formulario con RUT y DV
2. Hace click en "Consultar"
3. Intercepta el request POST completo (incluyendo reToken)
4. Extrae la respuesta

Esto es mucho más robusto y no depende de entender cómo reCAPTCHA genera el token.
"""
import logging
import time
import json
import requests
from typing import Dict, Any, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .core import STCDriver
from .config import STC_PORTAL_URL, STC_API_URL
from .exceptions import STCException, STCQueryError, STCTimeoutError

logger = logging.getLogger(__name__)


class STCClientV2:
    """
    Cliente STC v2 - Workaround con llenado de formulario

    En lugar de interceptar reCAPTCHA, llena el formulario y captura
    el request POST completo que envía el navegador.
    """

    def __init__(
        self,
        headless: bool = True,
        custom_config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa el cliente STC v2

        Args:
            headless: Ejecutar navegador en modo headless
            custom_config: Configuración personalizada
        """
        self.headless = headless
        self.custom_config = custom_config or {}

        # Componentes
        self._driver: Optional[STCDriver] = None

        # Estado
        self._initialized = False
        self._last_retoken: Optional[str] = None
        self._last_cookies: Optional[Dict[str, str]] = None
        self._last_headers: Optional[Dict[str, str]] = None

        logger.debug("🚀 STCClientV2 initialized")

    def _ensure_initialized(self):
        """Asegura que el cliente esté inicializado"""
        if not self._initialized:
            self._initialize()

    def _initialize(self):
        """Inicializa los componentes"""
        if self._initialized:
            return

        logger.debug("🔧 Initializing STCClientV2 components...")

        # Inicializar driver
        self._driver = STCDriver(
            headless=self.headless,
            custom_config=self.custom_config
        )
        self._driver.start()

        self._initialized = True
        logger.debug("✅ STCClientV2 components initialized")

    def consultar_documento(
        self,
        rut: str,
        dv: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Consulta documento llenando el formulario e interceptando el POST

        Args:
            rut: RUT del proveedor (sin puntos, sin guión)
            dv: Dígito verificador
            timeout: Timeout en segundos

        Returns:
            Dict con resultado de la API del SII

        Raises:
            STCException: Si falla el proceso
            STCTimeoutError: Si timeout
            STCQueryError: Si falla la consulta
        """
        self._ensure_initialized()

        logger.info(f"🔍 Querying document for RUT: {rut}-{dv}")

        try:
            # 1. Navegar al portal STC
            logger.info(f"🌐 Navigating to STC portal: {STC_PORTAL_URL}")
            self._driver.navigate_to(STC_PORTAL_URL, wait_seconds=5)

            # 2. Limpiar requests anteriores para capturar solo el POST que nos interesa
            self._driver.clear_requests()
            logger.debug("🧹 Cleared previous requests")

            # 3. Encontrar y llenar el campo RUT
            logger.info("✏️ Filling form...")

            # Formatear RUT con puntos y guión (77.794.858-K)
            rut_formatted = self._format_rut(rut, dv)
            logger.debug(f"📝 Formatted RUT: {rut_formatted}")

            # Esperar que el campo esté visible
            rut_input = WebDriverWait(self._driver.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.rut-form"))
            )

            # Llenar el campo RUT
            rut_input.clear()
            rut_input.send_keys(rut_formatted)
            logger.info(f"✅ Filled RUT field: {rut_formatted}")

            # Esperar un momento para que el formulario procese la entrada
            time.sleep(1)

            # 4. Hacer click en "Consultar"
            logger.info("👆 Clicking 'Consultar' button...")

            consultar_button = WebDriverWait(self._driver.driver, 10).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "input[name='Consultar'][type='button']"
                ))
            )
            consultar_button.click()
            logger.info("✅ Clicked 'Consultar' button")

            # 5. Esperar e interceptar el POST a la API
            logger.info(f"⏳ Waiting for POST to {STC_API_URL}...")

            post_request = self._wait_for_post_request(timeout=timeout)

            if not post_request:
                raise STCTimeoutError(
                    f"No POST request to API found after {timeout}s"
                )

            logger.info("✅ POST request captured!")

            # 6. Extraer el payload para guardar el reToken
            payload = self._extract_payload(post_request)
            if payload and 'reToken' in payload:
                self._last_retoken = payload['reToken']
                logger.info(f"✅ reToken captured ({len(self._last_retoken)} chars)")

            # 7. Guardar cookies y headers del request
            if hasattr(post_request, 'headers'):
                self._last_headers = dict(post_request.headers)
                logger.debug(f"✅ Headers captured: {list(self._last_headers.keys())[:5]}...")

            # Obtener cookies del driver
            self._last_cookies = {c['name']: c['value'] for c in self._driver.get_cookies()}
            logger.debug(f"✅ Cookies captured: {len(self._last_cookies)} cookies")

            # 8. Extraer la respuesta del request
            result = self._extract_response(post_request)

            logger.info(f"✅ Query successful for RUT {rut}-{dv}")
            return result

        except TimeoutException as e:
            logger.error(f"⏰ Timeout waiting for elements: {e}")
            raise STCTimeoutError(f"Timeout: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Query failed: {e}", exc_info=True)
            raise STCQueryError(f"Query failed: {str(e)}")

    def consultar_con_retoken(
        self,
        rut: str,
        dv: str,
        retoken: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Consulta documento usando un reToken previamente capturado

        Este método hace una llamada HTTP directa al API del SII usando
        el reToken obtenido en una consulta anterior. No requiere Selenium.

        Args:
            rut: RUT del proveedor (sin puntos, sin guión)
            dv: Dígito verificador
            retoken: reToken de reCAPTCHA. Si es None, usa el último capturado

        Returns:
            Dict con resultado de la API del SII

        Raises:
            STCException: Si no hay reToken disponible
            STCQueryError: Si falla la consulta
        """
        # Usar el reToken proporcionado o el último capturado
        token = retoken or self._last_retoken

        if not token:
            raise STCException(
                "No reToken available. Call consultar_documento() first or provide a retoken."
            )

        logger.info(f"🔍 Querying with reToken for RUT: {rut}-{dv}")

        try:
            # Construir payload
            payload = {
                "rut": rut,
                "dv": dv.upper(),
                "reAction": "consultaSTC",
                "reToken": token
            }

            # Construir headers base
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://www2.sii.cl",
                "Referer": "https://www2.sii.cl/stc/noauthz/consulta",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
            }

            # Si tenemos headers capturados, copiar los importantes
            if self._last_headers:
                important_keys = [
                    'User-Agent', 'Accept-Language', 'Accept-Encoding',
                    'Cookie', 'x-dtreferer', 'x-dtpc',
                    'sec-ch-ua', 'sec-ch-ua-mobile', 'sec-ch-ua-platform'
                ]
                for key in important_keys:
                    if key in self._last_headers:
                        headers[key] = self._last_headers[key]
                        logger.debug(f"   Copied header: {key}")

            # Hacer POST request directo
            logger.debug(f"📤 Sending POST to {STC_API_URL}")
            logger.debug(f"   Headers: {list(headers.keys())}")

            response = requests.post(
                STC_API_URL,
                json=payload,
                headers=headers,
                timeout=30
            )

            # Verificar status code
            response.raise_for_status()

            # Parsear respuesta
            result = response.json()
            logger.info(f"✅ Query with reToken successful for RUT {rut}-{dv}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ HTTP request failed: {e}")
            raise STCQueryError(f"HTTP request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            raise STCQueryError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Query with reToken failed: {e}", exc_info=True)
            raise STCQueryError(f"Query failed: {str(e)}")

    def _format_rut(self, rut: str, dv: str) -> str:
        """
        Formatea el RUT con puntos y guión (ej: 77.794.858-K)

        Args:
            rut: RUT sin formato (77794858)
            dv: Dígito verificador (K)

        Returns:
            RUT formateado (77.794.858-K)
        """
        # Asegurar que rut es string sin puntos ni guiones
        rut_clean = str(rut).replace(".", "").replace("-", "")

        # Agregar puntos cada 3 dígitos de derecha a izquierda
        rut_reversed = rut_clean[::-1]
        rut_with_dots = ".".join([rut_reversed[i:i+3] for i in range(0, len(rut_reversed), 3)])
        rut_formatted = rut_with_dots[::-1]

        # Agregar guión y DV
        return f"{rut_formatted}-{dv.upper()}"

    def _wait_for_post_request(self, timeout: int = 30) -> Optional[Any]:
        """
        Espera a que aparezca el POST request a la API del SII con su respuesta

        Args:
            timeout: Segundos máximos a esperar

        Returns:
            Request encontrado o None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Buscar requests POST a la API
            requests = self._driver.get_requests(pattern="getConsultaData")

            for req in requests:
                if req.method == "POST" and STC_API_URL in req.url:
                    # Verificar que tenga respuesta
                    if req.response:
                        logger.debug(f"✅ Found POST request with response: {req.url}")
                        return req
                    else:
                        logger.debug(f"⏳ POST request found but waiting for response...")

            # Esperar un poco antes de volver a buscar
            time.sleep(0.5)

        return None

    def _extract_payload(self, request) -> Optional[Dict[str, Any]]:
        """
        Extrae el payload (request body) del request interceptado

        Args:
            request: Request interceptado de selenium-wire

        Returns:
            Dict con el payload o None si no se puede extraer
        """
        if not hasattr(request, 'body') or not request.body:
            logger.debug("⚠️ Request has no body")
            return None

        try:
            payload_str = request.body.decode('utf-8')
            logger.debug(f"📦 Payload length: {len(payload_str)} chars")

            # Try to parse as JSON
            payload = json.loads(payload_str)
            logger.debug(f"✅ Payload parsed as JSON with keys: {list(payload.keys())}")

            return payload

        except json.JSONDecodeError:
            logger.debug("⚠️ Payload is not JSON")
            return None
        except Exception as e:
            logger.debug(f"⚠️ Failed to extract payload: {e}")
            return None

    def _extract_response(self, request) -> Dict[str, Any]:
        """
        Extrae la respuesta JSON del request interceptado

        Args:
            request: Request interceptado de selenium-wire

        Returns:
            Dict con la respuesta de la API

        Raises:
            STCQueryError: Si no se puede extraer la respuesta
        """
        if not request.response:
            raise STCQueryError("No response in POST request")

        try:
            # Obtener el body de la respuesta
            body = request.response.body.decode('utf-8')
            logger.debug(f"📄 Response body length: {len(body)} chars")

            # Parsear JSON
            result = json.loads(body)
            logger.debug(f"✅ Response parsed successfully")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.error(f"Response text: {body[:500] if body else 'empty'}")
            raise STCQueryError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Failed to extract response: {e}")
            raise STCQueryError(f"Failed to extract response: {str(e)}")

    def close(self) -> None:
        """Cierra el cliente y libera recursos"""
        logger.debug("🔴 Closing STCClientV2...")

        if self._driver:
            self._driver.quit()

        self._driver = None
        self._initialized = False

        logger.debug("✅ STCClientV2 closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

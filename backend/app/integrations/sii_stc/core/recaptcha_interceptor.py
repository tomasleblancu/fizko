"""
Interceptor de reCAPTCHA para extraer el token rresp
"""
import logging
import time
import json
import re
from typing import Optional, Dict, Any

from ..config import (
    RECAPTCHA_RELOAD_URL,
    DEFAULT_RECAPTCHA_WAIT_TIMEOUT
)
from ..exceptions import STCRecaptchaError, STCTimeoutError

logger = logging.getLogger(__name__)


class RecaptchaInterceptor:
    """
    Intercepta requests de reCAPTCHA y extrae el token rresp

    El flujo es:
    1. Navegar a la página STC
    2. Esperar a que se cargue reCAPTCHA
    3. Interceptar el request a recaptcha/enterprise/reload
    4. Parsear la respuesta y extraer el rresp token
    """

    def __init__(self, driver):
        """
        Inicializa el interceptor

        Args:
            driver: Instancia de STCDriver
        """
        self.driver = driver
        logger.debug("🔧 RecaptchaInterceptor initialized")

    def wait_and_capture_token(
        self,
        timeout: int = DEFAULT_RECAPTCHA_WAIT_TIMEOUT,
        clear_previous: bool = True
    ) -> str:
        """
        Espera y captura el token rresp de reCAPTCHA

        Args:
            timeout: Segundos máximos a esperar
            clear_previous: Limpiar requests previos antes de esperar

        Returns:
            Token rresp extraído

        Raises:
            STCRecaptchaError: Si falla la extracción del token
            STCTimeoutError: Si timeout esperando el request
        """
        logger.info(f"⏳ Waiting for reCAPTCHA token (timeout={timeout}s)...")

        # Limpiar requests previos si se solicita
        if clear_previous:
            self.driver.clear_requests()
            logger.debug("🧹 Cleared previous requests")

        # Esperar a que aparezca el request de reCAPTCHA
        start_time = time.time()
        recaptcha_request = None

        while time.time() - start_time < timeout:
            # Buscar el request de reload
            requests = self.driver.get_requests(pattern="recaptcha/enterprise/reload")

            if requests:
                # Tomar el último request (el más reciente)
                recaptcha_request = requests[-1]
                logger.debug(f"✅ Found reCAPTCHA request: {recaptcha_request.url}")
                break

            # Esperar un poco antes de volver a buscar
            time.sleep(0.5)

        if not recaptcha_request:
            raise STCTimeoutError(
                f"No reCAPTCHA request found after {timeout}s"
            )

        # Extraer el token de la respuesta
        try:
            token = self._extract_rresp_token(recaptcha_request)
            logger.info(f"✅ reCAPTCHA token captured: {token[:20]}...")
            return token
        except Exception as e:
            logger.error(f"❌ Failed to extract rresp token: {e}")
            raise STCRecaptchaError(f"Failed to extract rresp token: {str(e)}")

    def _extract_rresp_token(self, request) -> str:
        """
        Extrae el token rresp de la respuesta del request de reCAPTCHA

        La respuesta tiene el formato:
        )
        ]
        }'
        ["rresp","<TOKEN>",1]

        Args:
            request: Request interceptado de selenium-wire

        Returns:
            Token rresp

        Raises:
            STCRecaptchaError: Si no se puede extraer el token
        """
        if not request.response:
            raise STCRecaptchaError("No response in reCAPTCHA request")

        # Obtener el body de la respuesta
        try:
            body = request.response.body.decode('utf-8')
            logger.debug(f"📄 Response body length: {len(body)} chars")
        except Exception as e:
            raise STCRecaptchaError(f"Failed to decode response body: {str(e)}")

        # Parsear la respuesta
        # El formato es:
        # )
        # ]
        # }'
        # ["rresp","<TOKEN>",1]

        # Buscar el patrón ["rresp","..."]
        pattern = r'\["rresp","([^"]+)",\d+\]'
        match = re.search(pattern, body)

        if not match:
            logger.error(f"❌ Pattern not found in response body. Body preview: {body[:500]}")
            raise STCRecaptchaError("rresp token pattern not found in response")

        token = match.group(1)

        if not token:
            raise STCRecaptchaError("Empty rresp token extracted")

        logger.debug(f"✅ Extracted token: {token[:30]}...")
        return token

    def get_latest_token(self) -> Optional[str]:
        """
        Intenta obtener el token de los requests ya interceptados
        (sin esperar)

        Returns:
            Token si se encuentra, None en caso contrario
        """
        requests = self.driver.get_requests(pattern="recaptcha/enterprise/reload")

        if not requests:
            logger.debug("⚠️ No reCAPTCHA requests found")
            return None

        # Tomar el último request
        latest_request = requests[-1]

        try:
            token = self._extract_rresp_token(latest_request)
            logger.info(f"✅ Latest token retrieved: {token[:20]}...")
            return token
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract token from latest request: {e}")
            return None

"""
Handler de autenticación para el SII
"""
import time
import logging
from typing import Dict, Any, List
from selenium.webdriver.common.by import By

from .selenium_driver import SeleniumDriver
from .session import SessionManager
from ..exceptions import (
    AuthenticationException,
    InvalidCredentialsException,
    SIIUnavailableException,
    PageNotLoadedException,
    UnexpectedRedirectException
)

logger = logging.getLogger(__name__)


def capture_important_headers(driver: SeleniumDriver) -> Dict[str, str]:
    """
    Captura headers HTTP importantes del navegador y de requests reales

    Args:
        driver: SeleniumDriver instance

    Returns:
        Dict con headers importantes
    """
    headers = {}

    try:
        # Capturar User-Agent del navegador
        user_agent = driver.driver.execute_script("return navigator.userAgent;")
        if user_agent:
            headers['User-Agent'] = user_agent

        # Capturar idioma
        language = driver.driver.execute_script("return navigator.language;")
        if language:
            headers['Accept-Language'] = f"{language},en-US;q=0.9,en;q=0.8"

        # Headers comunes para aplicaciones GWT
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        headers['Accept-Encoding'] = 'gzip, deflate, br'
        headers['Connection'] = 'keep-alive'

        # Capturar headers GWT desde performance logs (requests reales)
        try:
            # Obtener logs de performance que contienen headers de requests
            logs = driver.driver.get_log('performance')

            for log in logs:
                try:
                    import json
                    message = json.loads(log['message'])

                    # Buscar eventos de tipo Network.requestWillBeSent
                    if message.get('message', {}).get('method') == 'Network.requestWillBeSent':
                        request_headers = message.get('message', {}).get('params', {}).get('request', {}).get('headers', {})

                        # Capturar headers GWT específicos
                        if 'X-GWT-Permutation' in request_headers:
                            headers['X-GWT-Permutation'] = request_headers['X-GWT-Permutation']
                            logger.info(f"✅ Captured X-GWT-Permutation: {request_headers['X-GWT-Permutation']}")

                        if 'X-GWT-Module-Base' in request_headers:
                            headers['X-GWT-Module-Base'] = request_headers['X-GWT-Module-Base']
                            logger.info(f"✅ Captured X-GWT-Module-Base")

                        # Capturar otros headers importantes de requests
                        for header_name in ['Referer', 'Origin']:
                            if header_name in request_headers and header_name not in headers:
                                headers[header_name] = request_headers[header_name]

                except Exception as e:
                    # Ignorar errores en logs individuales
                    continue

        except Exception as e:
            logger.warning(f"⚠️ Could not capture headers from performance logs: {e}")

        logger.info(f"📋 Captured {len(headers)} HTTP headers")

    except Exception as e:
        logger.warning(f"⚠️ Error capturing headers: {e}")

    return headers


def capture_gwt_response(driver: SeleniumDriver, url_filter: str = "svcConsulta", method_filter: str = "getDocumentosBusqueda") -> str:
    """
    Captura el response body de requests GWT-RPC desde performance logs

    Args:
        driver: SeleniumDriver instance
        url_filter: String que debe estar en la URL del request (default: "svcConsulta")
        method_filter: Método GWT-RPC a buscar en el payload (default: "getDocumentosBusqueda")

    Returns:
        Response body del request GWT-RPC, o string vacío si no se encuentra
    """
    response_body = ""

    try:
        import json
        import base64

        # Obtener logs de performance
        logs = driver.driver.get_log('performance')

        # Buscar TODOS los requests a svcConsulta y filtrar por el método correcto
        target_request_id = None

        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')

                # Buscar todos los requests a svcConsulta
                if method == 'Network.requestWillBeSent':
                    params = message.get('message', {}).get('params', {})
                    request_url = params.get('request', {}).get('url', '')
                    post_data = params.get('request', {}).get('postData', '')

                    # Verificar URL y que el payload contenga el método que buscamos
                    if url_filter in request_url:
                        if method_filter in post_data:
                            target_request_id = params.get('requestId')
                            logger.info(f"🎯 Found GWT request to {url_filter} with method '{method_filter}', requestId: {target_request_id}")
                            break
                        else:
                            # Log para debug: encontramos svcConsulta pero con otro método
                            logger.debug(f"⏭️ Skipping svcConsulta request (method '{method_filter}' not in payload)")

            except Exception as e:
                continue

        # Si encontramos el request, buscar su response
        if target_request_id:
            for log in logs:
                try:
                    message = json.loads(log['message'])
                    method = message.get('message', {}).get('method', '')

                    # Buscar el response correspondiente
                    if method == 'Network.responseReceived':
                        params = message.get('message', {}).get('params', {})
                        request_id = params.get('requestId')

                        if request_id == target_request_id:
                            logger.info(f"✅ Found matching response for requestId: {request_id}")

                            # Obtener el body del response usando el requestId
                            try:
                                response_data = driver.driver.execute_cdp_cmd(
                                    'Network.getResponseBody',
                                    {'requestId': request_id}
                                )

                                # El body puede estar en base64 o como string
                                if response_data.get('base64Encoded'):
                                    response_body = base64.b64decode(response_data['body']).decode('utf-8')
                                else:
                                    response_body = response_data.get('body', '')

                                logger.info(f"📦 Captured GWT response body ({len(response_body)} chars)")
                                break

                            except Exception as e:
                                logger.warning(f"⚠️ Could not get response body: {e}")

                except Exception as e:
                    continue

        else:
            logger.warning(f"⚠️ No request found with URL filter: {url_filter}")

    except Exception as e:
        logger.warning(f"⚠️ Error capturing GWT response: {e}")

    return response_body


class AuthenticationHandler:
    """
    Maneja el proceso de autenticación en el portal SII
    """

    # URLs del SII
    MISIIR_BASE_URL = "https://misiir.sii.cl/cgi_misii/siihome.cgi"
    LOGIN_URL = f"https://zeusr.sii.cl/AUT2000/InicioAutenticacion/IngresoRutClave.html?{MISIIR_BASE_URL}"

    def __init__(
        self,
        driver: SeleniumDriver,
        session_manager: SessionManager,
        tax_id: str,
        password: str
    ):
        self.driver = driver
        self.session_manager = session_manager
        self.tax_id = tax_id
        self.password = password

    def authenticate(self, force_new: bool = False) -> bool:
        """
        Autentica en el SII

        Args:
            force_new: Si True, fuerza nueva autenticación sin usar cookies

        Returns:
            True si autenticación exitosa

        Raises:
            InvalidCredentialsException: Credenciales inválidas
            SIIUnavailableException: SII no disponible
            AuthenticationException: Otro error de autenticación
        """
        logger.debug(f"🔐 Starting authentication for {self.tax_id}")

        # Si no es forzado, intentar con cookies existentes
        if not force_new:
            cookies = self.session_manager.get_cookies()
            if cookies and self._validate_cookies(cookies):
                logger.debug("✅ Using existing valid cookies")

                # Aplicar headers guardados si existen
                headers = self.session_manager.get_headers()
                if headers:
                    self.driver.set_extra_http_headers(headers)

                return True

        logger.debug("🔄 Performing fresh login")

        # Realizar login
        return self._perform_login()

    def _perform_login(self) -> bool:
        """
        Ejecuta el proceso de login completo

        Returns:
            True si login exitoso
        """
        try:
            # Navegar a página de login
            self.driver.navigate_to(self.LOGIN_URL)
            logger.debug(f"📄 Navigated to login page")
            # time.sleep(2)  # ⚡ REMOVED - Testing without delay

            # Llenar formulario
            self._fill_login_form()

            # Hacer clic en login
            login_button = self.driver.wait_for_clickable(By.ID, "bt_ingresar", timeout=15)
            current_url_before = self.driver.get_current_url()

            login_button.click()
            logger.debug("🖱️ Clicked login button")

            # Esperar cambio de URL
            self._wait_for_redirect(current_url_before)

            # Verificar resultado del login
            result = self._verify_login_result()

            if result['status'] == 'success':
                # Guardar sesión solo con cookies
                self.session_manager.save_session(
                    cookies=result['cookies'],
                    username=self.tax_id
                )
                logger.info("✅ Login successful")
                return True

            elif result['status'] == 'sii_unavailable':
                raise SIIUnavailableException(
                    result['message'],
                    retry_after=result.get('retry_after')
                )

            else:
                raise InvalidCredentialsException(result['message'])

        except (InvalidCredentialsException, SIIUnavailableException):
            raise
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            raise AuthenticationException(f"Login failed: {str(e)}") from e

    def _fill_login_form(self) -> None:
        """Llena el formulario de login"""
        # RUT
        rut_input = self.driver.wait_for_element(By.ID, "rutcntr", timeout=15)
        normalized_rut = self.tax_id.upper()
        self.driver.send_keys(rut_input, normalized_rut, clear_first=True)
        logger.debug(f"✏️ Entered RUT: {normalized_rut}")

        # Password
        clave_input = self.driver.wait_for_element(By.ID, "clave", timeout=15)
        self.driver.send_keys(clave_input, self.password, clear_first=True)
        logger.debug("✏️ Entered password")

    def _wait_for_redirect(self, initial_url: str, max_wait: int = 20) -> None:
        """
        Espera a que el SII procese el login y redirija

        Args:
            initial_url: URL inicial antes del login
            max_wait: Tiempo máximo de espera en segundos
        """
        logger.debug("⏳ Waiting for SII to process login...")
        wait_count = 0

        while wait_count < max_wait:
            time.sleep(1)
            new_url = self.driver.get_current_url()

            if new_url != initial_url:
                logger.debug(f"✅ URL changed after {wait_count + 1}s: {new_url}")

                # Si llegamos a misiir, dar tiempo extra para carga completa
                if "misiir.sii.cl" in new_url:
                    logger.debug("🎯 Reached MiSII, waiting for complete load...")
                    # time.sleep(2)  # ⚡ REMOVED - Testing without delay

                break

            wait_count += 1

        # Tiempo extra para cookies
        # time.sleep(2)  # ⚡ REMOVED - Testing without delay

    def _verify_login_result(self) -> Dict[str, Any]:
        """
        Verifica el resultado del login analizando la URL actual

        Returns:
            Dict con status, message, cookies, url
        """
        current_url = self.driver.get_current_url()
        logger.debug(f"🌐 Current URL after login: {current_url}")

        # CASO 1: Login exitoso - llegó directo a MiSII
        if "misiir.sii.cl" in current_url and "login" not in current_url.lower():
            cookies = self.driver.get_cookies()
            logger.debug(f"✅ Direct login success - {len(cookies)} cookies obtained")

            return {
                "status": "success",
                "message": "Login successful - direct access to MiSII",
                "cookies": cookies,
                "url": current_url
            }

        # CASO 2: Error del SII - servicio no disponible
        if "/ayudas/900.html" in current_url:
            return {
                "status": "sii_unavailable",
                "message": "SII service temporarily unavailable",
                "cookies": None,
                "url": current_url,
                "retry_after": 300
            }

        # CASO 3: Página de error del SII
        if "/ayudas/" in current_url:
            return {
                "status": "sii_error",
                "message": f"SII error page: {current_url}",
                "cookies": None,
                "url": current_url,
                "retry_after": 180
            }

        # CASO 4: En CAutInicio.cgi - verificar si es login exitoso o fallido
        if "zeusr.sii.cl" in current_url and "CAutInicio.cgi" in current_url:
            return self._verify_caut_inicio(current_url)

        # CASO 5: Otros casos de MiSII o Homer
        if "misiir.sii.cl" in current_url or "homer.sii.cl" in current_url:
            cookies = self.driver.get_cookies()
            return {
                "status": "success",
                "message": "Login successful",
                "cookies": cookies,
                "url": current_url
            }

        # CASO 6: URL inesperada
        return {
            "status": "error",
            "message": f"Unexpected URL after login: {current_url}",
            "cookies": None,
            "url": current_url
        }

    def _verify_caut_inicio(self, current_url: str) -> Dict[str, Any]:
        """
        Verifica si CAutInicio.cgi es un login exitoso o fallido

        Returns:
            Dict con status y resultado
        """
        logger.debug("🔄 Verifying CAutInicio.cgi...")

        # Obtener cookies actuales
        cookies = self.driver.get_cookies()
        logger.debug(f"🍪 Found {len(cookies)} cookies")

        # Buscar errores en la página
        try:
            page_source = self.driver.get_page_source().lower()
            error_indicators = [
                'usuario y/o clave incorrectos',
                'credenciales incorrectas',
                'error de autenticación',
                'acceso denegado'
            ]

            for error_msg in error_indicators:
                if error_msg in page_source:
                    logger.error(f"❌ Error detected: {error_msg}")
                    return {
                        "status": "error",
                        "message": f"SII error: {error_msg}",
                        "cookies": None,
                        "url": current_url
                    }
        except Exception as e:
            logger.warning(f"⚠️ Error checking page content: {e}")

        # Intentar navegar a MiSII para confirmar
        try:
            logger.debug("🔍 Attempting to access MiSII to verify authentication...")

            # Capturar cookies antes de navegar
            initial_cookies = self.driver.get_cookies()

            self.driver.navigate_to("https://misiir.sii.cl/cgi_misii/siihome.cgi")
            # time.sleep(2)  # ⚡ REMOVED - Testing without delay

            final_url = self.driver.get_current_url()
            logger.debug(f"🌐 URL after MiSII navigation: {final_url}")

            # Si fue redirigido al login, credenciales incorrectas
            if "IngresoRutClave.html" in final_url or "InicioAutenticacion" in final_url:
                logger.error("❌ Redirected back to login - invalid credentials")
                return {
                    "status": "error",
                    "message": "Invalid credentials or session not established",
                    "cookies": None,
                    "url": final_url
                }

            # Combinar cookies de ambos dominios
            misii_cookies = self.driver.get_cookies()
            combined_cookies = {}

            for cookie in initial_cookies + misii_cookies:
                key = (cookie.get('name'), cookie.get('domain'))
                combined_cookies[key] = cookie

            all_cookies = list(combined_cookies.values())
            logger.debug(f"🍪 Combined cookies: {len(all_cookies)}")

            # Verificar acceso exitoso
            if ("misiir.sii.cl" in final_url and
                "error" not in final_url.lower() and
                "login" not in final_url.lower() and
                len(all_cookies) > 1):

                logger.debug("✅ Login confirmed - MiSII access ok")
                return {
                    "status": "success",
                    "message": "Login successful - confirmed with MiSII access",
                    "cookies": all_cookies,
                    "url": final_url
                }

        except Exception as e:
            logger.error(f"❌ Error navigating to MiSII: {e}")

        # Si llegamos aquí, login falló
        return {
            "status": "error",
            "message": "Invalid credentials - could not access MiSII",
            "cookies": None,
            "url": current_url
        }

    def _validate_cookies(self, cookies: List[Dict]) -> bool:
        """
        Valida si las cookies son válidas haciendo una consulta simple

        Args:
            cookies: Lista de cookies a validar

        Returns:
            True si cookies válidas
        """
        try:
            # Aquí se podría implementar validación haciendo una consulta simple
            # Por ahora, asumimos válidas si existen
            return len(cookies) > 0
        except Exception as e:
            logger.warning(f"⚠️ Cookie validation error: {e}")
            return False

    def get_fresh_cookies(self) -> List[Dict]:
        """
        Obtiene cookies frescas realizando login

        Returns:
            Lista de cookies
        """
        self._perform_login()
        return self.driver.get_cookies()

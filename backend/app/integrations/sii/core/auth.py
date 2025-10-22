"""
Autenticación con el SII - Basado en v2
"""
import logging
from typing import List, Dict

from .auth_handler import AuthenticationHandler
from .driver import SeleniumDriver
from .session import SessionManager
from ..exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class Authenticator:
    """
    Maneja autenticación con el SII

    Simplifica y encapsula AuthenticationHandler de v2
    """

    def __init__(
        self,
        driver: SeleniumDriver,
        session_manager: SessionManager,
        tax_id: str,
        password: str
    ):
        """
        Inicializa el autenticador

        Args:
            driver: Instancia de SeleniumDriver
            session_manager: Instancia de SessionManager
            tax_id: RUT del contribuyente
            password: Contraseña del SII
        """
        self.driver = driver
        self.session_manager = session_manager
        self.tax_id = tax_id
        self.password = password

        # Crear handler interno
        self._v2_handler = AuthenticationHandler(
            driver=driver,
            session_manager=session_manager,
            tax_id=tax_id,
            password=password
        )

        logger.debug(f"🔐 Authenticator initialized for {tax_id}")

    def authenticate(self, force_new: bool = False) -> bool:
        """
        Autentica con el SII y obtiene cookies para todos los servicios

        Args:
            force_new: Forzar nueva autenticación (ignorar cookies guardadas)

        Returns:
            True si autenticación exitosa

        Raises:
            AuthenticationError: Si falla la autenticación
        """
        try:
            logger.debug(f"🔐 Authenticating (force_new={force_new})...")

            # Delegar a handler de v2
            success = self._v2_handler.authenticate(force_new=force_new)

            if success:
                logger.info("✅ Authentication successful")

                # Guardar cookies de MiSII antes de navegar
                misiir_cookies = self.driver.get_cookies()
                logger.debug(f"💾 Saved {len(misiir_cookies)} MiSII cookies")

                # Navegar al portal RCV para obtener cookies de la API
                rcv_cookies = self._obtain_rcv_cookies()

                # Combinar cookies de ambos dominios
                all_cookies = self._merge_cookies(misiir_cookies, rcv_cookies)
                logger.debug(f"🔗 Merged cookies: {len(all_cookies)} total from both domains")

                # Actualizar session manager con todas las cookies
                self.session_manager.save_session(all_cookies)
            else:
                logger.error("❌ Authentication failed")
                raise AuthenticationError(
                    f"Authentication failed for {self.tax_id}",
                    tax_id=self.tax_id
                )

            return success

        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError(
                f"Authentication failed: {str(e)}",
                tax_id=self.tax_id
            )

    def _obtain_rcv_cookies(self) -> List[Dict]:
        """
        Navega al portal RCV para obtener cookies necesarias para la API de DTEs

        Returns:
            Lista de cookies del portal RCV
        """
        try:
            import time
            RCV_PORTAL_URL = "https://www4.sii.cl/consdcvinternetui/#/index"

            logger.debug(f"🌐 Navigating to RCV portal to obtain API cookies...")
            self.driver.navigate_to(RCV_PORTAL_URL)

            # Esperar que cargue y se establezcan las cookies
            time.sleep(3)

            rcv_cookies = self.driver.get_cookies()
            logger.debug(f"✅ RCV cookies obtained: {len(rcv_cookies)} cookies")

            return rcv_cookies

        except Exception as e:
            logger.warning(f"⚠️ Could not obtain RCV cookies: {e}. API calls may fail.")
            return []

    def _merge_cookies(self, cookies1: List[Dict], cookies2: List[Dict]) -> List[Dict]:
        """
        Combina dos listas de cookies, eliminando duplicados por nombre

        Args:
            cookies1: Primera lista de cookies (tiene prioridad)
            cookies2: Segunda lista de cookies

        Returns:
            Lista combinada de cookies sin duplicados
        """
        # Crear un dict con cookies1 como base
        merged = {c['name']: c for c in cookies1}

        # Agregar cookies2 que no estén ya en merged
        for cookie in cookies2:
            if cookie['name'] not in merged:
                merged[cookie['name']] = cookie

        logger.debug(f"🔀 Merging: {len(cookies1)} + {len(cookies2)} = {len(merged)} unique cookies")
        return list(merged.values())

    def get_cookies(self) -> List[Dict]:
        """
        Obtiene cookies frescas (fuerza nueva autenticación)

        Returns:
            Lista de cookies

        Raises:
            AuthenticationError: Si falla la obtención de cookies
        """
        try:
            logger.info("🍪 Getting fresh cookies...")
            cookies = self._v2_handler.get_fresh_cookies()

            if not cookies:
                raise AuthenticationError(
                    "No cookies obtained",
                    tax_id=self.tax_id
                )

            logger.info(f"✅ Got {len(cookies)} fresh cookies")
            return cookies

        except Exception as e:
            logger.error(f"❌ Error getting cookies: {e}")
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError(
                f"Failed to get cookies: {str(e)}",
                tax_id=self.tax_id
            )

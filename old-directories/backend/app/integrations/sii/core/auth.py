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
                # Las cookies ya fueron guardadas por el v2_handler durante el login
                # No necesitamos hacer nada más aquí
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

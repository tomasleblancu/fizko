"""
Clase base del cliente SII con funcionalidades core
"""
import logging
from typing import Dict, Any, List, Optional

from ..core import SeleniumDriver, Authenticator, SessionManager
from ..extractors import ContribuyenteExtractor, F29Extractor, DTEExtractor
from ..config import config as default_config
from ..exceptions import AuthenticationError, ExtractionError

logger = logging.getLogger(__name__)


class SIIClientBase:
    """
    Clase base del cliente SII con funcionalidades core:
    - Inicialización y ciclo de vida
    - Autenticación y gestión de cookies
    - Context manager
    """

    def __init__(
        self,
        tax_id: str,
        password: str,
        headless: bool = True,
        config: Optional[Dict] = None,
        cookies: Optional[List[Dict]] = None
    ):
        """
        Inicializa el cliente SII

        Args:
            tax_id: RUT del contribuyente (formato: 12345678-9)
            password: Contraseña del SII
            headless: Ejecutar navegador en modo headless
            config: Configuración opcional (dict con timeout, window_size, etc)
            cookies: Cookies de sesión existentes (opcional). Si se proveen, se intentará
                    usarlas sin hacer login. Si no funcionan, se hará login automáticamente.
        """
        self.tax_id = tax_id
        self.password = password
        self.headless = headless
        self.custom_config = config or {}
        self.custom_config['headless'] = headless

        # Cookies iniciales (pueden venir de fuera)
        self._initial_cookies = cookies

        # Componentes core (lazy initialization)
        self._driver: Optional[SeleniumDriver] = None
        self._session_manager: Optional[SessionManager] = None
        self._authenticator: Optional[Authenticator] = None

        # Extractores (lazy initialization)
        self._contribuyente_extractor: Optional[ContribuyenteExtractor] = None
        self._f29_extractor: Optional[F29Extractor] = None
        self._dte_extractor: Optional[DTEExtractor] = None

        # Estado
        self._initialized = False
        self._authenticated = False
        self._current_cookies: Optional[List[Dict]] = cookies  # Cookies actuales en memoria

        logger.debug(f"🚀 SIIClient initialized for {tax_id}")
        if cookies:
            logger.debug(f"🍪 Initialized with {len(cookies)} cookies")

    # ==========================================
    # INICIALIZACIÓN Y RECURSOS
    # ==========================================

    def _ensure_initialized(self):
        """Asegura que el cliente esté inicializado"""
        if not self._initialized:
            self._initialize()

    def _initialize(self):
        """Inicializa los componentes core"""
        if self._initialized:
            return

        logger.debug("🔧 Initializing SIIClient components...")

        # Inicializar driver
        self._driver = SeleniumDriver(custom_config=self.custom_config)
        self._driver.start()

        # Inicializar session manager con cookies iniciales si existen
        self._session_manager = SessionManager(
            tax_id=self.tax_id,
            cookies=self._initial_cookies
        )

        # Inicializar authenticator
        self._authenticator = Authenticator(
            driver=self._driver,
            session_manager=self._session_manager,
            tax_id=self.tax_id,
            password=self.password
        )

        self._initialized = True
        logger.debug("✅ SIIClient components initialized")

    def close(self) -> None:
        """Cierra el cliente y libera recursos"""
        logger.debug("🔴 Closing SIIClient...")

        # Cerrar extractores
        if self._dte_extractor:
            self._dte_extractor.close()

        # Cerrar driver
        if self._driver:
            self._driver.quit()

        # Limpiar referencias
        self._driver = None
        self._session_manager = None
        self._authenticator = None
        self._contribuyente_extractor = None
        self._f29_extractor = None
        self._dte_extractor = None

        self._initialized = False
        self._authenticated = False

        logger.debug("✅ SIIClient closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    # ==========================================
    # AUTENTICACIÓN Y COOKIES
    # ==========================================

    def login(self, force_new: bool = False) -> bool:
        """
        Realiza autenticación en el SII

        Args:
            force_new: Forzar nuevo login aunque ya esté autenticado

        Returns:
            True si autenticación fue exitosa

        Raises:
            AuthenticationError: Si falla la autenticación
        """
        self._ensure_initialized()

        # Si forzamos nuevo login, resetear flag de autenticado
        if force_new:
            logger.info(f"🔄 Forcing new authentication for {self.tax_id}...")
            self._authenticated = False

        if self._authenticated and not force_new:
            logger.debug("✅ Already authenticated, skipping login")
            return True

        logger.info(f"🔐 Authenticating {self.tax_id}...")

        # IMPORTANTE: Pasar force_new al authenticator
        success = self._authenticator.authenticate(force_new=force_new)

        if success:
            self._authenticated = True
            # Actualizar cookies actuales desde el session manager
            self._current_cookies = self._session_manager.get_cookies()
            logger.info("✅ Authentication successful")
        else:
            raise AuthenticationError("Authentication failed")

        return success

    def get_cookies(self) -> List[Dict]:
        """
        Obtiene las cookies actuales de la sesión

        Si hay cookies guardadas en memoria, las retorna.
        Si no, hace login si es necesario y retorna las cookies.

        Returns:
            Lista de cookies en formato dict
        """
        self._ensure_initialized()

        # Si ya tenemos cookies en memoria, retornarlas
        if self._current_cookies:
            return self._current_cookies

        # Si no hay cookies, hacer login y obtenerlas
        if not self._authenticated:
            self.login()

        # Obtener cookies del session manager
        cookies = self._session_manager.get_cookies()
        self._current_cookies = cookies

        return cookies

    def is_authenticated(self) -> bool:
        """
        Verifica si el cliente está autenticado

        Returns:
            True si está autenticado
        """
        return self._authenticated

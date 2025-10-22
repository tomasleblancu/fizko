"""
Cliente unificado para interacción con el SII - RPA v3
"""
import logging
from typing import Dict, Any, List, Optional

from .core import SeleniumDriver, Authenticator, SessionManager
from .extractors import ContribuyenteExtractor, F29Extractor, DTEExtractor
from .config import config as default_config
from .exceptions import AuthenticationError, ExtractionError

logger = logging.getLogger(__name__)


class SIIClient:
    """
    Cliente unificado para todas las operaciones del SII.

    Funcionalidades:
    1. Autenticación y gestión de cookies (100% en memoria, sin DB)
    2. Extracción de datos del contribuyente
    3. Extracción de DTEs (compra/venta) vía API
    4. Extracción de formularios F29

    Ejemplo básico (sin cookies previas):
        with SIIClient(tax_id="12345678-9", password="secret") as client:
            # Hacer login y obtener cookies
            client.login()
            cookies = client.get_cookies()  # Guardar cookies para reutilizar

            # Extraer datos
            info = client.get_contribuyente()
            compras = client.get_compras(periodo="202501")

    Ejemplo con cookies existentes (sin login/RPA):
        # Reutilizar cookies de una sesión anterior
        with SIIClient(tax_id="12345678-9", password="secret", cookies=saved_cookies) as client:
            # No necesita login, usa las cookies provistas
            info = client.get_contribuyente()  # Usa cookies directamente
            compras = client.get_compras(periodo="202501")  # Sin abrir navegador
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
    # 1. AUTENTICACIÓN Y COOKIES
    # ==========================================

    def login(self, force_new: bool = False) -> bool:
        """
        Autentica con el SII

        Args:
            force_new: Forzar nueva autenticación (ignorar cookies guardadas)

        Returns:
            True si autenticación exitosa

        Raises:
            AuthenticationError: Si falla la autenticación
        """
        self._ensure_initialized()

        logger.info(f"🔐 Login (force_new={force_new})...")
        self._authenticated = self._authenticator.authenticate(force_new=force_new)

        # Actualizar cookies en memoria después de login exitoso
        if self._authenticated:
            self._current_cookies = self._driver.get_cookies()
            logger.debug(f"🍪 Cached {len(self._current_cookies)} cookies after login")

        return self._authenticated

    def get_cookies(self) -> List[Dict]:
        """
        Obtiene las cookies de sesión actuales

        Estrategia:
        1. Si hay cookies en memoria (_current_cookies), las devuelve
        2. Si no hay cookies y está autenticado, las obtiene del driver
        3. Si no está autenticado, hace login y devuelve las cookies

        Returns:
            Lista de cookies en formato dict

        Raises:
            AuthenticationError: Si no hay sesión autenticada
        """
        # Si ya tenemos cookies en memoria, devolverlas
        if self._current_cookies:
            logger.debug(f"🍪 Returning {len(self._current_cookies)} cookies from memory")
            return self._current_cookies

        self._ensure_initialized()

        # Si no está autenticado, hacer login
        if not self._authenticated:
            logger.debug("🔐 No active session, authenticating...")
            self.login()

        # Obtener cookies del driver y guardarlas en memoria
        cookies = self._driver.get_cookies()
        self._current_cookies = cookies
        logger.debug(f"🍪 Retrieved and cached {len(cookies)} cookies")
        return cookies

    def is_authenticated(self) -> bool:
        """
        Verifica si hay una sesión autenticada activa

        Returns:
            True si hay sesión activa
        """
        if self._authenticated:
            return True

        if self._session_manager:
            return self._session_manager.has_valid_session()

        return False

    # ==========================================
    # 2. DATOS DEL CONTRIBUYENTE
    # ==========================================

    def get_contribuyente(self) -> Dict[str, Any]:
        """
        Obtiene información completa del contribuyente

        Estrategia:
        1. Si el cliente se inicializó con cookies, las usa directamente (sin RPA)
        2. Si no hay cookies o fallan, hace login con RPA
        3. Extrae datos via API usando las cookies

        Returns:
            Dict con:
            - rut: str
            - razon_social: str
            - nombre: str
            - direccion: str
            - comuna: str
            - email: str
            - telefono: str
            - actividad_economica: str
            - fecha_inicio_actividades: str

        Raises:
            ExtractionError: Si falla la extracción
        """
        self._ensure_initialized()

        # Lazy loading del extractor
        if not self._contribuyente_extractor:
            self._contribuyente_extractor = ContribuyenteExtractor(self._driver)

        # PASO 1: Intentar con cookies en memoria (sin RPA)
        if self._current_cookies:
            logger.debug("🍪 Using provided cookies for contribuyente extraction (no RPA needed)")
            try:
                # Intentar extraer con cookies provistas
                return self._contribuyente_extractor.extract(
                    tax_id=self.tax_id,
                    cookies=self._current_cookies
                )
            except Exception as e:
                logger.warning(f"⚠️ Provided cookies failed: {e}. Will retry with fresh login.")
                # Si falla, continuar con login

        # PASO 2: Si no hay cookies válidas o fallaron, hacer login con RPA
        logger.debug("🔐 No valid cookies - performing RPA login")
        if not self._authenticated:
            self.login()

        # Extraer con cookies frescas del driver
        return self._contribuyente_extractor.extract(self.tax_id)

    # ==========================================
    # 3. DOCUMENTOS TRIBUTARIOS (API)
    # ==========================================

    def get_compras(
        self,
        periodo: str,
        tipo_doc: str = "33"
    ) -> Dict[str, Any]:
        """
        Obtiene documentos de compra vía API del SII

        Args:
            periodo: Período tributario (formato YYYYMM, ej: "202501")
            tipo_doc: Código tipo documento (default "33" = factura electrónica)

        Returns:
            Dict con:
            - status: 'success' | 'error'
            - data: List[Dict] con documentos
            - extraction_method: str
            - periodo_tributario: str

        Raises:
            ExtractionError: Si falla la extracción
        """
        # Lazy loading del extractor DTE
        if not self._dte_extractor:
            self._dte_extractor = DTEExtractor(tax_id=self.tax_id)

        # Obtener cookies (hacer login si es necesario)
        cookies = self.get_cookies()

        return self._dte_extractor.extract_compras(periodo, tipo_doc, cookies)

    def get_ventas(
        self,
        periodo: str,
        tipo_doc: str = "33"
    ) -> Dict[str, Any]:
        """
        Obtiene documentos de venta vía API del SII

        Args:
            periodo: Período tributario (formato YYYYMM)
            tipo_doc: Código tipo documento

        Returns:
            Dict con documentos de venta

        Raises:
            ExtractionError: Si falla la extracción
        """
        # Lazy loading del extractor DTE
        if not self._dte_extractor:
            self._dte_extractor = DTEExtractor(tax_id=self.tax_id)

        # Obtener cookies (hacer login si es necesario)
        cookies = self.get_cookies()

        return self._dte_extractor.extract_ventas(periodo, tipo_doc, cookies)

    def get_resumen(self, periodo: str) -> Dict[str, Any]:
        """
        Obtiene resumen de compras y ventas del período

        Args:
            periodo: Período tributario (YYYYMM)

        Returns:
            Dict con totales por tipo de documento

        Raises:
            ExtractionError: Si falla la extracción
        """
        # Lazy loading del extractor DTE
        if not self._dte_extractor:
            self._dte_extractor = DTEExtractor(tax_id=self.tax_id)

        # Obtener cookies (hacer login si es necesario)
        cookies = self.get_cookies()

        return self._dte_extractor.extract_resumen(periodo, cookies)

    # ==========================================
    # 4. FORMULARIOS F29
    # ==========================================

    def get_f29_lista(
        self,
        anio: str,
        folio: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca formularios F29

        Args:
            anio: Año (formato YYYY, ej: "2024")
            folio: Folio específico (opcional)

        Returns:
            Lista de formularios F29 encontrados

        Raises:
            ExtractionError: Si falla la búsqueda
        """
        self._ensure_initialized()

        # Asegurar autenticación FRESCA para F29
        # F29 requiere login directo, no funciona con sesiones reutilizadas
        logger.info("🔐 F29 requires fresh authentication...")
        self.login(force_new=True)

        # Lazy loading del extractor
        if not self._f29_extractor:
            self._f29_extractor = F29Extractor(self._driver, self.tax_id)

        return self._f29_extractor.search(anio, folio)

    def get_f29_compacto(
        self,
        folio: str,
        id_interno_sii: str
    ) -> Optional[bytes]:
        """
        Descarga el PDF del formulario F29 compacto

        Args:
            folio: Folio del formulario
            id_interno_sii: ID interno del SII (obtenido de get_f29_lista)

        Returns:
            PDF en bytes, o None si falla

        Example:
            >>> formularios = client.get_f29_lista("2024")
            >>> f29 = formularios[0]
            >>> pdf = client.get_f29_compacto(f29['folio'], f29['id_interno_sii'])
            >>> with open('f29.pdf', 'wb') as f:
            ...     f.write(pdf)

        Raises:
            ExtractionError: Si falla la descarga
        """
        # Lazy loading del extractor
        if not self._f29_extractor:
            self._f29_extractor = F29Extractor(self._driver, self.tax_id)

        return self._f29_extractor.get_formulario_compacto(
            folio=folio,
            id_interno_sii=id_interno_sii
        )

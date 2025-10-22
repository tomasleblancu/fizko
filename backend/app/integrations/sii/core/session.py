"""
Gestión simplificada de sesiones - Solo memoria (sin DB)
"""
from typing import Optional, List, Dict
import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Gestión simplificada de sesiones y cookies en memoria.

    No requiere base de datos. Las cookies se mantienen solo durante
    la vida del objeto.
    """

    def __init__(self, tax_id: str, cookies: Optional[List[Dict]] = None):
        """
        Inicializa el gestor de sesiones

        Args:
            tax_id: RUT del contribuyente (formato: 12345678-9 o 12345678k)
            cookies: Cookies iniciales opcionales
        """
        self.tax_id = tax_id

        # Extraer RUT y DV (soporta formato con o sin guión)
        if '-' in tax_id:
            parts = tax_id.split('-')
            self.rut = parts[0]
            self.dv = parts[1]
        else:
            # Formato sin guión: 12345678k
            self.rut = tax_id[:-1]
            self.dv = tax_id[-1]

        # Almacenamiento en memoria
        self._cookies: Optional[List[Dict]] = cookies
        self._headers: Optional[Dict] = None
        self._session_id: Optional[str] = str(uuid.uuid4())
        self._expires_at: Optional[datetime] = None

        # Si se proveen cookies iniciales, establecer tiempo de expiración
        if cookies:
            self._expires_at = datetime.now() + timedelta(hours=2)

        logger.debug(f"📋 SessionManager initialized for {tax_id} (memory-only mode)")
        if cookies:
            logger.debug(f"🍪 Initialized with {len(cookies)} cookies")

    def get_active_cookies(self) -> Optional[List[Dict]]:
        """
        Obtiene cookies de una sesión activa válida

        Returns:
            Lista de cookies o None si no hay sesión válida
        """
        # Verificar si hay cookies en memoria y no han expirado
        if self._cookies and self._expires_at:
            if datetime.now() < self._expires_at:
                logger.debug(f"🍪 Found active session with {len(self._cookies)} cookies")
                return self._cookies
            else:
                logger.debug("⏰ Session expired")
                self._cookies = None

        logger.debug("🔍 No valid active session found")
        return None

    def get_cookies(self) -> Optional[List[Dict]]:
        """
        Alias de get_active_cookies() para compatibilidad con v2

        Returns:
            Lista de cookies o None si no hay sesión válida
        """
        return self.get_active_cookies()

    def save_session(
        self,
        cookies: List[Dict],
        headers: Dict = None,
        session_id: str = None,
        username: str = None,  # Compatibilidad con v2
        **kwargs  # Ignorar otros argumentos
    ):
        """
        Guarda sesión completa (compatibilidad con v2)

        Args:
            cookies: Lista de cookies
            headers: Headers HTTP (opcional)
            session_id: ID de sesión (opcional)
            username: Usuario (ignorado, solo para compatibilidad v2)

        Returns:
            None (ya que no usa DB)
        """
        if not cookies:
            logger.warning("⚠️ No cookies to save")
            return None

        # Guardar en memoria
        self._cookies = cookies
        self._headers = headers
        self._session_id = session_id or str(uuid.uuid4())
        self._expires_at = datetime.now() + timedelta(hours=8)

        logger.debug(f"✅ Session saved in memory: {len(cookies)} cookies, expires in 8h")
        return None

    def save_cookies(self, cookies: List[Dict], session_id: str = None):
        """
        Guarda cookies (wrapper de save_session)

        Args:
            cookies: Lista de cookies
            session_id: ID de sesión (opcional)

        Returns:
            None
        """
        return self.save_session(cookies, session_id=session_id)

    def invalidate(self) -> int:
        """
        Invalida la sesión en memoria

        Returns:
            Número de sesiones invalidadas (0 o 1)
        """
        if self._cookies:
            self._cookies = None
            self._headers = None
            self._session_id = None
            self._expires_at = None
            logger.debug(f"🗑️ Invalidated memory session for {self.tax_id}")
            return 1

        return 0

    def has_valid_session(self) -> bool:
        """
        Verifica si existe una sesión válida activa

        Returns:
            True si hay sesión válida
        """
        return self.get_active_cookies() is not None

    def get_headers(self) -> Optional[Dict]:
        """
        Obtiene headers de la sesión activa (compatibilidad con v2)

        Returns:
            Dict con headers o None
        """
        return self._headers

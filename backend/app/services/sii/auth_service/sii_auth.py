"""
Módulo de autenticación con el SII
"""
import logging
from typing import Dict, Any

from app.integrations.sii import SIIClient
from app.integrations.sii.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


async def authenticate_sii(rut: str, password: str) -> Dict[str, Any]:
    """
    Autentica con el SII y extrae información del contribuyente

    Args:
        rut: RUT del contribuyente
        password: Contraseña del SII

    Returns:
        Dict con:
        {
            "contribuyente_info": dict,  # Datos del contribuyente
            "cookies": list              # Cookies de sesión SII
        }

    Raises:
        AuthenticationError: Si falla la autenticación
        ExtractionError: Si falla la extracción de datos
    """
    # Usar context manager para manejar recursos de Selenium
    with SIIClient(
        tax_id=rut,
        password=password,
        headless=True
    ) as sii_client:

        # Intentar login
        login_success = sii_client.login()

        if not login_success:
            raise AuthenticationError(
                "Error en la autenticación. Credenciales incorrectas o SII no disponible."
            )

        # Extraer información del contribuyente
        contribuyente_info = sii_client.get_contribuyente()

        # Obtener cookies para guardar en session
        sii_cookies = sii_client.get_cookies()

        return {
            "contribuyente_info": contribuyente_info,
            "cookies": sii_cookies
        }

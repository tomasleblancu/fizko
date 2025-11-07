"""
Módulo de autenticación con el SII
"""
import logging
from typing import Dict, Any, List

from app.integrations.sii import SIIClient
from app.integrations.sii.exceptions import AuthenticationError, ExtractionError
from app.integrations.sii.extractors import ContribuyenteExtractor

logger = logging.getLogger(__name__)


async def authenticate_sii(rut: str, password: str) -> Dict[str, Any]:
    """
    Autentica con el SII y obtiene cookies (OPTIMIZADO - sin extracción de datos)

    Este método solo hace login y obtiene cookies. La extracción de datos del
    contribuyente se hace después con extract_contribuyente_info() usando las
    cookies guardadas, sin necesidad de mantener Selenium abierto.

    Args:
        rut: RUT del contribuyente
        password: Contraseña del SII

    Returns:
        Dict con:
        {
            "cookies": list  # Cookies de sesión SII
        }

    Raises:
        AuthenticationError: Si falla la autenticación

    Performance:
        - Selenium abierto: 5-7 segundos
        - vs anterior: 10-13 segundos (incluía extracción)
    """
    logger.info(f"🔐 Starting optimized SII authentication for {rut}...")

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

        # Obtener cookies para guardar en session
        sii_cookies = sii_client.get_cookies()

        logger.info(f"✅ Authentication successful. Got {len(sii_cookies)} cookies. Selenium closing...")

        return {
            "cookies": sii_cookies
        }
    # ← Selenium se cierra aquí automáticamente


async def extract_contribuyente_info(rut: str, cookies: List[Dict]) -> Dict[str, Any]:
    """
    Extrae información del contribuyente usando cookies (sin Selenium/RPA)

    Este método usa las cookies obtenidas en authenticate_sii() para hacer
    requests HTTP directos a la API del SII, sin necesidad de abrir Selenium.

    Args:
        rut: RUT del contribuyente
        cookies: Cookies de sesión SII obtenidas en authenticate_sii()

    Returns:
        Dict con información del contribuyente:
        {
            'rut': str,
            'razon_social': str,
            'nombre': str,
            'direccion': str,
            'comuna': str,
            'email': str,
            'telefono': str,
            'actividad_economica': str,
            'fecha_inicio_actividades': str,
            ... (ver ContribuyenteExtractor para estructura completa)
        }

    Raises:
        ExtractionError: Si falla la extracción

    Performance:
        - Sin Selenium: 2-3 segundos (solo HTTP requests)
        - No bloquea otros logins simultáneos
    """
    logger.info(f"📊 Extracting contribuyente info for {rut} using saved cookies...")

    try:
        # Crear extractor sin driver (solo usa cookies)
        extractor = ContribuyenteExtractor(driver=None)

        # Extraer usando cookies directamente
        contribuyente_info = extractor.extract(
            tax_id=rut,
            cookies=cookies
        )

        logger.info(f"✅ Contribuyente info extracted: {contribuyente_info.get('razon_social', 'N/A')}")
        return contribuyente_info

    except Exception as e:
        logger.error(f"❌ Error extracting contribuyente: {e}")
        if isinstance(e, ExtractionError):
            raise
        raise ExtractionError(
            f"Failed to extract contribuyente: {str(e)}",
            resource='contribuyente'
        )

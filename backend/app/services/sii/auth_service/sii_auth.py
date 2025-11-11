"""
Módulo de autenticación con el SII
"""
import logging
from typing import Dict, Any, List

from app.integrations.sii import SIIClient
from app.integrations.sii.exceptions import AuthenticationError, ExtractionError
from app.integrations.sii.extractors import ContribuyenteExtractor

logger = logging.getLogger(__name__)


async def authenticate_and_extract_sii(rut: str, password: str, cookies: List[Dict] = None) -> Dict[str, Any]:
    """
    Autentica con el SII (si es necesario) y extrae información del contribuyente

    Este método usa SIIClient para mantener el contexto de Selenium durante toda
    la operación, lo cual permite que las cookies funcionen correctamente tanto
    para login como para extracción.

    Args:
        rut: RUT del contribuyente
        password: Contraseña del SII
        cookies: Cookies existentes (opcional). Si se proveen, intenta usarlas primero.
                Si fallan o no existen, hace login completo.

    Returns:
        Dict con:
        {
            "cookies": list,  # Cookies de sesión SII (actualizadas)
            "contribuyente_info": dict,  # Información del contribuyente
            "session_refreshed": bool  # True si se hizo re-login
        }

    Raises:
        AuthenticationError: Si falla la autenticación
        ExtractionError: Si falla la extracción

    Performance:
        - Con cookies válidas: 3-4 segundos (verify + extract)
        - Sin cookies o expiradas: 7-9 segundos (login + extract)
    """
    logger.info(f"🔐 Starting SII authentication and extraction for {rut}...")

    # Función sincrónica que ejecuta todo dentro del contexto de SIIClient
    def _authenticate_and_extract():
        with SIIClient(
            tax_id=rut,
            password=password,
            headless=True,
            cookies=cookies  # Pasar cookies si existen
        ) as sii_client:

            session_refreshed = False

            # Si hay cookies, verificar sesión
            if cookies:
                logger.info(f"🔍 Verifying existing session for {rut}...")
                try:
                    verification_result = sii_client.verify_session()
                    session_refreshed = verification_result['refreshed']

                    if session_refreshed:
                        logger.info(f"🔄 Session was refreshed (cookies expired, re-login done)")
                    else:
                        logger.info(f"✅ Existing session is still valid")

                except Exception as e:
                    logger.warning(f"⚠️ Session verification failed: {e}. Doing fresh login...")
                    sii_client.login(force_new=True)
                    session_refreshed = True
            else:
                # Sin cookies, hacer login completo
                logger.info(f"🔐 No cookies provided, performing fresh login...")
                sii_client.login()
                session_refreshed = True

            # Log de cookies antes de extraer contribuyente
            current_cookies = sii_client.get_cookies()
            cookie_names = [c.get('name') for c in current_cookies]
            logger.info(f"🔍 [Auth] Before get_contribuyente: {len(current_cookies)} cookies available: {cookie_names}")

            # Extraer información del contribuyente
            # Esto funciona porque estamos dentro del contexto de Selenium
            contribuyente_info = sii_client.get_contribuyente()

            # Obtener cookies actualizadas
            updated_cookies = sii_client.get_cookies()
            updated_cookie_names = [c.get('name') for c in updated_cookies]
            logger.info(f"✅ [Auth] After get_contribuyente: {len(updated_cookies)} cookies: {updated_cookie_names}")

            return {
                "cookies": updated_cookies,
                "contribuyente_info": contribuyente_info,
                "session_refreshed": session_refreshed
            }

    try:
        # Ejecutar en thread separado para no bloquear el event loop
        import asyncio
        result = await asyncio.to_thread(_authenticate_and_extract)

        logger.info(f"✅ Contribuyente info extracted: {result['contribuyente_info'].get('razon_social', 'N/A')}")
        return result

    except Exception as e:
        logger.error(f"❌ Error in authentication/extraction: {e}")
        if isinstance(e, (AuthenticationError, ExtractionError)):
            raise
        raise AuthenticationError(f"Failed to authenticate or extract: {str(e)}")

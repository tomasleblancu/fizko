"""
Validation logic for F29 scraper

Handles session validation and parameter validation.
"""
import logging
from typing import Optional
from selenium.common.exceptions import (
    InvalidSessionIdException,
    WebDriverException
)

logger = logging.getLogger(__name__)


def check_session_valid(driver) -> bool:
    """
    Verifica si la sesión de Selenium sigue activa

    Args:
        driver: WebDriver instance

    Returns:
        True si la sesión está activa, False si no
    """
    try:
        _ = driver.driver.current_url
        _ = driver.driver.window_handles
        return True
    except (InvalidSessionIdException, WebDriverException) as e:
        logger.warning(f"⚠️ Sesión de Selenium inválida detectada: {type(e).__name__}")
        return False
    except Exception as e:
        logger.warning(f"⚠️ Error verificando sesión: {type(e).__name__}: {e}")
        return False


def validar_parametros(anio: Optional[str], folio: Optional[str]) -> None:
    """
    Valida que los parametros de busqueda sean correctos

    Args:
        anio: Año a consultar (YYYY)
        folio: Folio específico

    Raises:
        ValueError: Si los parametros no son validos
    """
    if not folio and not anio:
        raise ValueError("Debe especificar ano o folio para buscar")

    if anio and (not anio.isdigit() or len(anio) != 4):
        raise ValueError("El ano debe ser un numero de 4 digitos")

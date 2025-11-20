"""
Utilidades para validar PDFs de F29
"""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def is_valid_f29_pdf(pdf_bytes: bytes) -> Tuple[bool, str]:
    """
    Valida que el PDF sea un F29 válido y no contenga errores del SII

    Args:
        pdf_bytes: Contenido del PDF en bytes

    Returns:
        Tupla (is_valid, reason)
        - is_valid: True si el PDF es válido
        - reason: Mensaje explicando por qué es válido/inválido

    Example:
        >>> is_valid, reason = is_valid_f29_pdf(pdf_content)
        >>> if not is_valid:
        ...     print(f"PDF inválido: {reason}")
    """
    # 1. Verificar que empiece con header PDF
    if not pdf_bytes.startswith(b'%PDF'):
        return False, "File does not start with PDF header"

    # 2. Verificar tamaño mínimo (un PDF vacío/error suele ser muy pequeño)
    if len(pdf_bytes) < 1000:  # Menos de 1KB
        return False, f"PDF too small ({len(pdf_bytes)} bytes), likely an error page"

    # 3. Buscar mensajes de error comunes del SII
    error_phrases = [
        b"Ha ocurrido un error",
        b"error al imprimir",
        b"No se pudo generar",
        b"Servicio no disponible",
        b"Error en el sistema",
        b"Intente nuevamente"
    ]

    pdf_lower = pdf_bytes.lower()
    for error_phrase in error_phrases:
        if error_phrase.lower() in pdf_lower:
            error_msg = error_phrase.decode('utf-8', errors='ignore')
            return False, f"PDF contains error message: '{error_msg}'"

    # 4. Verificar que contenga texto relacionado con F29
    # Los PDFs de F29 suelen contener estos términos
    f29_indicators = [
        b"FORMULARIO 29",
        b"Formulario 29",
        b"F29",
        b"DECLARACION MENSUAL",
        b"IVA"
    ]

    has_f29_indicator = any(indicator in pdf_bytes for indicator in f29_indicators)

    if not has_f29_indicator:
        logger.warning("PDF doesn't contain F29 indicators, but may still be valid")
        # No forzamos que falle, pero advertimos
        return True, "PDF appears valid but doesn't contain typical F29 markers"

    # 5. Todo bien
    return True, "PDF appears to be a valid F29"


def get_pdf_size_mb(pdf_bytes: bytes) -> float:
    """
    Obtiene el tamaño del PDF en megabytes

    Args:
        pdf_bytes: Contenido del PDF en bytes

    Returns:
        Tamaño en MB
    """
    return len(pdf_bytes) / (1024 * 1024)

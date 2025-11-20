"""
RPA v3 - Cliente simplificado para el SII

Cliente unificado y minimalista para interacción con el portal del SII de Chile.

Características:
- ✅ Autenticación automática con gestión de sesiones
- ✅ Extracción de datos del contribuyente
- ✅ Documentos tributarios (DTEs) vía API con cookies
- ✅ Formularios F29 completos
- ✅ API única y simple - una sola clase
- ✅ Context manager para gestión automática de recursos

Uso básico:
    from apps.sii.rpa_v3 import SIIClient

    with SIIClient(tax_id="12345678-9", password="secret") as client:
        # Datos del contribuyente
        info = client.get_contribuyente()

        # DTEs de compra/venta
        compras = client.get_compras(periodo="202501")
        ventas = client.get_ventas(periodo="202501")

        # Formularios F29
        formularios = client.get_f29_lista(anio="2024")
        detalle = client.get_f29_detalle(folio="123456")
"""

from .client import SIIClient
from .exceptions import (
    RPAException,
    AuthenticationError,
    ExtractionError,
    SessionError,
    ValidationError,
)

__all__ = [
    'SIIClient',
    'RPAException',
    'AuthenticationError',
    'ExtractionError',
    'SessionError',
    'ValidationError',
]

__version__ = '3.0.0'

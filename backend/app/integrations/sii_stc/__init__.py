"""
SII STC (Sin Autenticación) Integration

Módulo para consultas públicas del SII sin autenticación:
- Consulta de estado de proveedores
- Validación de documentos tributarios

Este módulo es completamente independiente de la integración SII principal
y NO requiere credenciales de usuario.

Uso:
    from app.integrations.sii_stc import STCClient

    with STCClient() as client:
        result = client.consultar_documento(
            rut="77794858",
            dv="K"
        )
"""

from .client import STCClient
from .client_v2 import STCClientV2

__all__ = ['STCClient', 'STCClientV2']

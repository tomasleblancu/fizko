"""
SII Service - Capa de aplicación para integración con SII

Estructura modular:
- BaseSIIService: Funcionalidad base (credenciales, cookies, sesiones)
- DocumentService: Documentos tributarios (DTEs, compras, ventas, resumen)
- FormService: Formularios (F29, F22, etc.)
- SIIService: Facade que unifica todos los servicios (mantiene compatibilidad)
- SIISyncService: Servicio de sincronización legacy
- SIIAuthService: Servicio de autenticación
"""
from .base_service import BaseSIIService
from .document_service import DocumentService
from .form_service import FormService
from .service import (
    SIIService,
    get_sii_service,
    get_form_service,
    get_document_service
)
from .sync_service import SIISyncService
from .auth_service import SIIAuthService

__all__ = [
    # Base
    "BaseSIIService",

    # Servicios especializados
    "DocumentService",
    "FormService",

    # Facade (compatibilidad)
    "SIIService",
    "get_sii_service",
    "get_form_service",
    "get_document_service",

    # Legacy services
    "SIISyncService",
    "SIIAuthService",
]

"""
Servicio de autenticación SII modularizado

Este servicio maneja el proceso completo de login y setup inicial de empresas.
Está dividido en módulos especializados:

- service: SIIAuthService (orquestador principal)
- sii_auth: Autenticación con el SII y extracción de contribuyente
- setup: Setup de Company, CompanyTaxInfo, Session y Profile
- memories: Gestión de memorias en Mem0
- events: Activación de eventos tributarios y notificaciones
"""

# Export de la clase principal
from .service import SIIAuthService

# Export para mantener compatibilidad con imports existentes
__all__ = ['SIIAuthService']

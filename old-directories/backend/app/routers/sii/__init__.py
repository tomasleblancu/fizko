"""
SII Integration Routers

Este paquete contiene todos los endpoints relacionados con la integración SII.
Organizado por funcionalidad:

- auth.py: Autenticación y setup de sesiones SII
- sync.py: Sincronización de documentos tributarios en background
- forms.py: Consulta de formularios F29 sincronizados
- extractions.py: Endpoints de extracción de datos (DTEs, F29, etc.) [futuro]
- webhooks.py: Webhooks para eventos del SII (futuro)
"""
from fastapi import APIRouter
from app.routers.sii import auth, sync, forms

# Router principal que agrupa todos los sub-routers
router = APIRouter(prefix="/api/sii", tags=["SII"])

# Incluir sub-routers
router.include_router(auth.router)
router.include_router(sync.router)
router.include_router(forms.router)

__all__ = ["router"]

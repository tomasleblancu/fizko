"""
Router principal para sincronización SII

Agrupa todos los routers de sincronización (documentos, F29, etc.)
"""
from fastapi import APIRouter

from .sync_documents import router as documents_router
from .sync_f29 import router as f29_router

router = APIRouter(prefix="/sync", tags=["sii-sync"])

# Incluir sub-routers
router.include_router(documents_router, prefix="")
router.include_router(f29_router, prefix="")

"""Notification management routers (admin and user operations)."""

from fastapi import APIRouter, Depends

from ...dependencies import require_auth
from .templates import router as templates_router
from .whatsapp_sync import router as whatsapp_sync_router
from .subscriptions import router as subscriptions_router
from .user_operations import router as user_operations_router

# Main notifications router
router = APIRouter(
    prefix="/api/notifications",
    tags=["notifications"]
)

# Admin sub-routers (require auth)
admin_router = APIRouter(dependencies=[Depends(require_auth)])
admin_router.include_router(templates_router)
admin_router.include_router(whatsapp_sync_router)
admin_router.include_router(subscriptions_router)

# User-facing sub-routers (use get_user_company_id for scoping)
router.include_router(user_operations_router)
router.include_router(admin_router)

__all__ = ["router"]

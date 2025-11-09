"""Administrative routers."""

from fastapi import APIRouter, Depends

from ...dependencies import require_auth
from . import companies, f29, testing

# Create main admin router
router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_auth)]
)

# Include all sub-routers
router.include_router(companies.router)
router.include_router(f29.router)
router.include_router(testing.router)

__all__ = ["router"]

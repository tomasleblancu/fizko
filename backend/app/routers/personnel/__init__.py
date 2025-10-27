"""Personnel management API routes."""

from fastapi import APIRouter

from .people import router as people_router
from .payroll import router as payroll_router

router = APIRouter(prefix="/api/personnel", tags=["personnel"])

# Include sub-routers
router.include_router(people_router, prefix="/people", tags=["people"])
router.include_router(payroll_router, prefix="/payroll", tags=["payroll"])

__all__ = ["router"]

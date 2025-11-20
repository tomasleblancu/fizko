"""Subscription routers."""

from fastapi import APIRouter

from . import current, plans

# Create main subscription router
router = APIRouter()

# Include sub-routers
router.include_router(plans.router)
router.include_router(current.router)

__all__ = ["router"]

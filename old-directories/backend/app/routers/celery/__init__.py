"""
Celery Task Launch Router

Provides a generic endpoint for launching Celery tasks.
"""
from fastapi import APIRouter

from .launch import router as launch_router

router = APIRouter(prefix="/api/celery", tags=["celery"])

# Include sub-routers
router.include_router(launch_router)

__all__ = ["router"]

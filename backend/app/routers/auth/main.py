"""Main authentication router."""

from fastapi import APIRouter

from . import phone

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
)

# Include phone authentication routes
router.include_router(phone.router)

"""Main authentication router."""

from fastapi import APIRouter

from . import phone

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
)

# Include phone authentication routes
router.include_router(phone.router)

# Note: Profile push token management is handled directly by frontend via Supabase
# No backend endpoint needed since frontend updates profiles.expo_push_token directly

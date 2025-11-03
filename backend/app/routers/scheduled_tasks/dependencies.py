"""Dependencies for scheduled tasks router."""

# Re-export get_user_company_id from main dependencies module for backward compatibility
from app.dependencies import get_user_company_id

__all__ = ["get_user_company_id"]

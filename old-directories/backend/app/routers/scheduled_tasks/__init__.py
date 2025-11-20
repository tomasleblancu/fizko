"""
Scheduled Tasks Router Module.

This module provides API endpoints for managing Celery Beat scheduled tasks.
All endpoints are defined in router.py and imported here for clean organization.
"""
from .router import router

__all__ = ["router"]

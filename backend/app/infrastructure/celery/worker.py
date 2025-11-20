"""
Celery worker entry point for Backend V2.

This module provides the entry point for starting Celery workers.
It ensures proper initialization of the application context and
Supabase client.

Usage:
    # Start worker for all queues:
    celery -A app.infrastructure.celery.worker worker --loglevel=info

    # Start worker for specific queue:
    celery -A app.infrastructure.celery.worker worker -Q high --loglevel=info

    # Start worker with autoreload (development):
    celery -A app.infrastructure.celery.worker worker --loglevel=info --reload

    # Start Flower monitoring (optional):
    celery -A app.infrastructure.celery.worker flower

    # Start Beat scheduler:
    celery -A app.infrastructure.celery.worker beat --loglevel=info

Architecture notes:
    - Tasks use Supabase client via get_supabase_client()
    - All database operations go through repositories
    - No direct SQL queries in task code
"""
from dotenv import load_dotenv

# Load environment variables before importing anything else
load_dotenv()

from app.infrastructure.celery import celery_app

# This allows Celery to find the app when starting workers
__all__ = ["celery_app"]

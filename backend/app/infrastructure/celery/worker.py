"""
Celery worker entry point.

This module provides the entry point for starting Celery workers.
It ensures proper initialization of the application context.

Usage:
    # Start worker for all queues:
    celery -A app.infrastructure.celery.worker worker --loglevel=info

    # Start worker for specific queue:
    celery -A app.infrastructure.celery.worker worker -Q high --loglevel=info

    # Start worker with autoreload (development):
    celery -A app.infrastructure.celery.worker worker --loglevel=info --reload

    # Start Flower monitoring (optional):
    celery -A app.infrastructure.celery.worker flower
"""
from dotenv import load_dotenv

# Load environment variables before importing anything else
load_dotenv()

from app.infrastructure.celery import celery_app

# This allows Celery to find the app when starting workers
__all__ = ["celery_app"]

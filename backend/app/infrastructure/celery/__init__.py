"""
Celery infrastructure for Fizko backend.

This module initializes the Celery app and configures it for use
with FastAPI. Tasks are automatically discovered from the tasks/ directory.

Architectural decision: Celery is infrastructure, not a business integration.
Therefore it lives in app.infrastructure.celery.
"""
from celery import Celery
from . import config

# Create Celery app
celery_app = Celery("fizko")

# Load configuration from config module
celery_app.config_from_object(config)

# Auto-discover tasks from tasks/ directory
# This will import all task modules and register their @celery_app.task decorators
celery_app.autodiscover_tasks(
    [
        "app.infrastructure.celery.tasks.sii",
        "app.infrastructure.celery.tasks.documents",
        "app.infrastructure.celery.tasks.whatsapp",
        "app.infrastructure.celery.tasks.notifications",
        "app.infrastructure.celery.tasks",  # For calendar.py and other root-level tasks
    ],
    force=True,
)

__all__ = ["celery_app"]

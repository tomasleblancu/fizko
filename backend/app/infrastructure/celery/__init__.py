"""
Celery infrastructure for Backend V2.

This module initializes the Celery app and configures it for use
with FastAPI and Supabase client. Tasks are automatically discovered
from the tasks/ directory.

Key differences from original backend:
- Uses Supabase client instead of SQLAlchemy
- All database operations go through repositories
- No direct SQL queries in task code
"""
from celery import Celery
from . import config

# Create Celery app
celery_app = Celery("fizko-v2")

# Load configuration from config module
celery_app.config_from_object(config)

# Auto-discover tasks from tasks/ directory
# This will import all task modules and register their @celery_app.task decorators
celery_app.autodiscover_tasks(
    [
        "app.infrastructure.celery.tasks.sii",
        "app.infrastructure.celery.tasks.calendar",
        "app.infrastructure.celery.tasks",  # For root-level tasks
    ],
    force=True,
)

__all__ = ["celery_app"]

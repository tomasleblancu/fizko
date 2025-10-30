"""
Celery configuration for Fizko backend.

This module contains all Celery-related configuration including
broker settings, result backend, task routing, and worker settings.
"""
import os
from dotenv import load_dotenv
from kombu import Queue

# Load environment variables
load_dotenv()

# Redis configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery broker and result backend
broker_url = REDIS_URL
result_backend = REDIS_URL

# Serialization settings (use JSON for better compatibility)
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "America/Santiago"  # Chile timezone
enable_utc = True

# Task execution settings
task_track_started = True  # Track when tasks start (not just when queued)
task_time_limit = 30 * 60  # Hard time limit: 30 minutes
task_soft_time_limit = 25 * 60  # Soft time limit: 25 minutes
worker_prefetch_multiplier = 1  # Fetch one task at a time (better for long tasks)
worker_max_tasks_per_child = 50  # Restart worker after 50 tasks (prevent memory leaks)

# Retry settings
task_acks_late = True  # Only acknowledge task after completion (safer)
task_reject_on_worker_lost = True  # Re-queue if worker dies

# Result backend settings
result_expires = 3600  # Results expire after 1 hour
result_extended = True  # Store extended task metadata

# Task routing - different queues for different priorities
task_routes = {
    # High priority - Critical operations
    "app.infrastructure.celery.tasks.whatsapp.whatsapp_tasks.*": {"queue": "high"},

    # Default priority - Normal operations
    "app.infrastructure.celery.tasks.documents.document_tasks.*": {"queue": "default"},

    # Low priority - Heavy/slow operations
    "app.infrastructure.celery.tasks.sii.sii_tasks.*": {"queue": "low"},
    "app.infrastructure.celery.tasks.sii.sync_tasks.*": {"queue": "low"},
}

# Define queues with priorities
task_queues = (
    Queue("high", routing_key="high"),
    Queue("default", routing_key="default"),
    Queue("low", routing_key="low"),
)

# Default queue for tasks not explicitly routed
task_default_queue = "default"
task_default_exchange = "tasks"
task_default_routing_key = "default"

# ============================================================================
# CELERY BEAT - Database Scheduler Configuration
# ============================================================================

# Use database scheduler instead of file-based schedule
# This allows dynamic creation/modification/deletion of periodic tasks
beat_scheduler = "sqlalchemy_celery_beat.schedulers:DatabaseScheduler"

# Database URL for beat scheduler (same as main database)
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # SQLAlchemy-celery-beat uses sync connection, convert asyncpg to psycopg2
    beat_dburi = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
else:
    beat_dburi = None

# Beat settings
beat_max_loop_interval = 5  # Check database every 5 seconds for changes
beat_sync_every = 0  # Number of tasks beat executes before syncing (0 = always sync)

# Schema configuration for sqlalchemy-celery-beat
# The library will create tables in this schema automatically
beat_schema = "celery_schema"  # Database schema where Beat tables will be created

# Logging
worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"

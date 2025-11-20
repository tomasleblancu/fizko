#!/bin/bash
# ============================================
# Railway Celery Beat Start Script
# ============================================
# This script is called by Railway to start the Celery Beat scheduler

set -e

echo "========================================"
echo "Starting Celery Beat (Railway)"
echo "========================================"

# Check Redis connection (required for Celery)
echo "→ Waiting for Redis..."
timeout 30 bash -c 'until redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; do sleep 1; done' || \
    { echo "✗ Redis not available"; exit 1; }
echo "✓ Redis is ready"

# Check DATABASE_URL (required for Beat scheduler)
if [ -z "$DATABASE_URL" ]; then
    echo "✗ DATABASE_URL not set (required for Beat scheduler)"
    exit 1
fi
echo "✓ DATABASE_URL is configured"

# Initialize Beat database tables if they don't exist
echo "→ Initializing Beat database tables..."
/app/.venv/bin/python -m app.infrastructure.celery.init_beat_db || \
    echo "⚠ Tables already exist or initialization skipped"

# Start Celery Beat
echo "→ Starting Celery Beat scheduler..."
echo "  • Scheduler: DatabaseScheduler (PostgreSQL)"
echo "  • Log level: ${CELERY_LOG_LEVEL:-info}"

exec /app/.venv/bin/celery -A app.infrastructure.celery.worker beat \
    --loglevel=${CELERY_LOG_LEVEL:-info} \
    --scheduler=sqlalchemy_celery_beat.schedulers:DatabaseScheduler

#!/bin/bash
# ============================================
# Railway Celery Worker Start Script
# ============================================
# This script is called by Railway to start the Celery worker

set -e

echo "========================================"
echo "Starting Celery Worker (Railway)"
echo "========================================"

# Check Redis connection (required for Celery)
echo "→ Waiting for Redis..."
timeout 30 bash -c 'until redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; do sleep 1; done' || \
    { echo "✗ Redis not available"; exit 1; }
echo "✓ Redis is ready"

# Start Celery worker
echo "→ Starting Celery worker..."
echo "  • Concurrency: ${CELERY_CONCURRENCY:-2}"
echo "  • Queues: default, low"
echo "  • Log level: ${CELERY_LOG_LEVEL:-info}"

exec /app/.venv/bin/celery -A app.infrastructure.celery.worker worker \
    --loglevel=${CELERY_LOG_LEVEL:-info} \
    --concurrency=${CELERY_CONCURRENCY:-2} \
    --queues=default,low \
    --max-tasks-per-child=50 \
    --time-limit=1800 \
    --soft-time-limit=1500

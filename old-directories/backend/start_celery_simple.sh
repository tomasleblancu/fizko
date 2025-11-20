#!/bin/bash
# Simple Celery worker start script (no checks)
# Usage: ./start_celery_simple.sh

cd "$(dirname "$0")"

echo "🚀 Starting Celery worker..."
echo "📋 Log level: info | Concurrency: 2 | Pool: solo (development)"
echo ""

.venv/bin/celery -A app.celery_app.worker worker \
    --loglevel=info \
    --concurrency=2 \
    --pool=solo

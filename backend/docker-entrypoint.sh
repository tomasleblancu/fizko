#!/bin/bash
# ============================================
# Docker Entrypoint - Backend V2
# ============================================
# Punto de entrada para Backend V2: FastAPI + Celery

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Backend V2 - Docker Entrypoint${NC}"
echo -e "${BLUE}======================================${NC}"

# ============================================
# Service Commands
# ============================================

case "$1" in
    fastapi)
        echo -e "${GREEN}🚀 Starting FastAPI (Production)${NC}"

        # Check Redis connection (optional, non-blocking)
        if [ ! -z "$REDIS_URL" ]; then
            echo -e "${BLUE}→${NC} Checking Redis connection..."
            timeout 5 redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1 && \
                echo -e "${GREEN}✓${NC} Redis is available" || \
                echo -e "${YELLOW}⚠${NC} Redis not available (Celery tasks will not work)"
        fi

        exec uvicorn app.main:app \
            --host 0.0.0.0 \
            --port ${PORT:-8000} \
            --workers ${WORKERS:-1} \
            --timeout-keep-alive 5 \
            --log-level info
        ;;

    fastapi-dev)
        echo -e "${GREEN}🚀 Starting FastAPI (Development - Hot Reload)${NC}"

        # Check Redis connection (optional, non-blocking)
        if [ ! -z "$REDIS_URL" ]; then
            echo -e "${BLUE}→${NC} Checking Redis connection..."
            timeout 5 redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1 && \
                echo -e "${GREEN}✓${NC} Redis is available" || \
                echo -e "${YELLOW}⚠${NC} Redis not available (Celery tasks will not work)"
        fi

        exec uvicorn app.main:app \
            --host 0.0.0.0 \
            --port ${PORT:-8000} \
            --reload \
            --reload-dir /app/app \
            --log-level debug
        ;;

    celery-worker)
        echo -e "${GREEN}🔧 Starting Celery Worker${NC}"

        # Check Redis connection (required for Celery)
        echo -e "${BLUE}→${NC} Waiting for Redis..."
        timeout 30 bash -c 'until redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; do sleep 1; done' || \
            { echo -e "${RED}✗${NC} Redis not available"; exit 1; }
        echo -e "${GREEN}✓${NC} Redis is ready"

        # Start Celery worker
        # - Concurrency: 2 workers for SII tasks (heavy Selenium)
        # - Queues: default (general) and low (heavy SII tasks)
        # - Loglevel: info (can be overridden with CELERY_LOG_LEVEL)
        exec /app/.venv/bin/celery -A app.infrastructure.celery.worker worker \
            --loglevel=${CELERY_LOG_LEVEL:-info} \
            --concurrency=${CELERY_CONCURRENCY:-2} \
            --queues=default,low \
            --max-tasks-per-child=50 \
            --time-limit=1800 \
            --soft-time-limit=1500
        ;;

    celery-beat)
        echo -e "${GREEN}⏰ Starting Celery Beat Scheduler${NC}"

        # Check Redis connection (required for Celery)
        echo -e "${BLUE}→${NC} Waiting for Redis..."
        timeout 30 bash -c 'until redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; do sleep 1; done' || \
            { echo -e "${RED}✗${NC} Redis not available"; exit 1; }
        echo -e "${GREEN}✓${NC} Redis is ready"

        # Check DATABASE_URL (required for Beat scheduler)
        if [ -z "$DATABASE_URL" ]; then
            echo -e "${RED}✗${NC} DATABASE_URL not set (required for Beat scheduler)"
            exit 1
        fi
        echo -e "${GREEN}✓${NC} DATABASE_URL is configured"

        # Initialize Beat database tables if they don't exist
        echo -e "${BLUE}→${NC} Initializing Beat database tables..."
        /app/.venv/bin/python -m app.infrastructure.celery.init_beat_db || \
            echo -e "${YELLOW}⚠${NC} Tables already exist or initialization skipped"

        # Start Celery Beat
        # - Uses database scheduler (sqlalchemy-celery-beat)
        # - Stores schedules in PostgreSQL
        exec /app/.venv/bin/celery -A app.infrastructure.celery.worker beat \
            --loglevel=${CELERY_LOG_LEVEL:-info} \
            --scheduler=sqlalchemy_celery_beat.schedulers:DatabaseScheduler
        ;;

    test|pytest)
        echo -e "${GREEN}🧪 Running Tests${NC}"
        # Pass all remaining arguments to pytest
        shift  # Remove 'test' or 'pytest' from arguments
        exec python -m pytest "$@"
        ;;

    bash|sh)
        echo -e "${GREEN}🐚 Starting Interactive Shell${NC}"
        exec /bin/bash
        ;;

    *)
        echo -e "${RED}✗${NC} Unknown command: $1"
        echo ""
        echo "Available commands:"
        echo "  fastapi        - Start FastAPI (production)"
        echo "  fastapi-dev    - Start FastAPI (development with hot-reload)"
        echo "  celery-worker  - Start Celery worker (SII tasks)"
        echo "  celery-beat    - Start Celery Beat scheduler (periodic tasks)"
        echo "  test|pytest    - Run tests with pytest"
        echo "  bash           - Interactive shell"
        echo ""
        echo "Examples:"
        echo "  docker run backend-v2 fastapi"
        echo "  docker run backend-v2 fastapi-dev"
        echo "  docker run backend-v2 celery-worker"
        echo "  docker run backend-v2 celery-beat"
        echo "  docker run backend-v2 test tests/ -v"
        echo "  docker run backend-v2 bash"
        exit 1
        ;;
esac

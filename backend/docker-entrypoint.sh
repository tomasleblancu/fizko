#!/bin/bash
# ============================================
# Docker Entrypoint - Fizko Backend
# ============================================
# Punto de entrada flexible para diferentes servicios

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Fizko Backend - Docker Entrypoint${NC}"
echo -e "${BLUE}======================================${NC}"

# ============================================
# Helper Functions
# ============================================

wait_for_service() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}→${NC} Waiting for ${service_name} (${host}:${port})..."

    # Use nc (netcat) for connection check - more reliable in containers
    while ! nc -z -w1 "$host" "$port" 2>/dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            echo -e "${RED}✗${NC} ${service_name} not available after ${max_attempts} attempts"
            echo -e "${YELLOW}ℹ${NC}  Make sure Redis plugin is running in the same Railway project"
            exit 1
        fi
        echo -e "  Attempt ${attempt}/${max_attempts}..."
        attempt=$((attempt + 1))
        sleep 2
    done

    echo -e "${GREEN}✓${NC} ${service_name} is ready!"
}

check_env_vars() {
    local required_vars=("$@")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo -e "${RED}✗${NC} Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo -e "  - ${var}"
        done
        echo -e "${YELLOW}⚠${NC}  Please set these in your .env file"
        exit 1
    fi
}

# ============================================
# Wait for Dependencies
# ============================================

# Wait for Redis (always required)
if [ -n "$REDIS_URL" ]; then
    # Parse Redis URL - supports both formats:
    # redis://host:port/db
    # redis://user:pass@host:port/db
    REDIS_HOST=$(echo "$REDIS_URL" | sed -E 's|redis://([^:]+:[^@]+@)?([^:]+):.*|\2|')
    REDIS_PORT=$(echo "$REDIS_URL" | sed -E 's|redis://.*:([0-9]+).*|\1|')

    wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
fi

# Wait for PostgreSQL (for database operations)
if [ -n "$DATABASE_URL" ]; then
    # Parse DATABASE_URL (postgresql+asyncpg://user:pass@host:port/db)
    DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:]+):.*|\1|')
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')

    wait_for_service "$DB_HOST" "$DB_PORT" "PostgreSQL"
fi

# ============================================
# Service Commands
# ============================================

case "$1" in
    fastapi)
        echo -e "${GREEN}🚀 Starting FastAPI (Production)${NC}"
        check_env_vars "DATABASE_URL" "REDIS_URL" "OPENAI_API_KEY" "SUPABASE_URL"

        exec gunicorn app.main:app \
            --workers 2 \
            --worker-class uvicorn.workers.UvicornWorker \
            --bind 0.0.0.0:${PORT:-8000} \
            --timeout 120 \
            --graceful-timeout 30 \
            --keep-alive 5 \
            --access-logfile - \
            --error-logfile - \
            --log-level info
        ;;

    fastapi-dev)
        echo -e "${GREEN}🚀 Starting FastAPI (Development - Hot Reload)${NC}"
        check_env_vars "DATABASE_URL" "REDIS_URL" "OPENAI_API_KEY" "SUPABASE_URL"

        exec uvicorn app.main:app \
            --host 0.0.0.0 \
            --port ${PORT:-8000} \
            --reload \
            --reload-dir /app/app \
            --log-level debug
        ;;

    celery-worker)
        echo -e "${GREEN}🔨 Starting Celery Worker${NC}"
        check_env_vars "DATABASE_URL" "REDIS_URL"

        exec celery -A app.infrastructure.celery.worker worker \
            --loglevel=${CELERY_LOG_LEVEL:-info} \
            --concurrency=${CELERY_CONCURRENCY:-2} \
            --max-tasks-per-child=${CELERY_MAX_TASKS_PER_CHILD:-1000}
        ;;

    celery-beat)
        echo -e "${GREEN}⏰ Starting Celery Beat Scheduler${NC}"
        check_env_vars "DATABASE_URL" "REDIS_URL"

        exec celery -A app.infrastructure.celery.worker beat \
            --loglevel=${CELERY_LOG_LEVEL:-info} \
            --scheduler=sqlalchemy_celery_beat.schedulers:DatabaseScheduler
        ;;

    flower)
        echo -e "${GREEN}🌸 Starting Flower (Celery Monitoring)${NC}"
        check_env_vars "REDIS_URL"

        exec celery -A app.infrastructure.celery.worker flower \
            --port=5555 \
            --url_prefix=flower
        ;;

    bash|sh)
        echo -e "${GREEN}🐚 Starting Interactive Shell${NC}"
        exec /bin/bash
        ;;

    *)
        echo -e "${RED}✗${NC} Unknown command: $1"
        echo ""
        echo "Available commands:"
        echo "  fastapi        - Start FastAPI (production with Gunicorn)"
        echo "  fastapi-dev    - Start FastAPI (development with hot-reload)"
        echo "  celery-worker  - Start Celery Worker"
        echo "  celery-beat    - Start Celery Beat Scheduler"
        echo "  flower         - Start Flower monitoring"
        echo "  bash           - Interactive shell"
        echo ""
        echo "Example:"
        echo "  docker-compose run backend bash"
        exit 1
        ;;
esac

#!/bin/bash

# ============================================================================
# Celery Beat Scheduler Startup Script
# ============================================================================
#
# This script starts the Celery Beat scheduler, which reads periodic tasks
# from the database and submits them to the worker queue at scheduled times.
#
# The Beat scheduler:
# - Reads from PostgreSQL tables (celery_periodic_task, etc.)
# - Checks for changes every 5 seconds (beat_max_loop_interval)
# - Submits tasks to the appropriate queues (high, default, low)
#
# Requirements:
# - PostgreSQL with Beat tables (run migration 017_celery_beat_scheduler.sql)
# - DATABASE_URL environment variable set
# - Redis running (for task queue)
# - At least one worker running (to execute submitted tasks)
#
# Usage:
#   ./start_beat.sh              # Start Beat scheduler
#   ./start_beat.sh --loglevel=debug  # Start with debug logging
#
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Celery Beat Scheduler Startup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# ============================================================================
# 1. Check Python environment
# ============================================================================
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓${NC} Found .venv directory"
    source .venv/bin/activate
    echo -e "${GREEN}✓${NC} Activated virtual environment"
else
    echo -e "${RED}✗${NC} No .venv directory found"
    echo -e "${YELLOW}⚠${NC}  Please create a virtual environment first:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -e ."
    exit 1
fi

# ============================================================================
# 2. Check .env file
# ============================================================================
if [ ! -f ".env" ]; then
    echo -e "${RED}✗${NC} No .env file found"
    echo -e "${YELLOW}⚠${NC}  Please create a .env file with:"
    echo "   DATABASE_URL=postgresql+asyncpg://..."
    echo "   REDIS_URL=redis://localhost:6379/0"
    exit 1
fi
echo -e "${GREEN}✓${NC} Found .env file"

# Load environment variables
set -a
source .env
set +a

# ============================================================================
# 3. Check DATABASE_URL
# ============================================================================
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}✗${NC} DATABASE_URL not set in .env"
    echo -e "${YELLOW}⚠${NC}  Celery Beat requires DATABASE_URL to store schedules"
    exit 1
fi
echo -e "${GREEN}✓${NC} DATABASE_URL configured"

# ============================================================================
# 4. Check REDIS_URL
# ============================================================================
if [ -z "$REDIS_URL" ]; then
    echo -e "${YELLOW}⚠${NC}  REDIS_URL not set, using default: redis://localhost:6379/0"
    export REDIS_URL="redis://localhost:6379/0"
else
    echo -e "${GREEN}✓${NC} REDIS_URL configured: $REDIS_URL"
fi

# ============================================================================
# 5. Check Redis connection (optional, with timeout)
# ============================================================================
echo -e "${BLUE}→${NC} Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if timeout 2 redis-cli -u "$REDIS_URL" ping &> /dev/null; then
        echo -e "${GREEN}✓${NC} Redis is responding"
    else
        echo -e "${YELLOW}⚠${NC}  Redis check failed (timeout or connection refused)"
        echo -e "${YELLOW}⚠${NC}  Make sure Redis is running: redis-server"
        echo -e "${YELLOW}⚠${NC}  Or start with Docker: docker-compose up redis -d"
        echo ""
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠${NC}  redis-cli not found, skipping connection check"
fi

# ============================================================================
# 6. Check database connection (optional)
# ============================================================================
echo -e "${BLUE}→${NC} Checking database connection..."
if command -v psql &> /dev/null; then
    # Extract connection params from DATABASE_URL
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    DB_URL_SYNC="${DATABASE_URL//postgresql+asyncpg:\/\//postgresql://}"

    if timeout 2 psql "$DB_URL_SYNC" -c "SELECT 1;" &> /dev/null; then
        echo -e "${GREEN}✓${NC} Database is accessible"
    else
        echo -e "${YELLOW}⚠${NC}  Database check failed (timeout or connection refused)"
        echo -e "${YELLOW}⚠${NC}  Make sure PostgreSQL is running and DATABASE_URL is correct"
        echo ""
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠${NC}  psql not found, skipping database check"
fi

# ============================================================================
# 7. Verify Beat tables exist
# ============================================================================
echo -e "${BLUE}→${NC} Checking for Beat scheduler tables..."
if command -v psql &> /dev/null; then
    DB_URL_SYNC="${DATABASE_URL//postgresql+asyncpg:\/\//postgresql://}"

    if psql "$DB_URL_SYNC" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'celery_schema' AND table_name = 'celery_periodictask');" 2>/dev/null | grep -q "t"; then
        echo -e "${GREEN}✓${NC} Beat tables exist in celery_schema"
    else
        echo -e "${RED}✗${NC} Beat tables not found in celery_schema"
        echo -e "${YELLOW}⚠${NC}  Please run the migration first:"
        echo "   psql \"\$DATABASE_URL\" < supabase/migrations/017_celery_beat_scheduler.sql"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC}  psql not found, skipping table check"
fi

# ============================================================================
# 8. Start Celery Beat
# ============================================================================
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}Starting Celery Beat Scheduler...${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  • Database scheduler: sqlalchemy-celery-beat"
echo "  • Check interval: 5 seconds"
echo "  • Timezone: America/Santiago"
echo "  • Log level: ${1:-info}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Start Beat with database scheduler
# Note: Beat does NOT use --pool option (that's for workers only)
celery -A app.infrastructure.celery.worker beat \
    --loglevel="${1:-info}" \
    --scheduler=sqlalchemy_celery_beat.schedulers:DatabaseScheduler

# ============================================================================
# Notes:
# ============================================================================
#
# The Beat scheduler:
# - Reads periodic tasks from PostgreSQL
# - Submits tasks to Redis queues at scheduled times
# - Does NOT execute tasks itself (that's the worker's job)
#
# Common Issues:
# 1. "Table does not exist" → Run migration 017_celery_beat_scheduler.sql
# 2. "Connection refused" → Start Redis: redis-server or docker-compose up redis
# 3. "No tasks scheduled" → Create tasks via API or directly in database
#
# Monitoring:
# - Check logs for "Scheduler: Sending due task..."
# - Query database: SELECT * FROM celery_periodic_task WHERE enabled = true;
# - Use admin interface or API: GET /api/scheduled-tasks
#
# ============================================================================

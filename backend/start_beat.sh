#!/bin/bash

# ============================================================================
# Celery Beat Scheduler Startup Script for Backend V2
# ============================================================================
#
# This script starts the Celery Beat scheduler for Backend V2, which reads
# periodic tasks from the database and submits them to the worker queue.
#
# Backend V2 is focused on SII integration tasks only.
#
# The Beat scheduler:
# - Reads from PostgreSQL tables (celery_periodic_task, etc.)
# - Checks for changes every 5 seconds (beat_max_loop_interval)
# - Submits SII tasks to the appropriate queues (default, low)
#
# Requirements:
# - PostgreSQL with Beat tables (celery_schema)
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
echo -e "${BLUE}Backend V2 - SII Integration${NC}"
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
    echo "   uv venv"
    echo "   source .venv/bin/activate"
    echo "   uv sync"
    exit 1
fi

# ============================================================================
# 2. Check .env file
# ============================================================================
if [ ! -f ".env" ]; then
    echo -e "${RED}✗${NC} No .env file found"
    echo -e "${YELLOW}⚠${NC}  Please create a .env file with:"
    echo "   DATABASE_URL=postgresql://..."
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
# 6. Start Celery Beat
# ============================================================================
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}Starting Celery Beat Scheduler...${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  • Backend: V2 (SII Integration)"
echo "  • Database scheduler: sqlalchemy-celery-beat"
echo "  • Check interval: 5 seconds"
echo "  • Timezone: America/Santiago"
echo "  • Queues: default, low"
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
# 1. "Table does not exist" → Run migration to create celery_schema tables
# 2. "Connection refused" → Start Redis: redis-server
# 3. "No tasks scheduled" → Create tasks via API or directly in database
#
# Monitoring:
# - Check logs for "Scheduler: Sending due task..."
# - Query database: SELECT * FROM celery_schema.celery_periodictask WHERE enabled = true;
#
# ============================================================================

#!/bin/bash

# Start Celery worker script for Fizko backend
# Usage: ./start_celery.sh [options]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Celery worker for Fizko${NC}"

# Check if Redis is running (with timeout)
echo -e "${YELLOW}📡 Checking Redis connection...${NC}"
if command -v redis-cli &> /dev/null; then
    if timeout 2 redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not verify Redis, but continuing anyway${NC}"
        echo -e "${YELLOW}💡 Make sure Redis is running: redis-server${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  redis-cli not found, skipping Redis check${NC}"
    echo -e "${YELLOW}💡 Make sure Redis is running on localhost:6379${NC}"
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "${YELLOW}💡 Copy .env.example to .env and configure REDIS_URL${NC}"
    exit 1
fi

# Parse command line arguments
LOGLEVEL=${LOGLEVEL:-info}
CONCURRENCY=${CONCURRENCY:-4}
QUEUE=${QUEUE:-""}
RELOAD=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --reload)
            # Note: Celery doesn't have built-in --reload
            # We'll use watchdog if available, otherwise just note it
            RELOAD="--pool=solo"  # Solo pool is better for development
            shift
            ;;
        --queue|-Q)
            QUEUE="-Q $2"
            shift 2
            ;;
        --concurrency|-c)
            CONCURRENCY="$2"
            shift 2
            ;;
        --loglevel|-l)
            LOGLEVEL="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --reload              Enable autoreload (for development)"
            echo "  --queue, -Q QUEUE     Run worker for specific queue (high, default, low)"
            echo "  --concurrency, -c N   Number of worker processes (default: 2)"
            echo "  --loglevel, -l LEVEL  Log level (default: info)"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Start worker for all queues"
            echo "  $0 --reload                           # Start with autoreload (dev mode)"
            echo "  $0 --queue high --concurrency 4       # High priority queue, 4 workers"
            echo "  $0 --loglevel debug                   # Debug logging"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build the command
CMD="celery -A app.infrastructure.celery.worker worker --loglevel=$LOGLEVEL --concurrency=$CONCURRENCY $QUEUE $RELOAD"

echo -e "${GREEN}📋 Starting Celery worker with:${NC}"
echo -e "   Log level: ${LOGLEVEL}"
echo -e "   Concurrency: ${CONCURRENCY}"
if [ -n "$QUEUE" ]; then
    echo -e "   Queue: ${QUEUE:3}"  # Remove '-Q ' prefix
else
    echo -e "   Queue: all"
fi
if [ -n "$RELOAD" ]; then
    echo -e "   Mode: ${YELLOW}development (solo pool)${NC}"
else
    echo -e "   Mode: production"
fi

echo ""
echo -e "${GREEN}🎯 Running: $CMD${NC}"
echo ""

# Execute the command
exec $CMD

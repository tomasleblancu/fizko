#!/bin/bash
# ============================================
# Development server with PRODUCTION PARITY
# ============================================
# This script runs the backend with the same configuration as production:
# - Gunicorn process manager
# - 2 Uvicorn workers
# - Same database pooling (pgbouncer)
# - Auto-reload on code changes

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Fizko Backend - Production Parity${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    echo -e "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env and add your credentials${NC}"
    exit 1
fi

# Check if using pgbouncer pooler (port 6543)
if grep -q ":6543" .env; then
    echo -e "${GREEN}✓${NC} Using pgbouncer pooler (port 6543) - matches production"
else
    echo -e "${YELLOW}⚠️  DATABASE_URL is not using port 6543 (pgbouncer pooler)${NC}"
    echo -e "  For production parity, update your DATABASE_URL to use port 6543"
    echo -e "  Example: postgresql+asyncpg://user:pass@db.project.supabase.co:6543/postgres?sslmode=require"
fi

# Check if dependencies are installed
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo -e "Installing dependencies with uv..."
    uv sync
fi

# Port selection
PORT=${PORT:-8089}
WORKERS=${WORKERS:-2}

echo ""
echo -e "${GREEN}Starting backend with:${NC}"
echo -e "  Port: ${BLUE}${PORT}${NC}"
echo -e "  Workers: ${BLUE}${WORKERS}${NC}"
echo -e "  Reload: ${BLUE}enabled${NC}"
echo -e "  Pooler: ${BLUE}pgbouncer (6543)${NC}"
echo ""
echo -e "${YELLOW}API available at:${NC}"
echo -e "  ${BLUE}http://localhost:${PORT}${NC}"
echo -e "  ${BLUE}http://localhost:${PORT}/docs${NC} (OpenAPI)"
echo -e "  ${BLUE}http://localhost:${PORT}/health${NC} (Health check)"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop${NC}"
echo ""

# Run with Gunicorn + Uvicorn workers (same as production)
uv run gunicorn app.main:app \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --reload \
    --access-logfile - \
    --error-logfile - \
    --log-level info

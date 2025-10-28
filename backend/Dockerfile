# ============================================
# Dockerfile para Backend Fizko (Railway)
# ============================================
# FastAPI + Selenium + Chrome para SII scraping

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install uv for faster dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv sync
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
# Using full python image for better browser compatibility
FROM python:3.11

WORKDIR /app

# Install Chromium and ChromeDriver for Selenium
# Using Chromium from Debian repos (easier than Chrome)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && chromium --version \
    && chromedriver --version

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY ./app ./app

# Copy migrations if they exist (optional for runtime)
# Migrations should be applied separately via Supabase SQL Editor
# COPY ./migrations ./migrations

# Create necessary directories
RUN mkdir -p /app/sessions /app/chrome-data /app/screenshots

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Chromium settings for headless mode
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV CHROME_BINARY_PATH=/usr/bin/chromium

# Expose port (Railway assigns dynamically)
EXPOSE 8080

# Health check (use $PORT from Railway)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Run FastAPI with Gunicorn + Uvicorn workers for production
# - 2 workers for small instances (Railway Starter)
# - Use uvicorn.workers.UvicornWorker for ASGI support
# - Timeout: 120s for long-running SII scraping tasks
# - Graceful timeout: 30s for shutdown
# - Keep-alive: 5s for connection reuse
CMD gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8080} \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

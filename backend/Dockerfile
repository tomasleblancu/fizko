# ============================================
# Dockerfile para Backend V2 - SII Integration Service
# ============================================
# FastAPI + Celery + Selenium + Chrome
# Multi-stage build optimizado

# ============================================
# Stage 1: Builder - Instalar dependencias
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install uv for faster dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies for production)
ARG INSTALL_DEV=false
RUN echo "================================" && \
    echo "INSTALL_DEV value: $INSTALL_DEV" && \
    echo "================================" && \
    if [ "$INSTALL_DEV" = "true" ]; then \
        echo "Installing WITH dev dependencies..." && \
        uv sync --frozen --extra dev; \
    else \
        echo "Installing WITHOUT dev dependencies..." && \
        uv sync --frozen --no-dev; \
    fi

# ============================================
# Stage 2: Runtime - Imagen final
# ============================================
FROM python:3.11

WORKDIR /app

# Install system dependencies
# - Chromium + ChromeDriver para Selenium (SII scraping)
# - curl para healthchecks
# - netcat-openbsd para wait_for_service checks
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    curl \
    netcat-openbsd \
    redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && chromium --version \
    && chromedriver --version

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY app ./app

# Copy tests (for running tests in container)
COPY tests ./tests

# Copy test configuration
COPY pytest.ini ./pytest.ini

# Copy entrypoint script and Railway-specific scripts
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY railway-worker.sh /railway-worker.sh
COPY railway-beat.sh /railway-beat.sh
RUN chmod +x /docker-entrypoint.sh /railway-worker.sh /railway-beat.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/sessions /app/chrome-data /app/screenshots \
    && chmod -R 755 /app/sessions /app/chrome-data /app/screenshots

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Chromium settings for headless mode
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV CHROME_BINARY_PATH=/usr/bin/chromium

# Expose port
# - 8000: FastAPI (backend-v2 default)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use entrypoint for flexible command execution
ENTRYPOINT ["/docker-entrypoint.sh"]

# Default command: FastAPI with Uvicorn
CMD ["fastapi"]

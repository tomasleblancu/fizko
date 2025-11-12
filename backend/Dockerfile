# ============================================
# Dockerfile para Backend Fizko
# ============================================
# FastAPI + Celery + Selenium + Chrome para SII scraping
# Multi-stage build optimizado para desarrollo y producción

# ============================================
# Stage 1: Builder - Instalar dependencias
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install uv for faster dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install ALL dependencies (including dev for local development)
# Production will use --no-dev
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
# - postgresql-client para migrations (opcional)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    curl \
    netcat-openbsd \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && chromium --version \
    && chromedriver --version

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY app ./app

# Copy scripts (including seed scripts)
COPY scripts ./scripts

# Copy tests (for running tests in container)
COPY tests ./tests

# Copy test configuration
COPY pytest.ini ./pytest.ini

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

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
# - 8080: FastAPI (production/Railway)
# - 8000: FastAPI (development)
EXPOSE 8080 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Use entrypoint for flexible command execution
ENTRYPOINT ["/docker-entrypoint.sh"]

# Default command: FastAPI with Gunicorn (production)
# Override in docker-compose.yml for different services
CMD ["fastapi"]

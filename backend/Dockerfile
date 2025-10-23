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

# Install dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install Chrome and dependencies for Selenium (force rebuild - v2)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && google-chrome --version

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

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

# Chrome settings for headless mode
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/bin/google-chrome

# Expose port (Railway assigns dynamically)
EXPOSE 8080

# Health check (use $PORT from Railway)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Run FastAPI with uvicorn (use $PORT from Railway, default to 8080)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}

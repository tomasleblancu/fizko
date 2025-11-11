.PHONY: help test test-unit test-integration test-e2e test-security test-sii test-cov test-fast test-watch clean install

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RESET := \033[0m

help:  ## Show this help message
	@echo "$(BLUE)Available make commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

install:  ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	uv sync

# Testing commands

test:  ## Run all tests
	@echo "$(BLUE)Running all tests...$(RESET)"
	.venv/bin/pytest tests/ -v

test-unit:  ## Run unit tests only (fast)
	@echo "$(BLUE)Running unit tests...$(RESET)"
	.venv/bin/pytest tests/unit/ -v -m unit

test-integration:  ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(RESET)"
	.venv/bin/pytest tests/integration/ -v -m integration

test-e2e:  ## Run E2E tests
	@echo "$(BLUE)Running E2E tests...$(RESET)"
	.venv/bin/pytest tests/e2e/ -v -m e2e

test-security:  ## Run security tests
	@echo "$(BLUE)Running security tests...$(RESET)"
	.venv/bin/pytest tests/security/ -v -m security

test-sii:  ## Run SII integration tests (requires credentials)
	@echo "$(BLUE)Running SII integration tests...$(RESET)"
	.venv/bin/pytest tests/sii_integration/ -v -m sii

test-cov:  ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	.venv/bin/pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(RESET)"

test-fast:  ## Run fast tests only (unit, skip slow)
	@echo "$(BLUE)Running fast tests...$(RESET)"
	.venv/bin/pytest tests/unit/ -v -m "unit and not slow"

test-watch:  ## Run tests in watch mode (requires pytest-watch)
	@echo "$(BLUE)Running tests in watch mode...$(RESET)"
	.venv/bin/ptw tests/ -- -v

test-file:  ## Run specific test file (usage: make test-file FILE=path/to/test.py)
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=path/to/test.py"; \
		exit 1; \
	fi
	@echo "$(BLUE)Running $(FILE)...$(RESET)"
	.venv/bin/pytest $(FILE) -v

test-failed:  ## Re-run only failed tests from last run
	@echo "$(BLUE)Re-running failed tests...$(RESET)"
	.venv/bin/pytest --lf -v

# Code quality

format:  ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(RESET)"
	uv run ruff format .

lint:  ## Lint code with ruff
	@echo "$(BLUE)Linting code...$(RESET)"
	uv run ruff check .

lint-fix:  ## Lint and fix issues automatically
	@echo "$(BLUE)Linting and fixing code...$(RESET)"
	uv run ruff check . --fix

typecheck:  ## Type check with mypy (if configured)
	@echo "$(BLUE)Type checking...$(RESET)"
	python3 -m py_compile app/**/*.py

# Development

dev:  ## Start development server (production parity)
	@echo "$(BLUE)Starting development server...$(RESET)"
	./dev.sh

worker:  ## Start Celery worker
	@echo "$(BLUE)Starting Celery worker...$(RESET)"
	.venv/bin/celery -A app.infrastructure.celery worker --loglevel=info

beat:  ## Start Celery Beat scheduler
	@echo "$(BLUE)Starting Celery Beat...$(RESET)"
	./start_beat.sh

# Database

db-migrate:  ## Apply database migrations (manual via Supabase)
	@echo "$(BLUE)Apply migrations manually in Supabase SQL editor$(RESET)"
	@echo "Migrations are in: supabase/migrations/"

# Cleanup

clean:  ## Clean cache and temporary files
	@echo "$(BLUE)Cleaning cache files...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)Cache cleaned!$(RESET)"

# CI/CD helpers

ci-test:  ## Run tests for CI (skip slow and SII tests)
	@echo "$(BLUE)Running CI tests...$(RESET)"
	.venv/bin/pytest tests/ -v -m "not slow and not sii" --cov=app --cov-report=xml

ci-lint:  ## Run linting for CI
	@echo "$(BLUE)Running CI linting...$(RESET)"
	uv run ruff check .
	python3 -m py_compile app/**/*.py

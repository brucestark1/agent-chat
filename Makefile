.PHONY: help install fmt lint typecheck test check clean dev db-up db-down db-reset

help:
	@echo "Agentic Chat Loop MVP - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install    - Install dependencies and pre-commit hooks"
	@echo "  make dev        - Install dev dependencies"
	@echo ""
	@echo "Quality Gates:"
	@echo "  make fmt        - Format code with ruff"
	@echo "  make lint       - Lint code with ruff"
	@echo "  make typecheck  - Type check with pyright"
	@echo "  make test       - Run tests with pytest"
	@echo "  make check      - Run all quality gates (fmt, lint, typecheck, test)"
	@echo ""
	@echo "Database:"
	@echo "  make db-up      - Start Postgres with Docker Compose"
	@echo "  make db-down    - Stop Postgres"
	@echo "  make db-reset   - Reset database (down, up, migrate, seed)"
	@echo ""
	@echo "Other:"
	@echo "  make clean      - Clean generated files"

install:
	pip install -e ".[dev]"
	pre-commit install

dev:
	pip install -e ".[dev]"

fmt:
	ruff format src tests
	ruff check --fix src tests

lint:
	ruff check src tests

typecheck:
	pyright src tests

test:
	python -m pytest

check: fmt lint typecheck test

clean:
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name pyrightcache -exec rm -rf {} +

db-up:
	docker-compose up -d
	@echo "Waiting for Postgres to be ready..."
	@sleep 3

db-down:
	docker-compose down

db-reset: db-down db-up
	@echo "Database reset complete"

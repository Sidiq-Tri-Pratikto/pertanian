PORT ?= 8020
OPENAPI_OUT ?= ../../contracts/openapi.json

.PHONY: install
install:
	uv sync
	@git rev-parse --git-dir >/dev/null 2>&1 && uv run pre-commit install -c ../../.pre-commit-config.yaml --allow-missing-config || echo "Skipped pre-commit install: not a git repository"

.PHONY: lock
lock:
	uv lock

.env:
	cp .env.example .env

.PHONY: run
run: .env
	uv run uvicorn app.main:app --host 0.0.0.0 --port $(PORT) --reload

# Dispatches outbox events and runs jobs; Ctrl+C finishes the current pass.
.PHONY: worker
worker: .env
	uv run python -m app.worker

# Recreates the labelled demo accounts and fixtures (spec 021); real accounts are untouched.
.PHONY: demo-seed
demo-seed: .env
	uv run python -m app.demo

.PHONY: run-dependencies
run-dependencies:
	docker compose -f dev-compose.yml up -d --wait

.PHONY: stop-dependencies
stop-dependencies:
	docker compose -f dev-compose.yml down

.PHONY: reset-dependencies
reset-dependencies:
	docker compose -f dev-compose.yml down -v

.PHONY: migrate
migrate: .env
	uv run alembic upgrade head

.PHONY: openapi
openapi: .env
	@mkdir -p $(dir $(OPENAPI_OUT))
	uv run python -m app.core.openapi > $(OPENAPI_OUT)

.PHONY: lint
lint:
	uv run ruff check .
	uv run ruff format --check .

.PHONY: test
test:
	uv run pytest tests

.PHONY: test-unit
test-unit:
	uv run pytest tests/unit

.PHONY: test-integration
test-integration:
	uv run pytest tests/integration

.PHONY: test-coverage
test-coverage:
	uv run pytest tests --cov --cov-report=term --cov-report=html

.PHONY: check
check: lint test-coverage

# temuriset-api

TemuRiset service: FastAPI, async SQLAlchemy, Alembic and Postgres 17. It is the one authority for matching, permissions, money semantics and consent; the web client only renders what it returns.

To run the whole product, use `make dev` from the [project root](../../README.md#quick-start). Its [testing guide](../../README.md#testing) covers both applications.

## Run the service alone

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
make install           # Python dependencies and pre-commit hooks
make run-dependencies  # Postgres on host port 5442
make migrate           # creates .env on first use, then applies migrations
make run               # API with reload on port 8020
```

Open http://localhost:8020/docs. Use `make run PORT=8030` if port 8020 is taken, and `make stop-dependencies` when you finish.

## Testing

```bash
make test-unit         # no services needed
make run-dependencies  # once, for everything below
make check             # lint, format check, all tests, 80% coverage gate
```

| Path | Covers | Needs |
|---|---|---|
| `tests/unit/capabilities/` | Manifest and composition | Nothing |
| `tests/unit/core/` | Errors, database session, OpenAPI document, no money-movement routes | Nothing |
| `tests/unit/health/` | Liveness and readiness | Nothing |
| `tests/integration/` | Real requests against Postgres after migrations | Postgres |

Run one test with `uv run pytest tests/unit/health/test_health.py -v`, or match by name with `uv run pytest tests -k capabilities`. `make test-coverage` also writes an HTML report to `htmlcov/index.html`.

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | yes | | Async SQLAlchemy URL |
| `SERVICE_NAME` | no | `temuriset-api` | Name on failure records |
| `ENVIRONMENT` | no | `development` | Deployment environment |
| `LOG_LEVEL` | no | `INFO` | Log level |
| `CORS_ALLOWED_ORIGINS` | no | `[]` | JSON list of browser origins; the web client proxies through its own origin and needs none |
| `COMPOSITION` | no | `generic-base` | `generic-base`, `generic-with-review` or `project-support-only`; anything else stops startup |
| `SKIP_MIGRATIONS` | no | `false` | Container start skips migrations when `true` |
| `PORT` | no | `8000` | Container listen port (`make run` uses 8020 on the host) |

## Commands

| Command | Does |
|---|---|
| `make openapi` | Export the API contract to `contracts/openapi.json` |
| `make test-integration` | Integration tests only, needs Postgres |
| `make reset-dependencies` | Stop Postgres and delete its volume, for an empty database |
| `make lint` | Ruff lint and format check |

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health/live` | Liveness |
| `GET /health/ready` | Readiness, checks the database |
| `GET /api/v1/capabilities` | Non-secret deployment manifest; explains, never authorizes |

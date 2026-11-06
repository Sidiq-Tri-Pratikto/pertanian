# hematdaya-api

HematDaya service: FastAPI, async SQLAlchemy, Alembic and Postgres 17. It is the one calculation authority; the mobile app only renders what it returns.

To run the whole product, use `./local-start.sh` from the [repository root](../../README.md#quick-start).

## Run the service alone

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
make install           # Python dependencies and pre-commit hooks
make run-dependencies  # Postgres on port 5432
make migrate           # creates .env on first use, then applies migrations
make run               # API with reload on port 8000
```

Open http://localhost:8000/docs. Use `make run PORT=8010` if port 8000 is taken, and `make stop-dependencies` when you finish.

## Testing

```bash
make test-unit         # no services needed
make run-dependencies  # once, for everything below
make check             # lint, format check, all tests, 80% coverage gate
```

| Path | Covers | Needs |
|---|---|---|
| `tests/unit/capabilities/` | Manifest and composition | Nothing |
| `tests/unit/core/` | Errors, database session, OpenAPI document, no actuation routes | Nothing |
| `tests/unit/health/` | Liveness and readiness | Nothing |
| `tests/integration/` | Real requests against Postgres after migrations | Postgres |

Run one test with `uv run pytest tests/unit/health/test_health.py -v`, or match by name with `uv run pytest tests -k capabilities`. `make test-coverage` also writes an HTML report to `htmlcov/index.html`.

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | yes | | Async SQLAlchemy URL |
| `SERVICE_NAME` | no | `hematdaya-api` | Name on failure records |
| `ENVIRONMENT` | no | `development` | Deployment environment |
| `LOG_LEVEL` | no | `INFO` | Log level |
| `CORS_ALLOWED_ORIGINS` | no | `[]` | JSON list of browser origins; native clients need none |
| `COMPOSITION` | no | `core-plus-optional` | Supported product composition; `core-only` drops optional modules |
| `SKIP_MIGRATIONS` | no | `false` | Container start skips migrations when `true` |
| `PORT` | no | `8000` | Container listen port |

## Commands

| Command | Does |
|---|---|
| `make openapi` | Export the API contract to `contracts/openapi.json` |
| `make test-integration` | Integration tests only, needs Postgres |
| `make lint` | Ruff lint and format check |

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health/live` | Liveness |
| `GET /health/ready` | Readiness, checks the database |
| `GET /api/v1/capabilities` | Non-secret deployment manifest; explains, never authorizes |

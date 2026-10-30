# hematdaya-api

Service for hematdaya.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
make install
make run-dependencies
make migrate
make run
```

API: http://localhost:8000, docs at `/docs`.

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | yes | | Async SQLAlchemy URL |
| `SERVICE_NAME` | no | `hematdaya-api` | Name on failure records |
| `ENVIRONMENT` | no | `development` | Deployment environment |
| `LOG_LEVEL` | no | `INFO` | Log level |
| `CORS_ALLOWED_ORIGINS` | no | `[]` | JSON list of browser origins; native clients need none |
| `SKIP_MIGRATIONS` | no | `false` | Container start skips migrations when `true` |
| `PORT` | no | `8000` | Container listen port |

## Commands

| Command | Does |
|---|---|
| `make run` | API with reload |
| `make migrate` | Apply migrations |
| `make openapi` | Export the API contract to `contracts/openapi.json` |
| `make test-unit` | Unit tests, no services |
| `make test-integration` | Integration tests, needs Postgres |
| `make check` | Lint, format check, all tests, 80% coverage gate |

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness |
| `GET /ready` | Readiness, checks the database |

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
| `tests/unit/capabilities/` | Manifest, compositions and overrides, capability guard, startup configuration checks | Nothing |
| `tests/unit/core/` | Errors, database session, OpenAPI document, no money-movement routes, clock, money and cursors | Nothing |
| `tests/unit/platform/` | Stale versions, request digest, acting-party placeholder, worker backoff and registry | Nothing |
| `tests/unit/health/` | Liveness and readiness | Nothing |
| `tests/integration/` | Real requests against Postgres after migrations | Postgres |
| `tests/integration/identity/` | Sign-up for both personas without an organization, codes wrong, expired and used up, 1,000-guess brute force, rate limits, no account leak, sign-out, cross-origin refusal, `PATCH /me` | Postgres |
| `tests/integration/documents/` | Limits before upload, quarantine and scan (AC13, AC14), scans without text (AC15), signature mismatch, grants, ranges and revocation (AC65), a 20 MB round trip | Postgres |
| `tests/unit/documents/` | ClamAV INSTREAM against a fake daemon, byte sniffing, extraction, chunked storage | Nothing |
| `tests/integration/portfolio/` | Drafts, each publication rule, immutable versions (AC07–AC11), stale drafts, archive, public projection, outbox events | Postgres |
| `tests/integration/access/` | Organizations, capabilities (AC04), hidden organizations (AC05), a removed member's job denied (AC06), invitations expired and revoked, stale context, last manager | Postgres |
| `tests/integration/test_isolation.py` | Every data route called as an unrelated party returns `NOT_FOUND` or nothing; fails when a new route is not registered | Postgres |
| `tests/integration/platform/` | Idempotent replay and conflict, 20 parallel requests with one key, operations, append-only audit, outbox atomic with the request, worker retries, two workers, jobs | Postgres |

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
| `COMPOSITION_OVERRIDES` | no | `{}` | JSON object switching capabilities on or off on top of the composition, for example `{"organization_review": true}`. An unknown capability, a missing dependency or a secret-looking value stops startup |
| `FILE_SCANNER` | no | `development-accept` | `clamav` or `development-accept`; the second stops startup outside development |
| `WEB_ORIGIN` | no | `http://localhost:3020` | Origin of the web client; an unsafe request carrying the session cookie from any other origin gets `FORBIDDEN` |
| `SESSION_COOKIE_SECURE` | no | unset | `Secure` flag on `tr_session`; unset means secure everywhere but development |
| `MAILBOX_ADAPTER` | no | `development` | Writes email to `mailbox_messages`, readable at `GET /api/v1/dev/mailbox` in development; stops startup elsewhere until spec 042 |
| `CODE_REQUESTS_PER_EMAIL_PER_HOUR` | no | `5` | Sign-in code requests per email per hour |
| `CODE_REQUESTS_PER_ADDRESS_PER_HOUR` | no | `20` | Sign-in code requests per client address per hour |
| `STORAGE_PATH` | no | `.storage` | Private folder for uploaded bytes; downloads always go through the gateway |
| `CLAMAV_HOST`, `CLAMAV_PORT` | no | `localhost`, `3310` | ClamAV daemon for `FILE_SCANNER=clamav` (`--profile scanner` in `dev-compose.yml`) |
| `SKIP_MIGRATIONS` | no | `false` | Container start skips migrations when `true` |
| `PORT` | no | `8000` | Container listen port (`make run` uses 8020 on the host) |

## Commands

| Command | Does |
|---|---|
| `make openapi` | Export the API contract to `contracts/openapi.json` |
| `make worker` | Run `python -m app.worker`: dispatch outbox events and run jobs; Ctrl+C finishes the current pass |
| `make test-integration` | Integration tests only, needs Postgres |
| `make reset-dependencies` | Stop Postgres and delete its volume, for an empty database |
| `make lint` | Ruff lint and format check |

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health/live` | Liveness |
| `GET /health/ready` | Readiness, checks the database |
| `GET /api/v1/capabilities` | Non-secret deployment manifest; explains, never authorizes |
| `POST /api/v1/auth/code` | Email a six-digit code for `sign_up` or `sign_in`; always 202, so it never reveals whether an account exists |
| `POST /api/v1/auth/verify` | Check the code, set the `tr_session` cookie, return `/me`; sign-up creates the account and its personal party |
| `POST /api/v1/auth/sign-out` | Revoke this session and clear the cookie |
| `GET /api/v1/me`, `PATCH /api/v1/me` | The signed-in account; changes need `expected_version` |
| `POST /api/v1/organizations` | Create an organization; the creator joins with every capability. Needs `Idempotency-Key` |
| `GET /api/v1/organizations/{id}/members` | Members and capabilities, to members only |
| `DELETE /api/v1/organizations/{id}/members/{account_id}` | Remove a member: `acting_party_id`, `expected_version`, `manage_members`; never the last manager |
| `POST`, `GET /api/v1/organizations/{id}/invitations` | Invite an email with capabilities for seven days (`Idempotency-Key`); list invitations |
| `GET /api/v1/invitations/{token}`, `POST .../accept` | What the invitation grants; join. Only the invited email sees it |
| `POST /api/v1/invitations/{id}/revoke` | Revoke a pending invitation |
| `PUT /api/v1/me/context` | Act as the personal party or a joined organization; anything else is `NOT_FOUND` |
| `POST`, `GET /api/v1/inventions` | Start an invention for the acting party (`Idempotency-Key`); list its inventions with drafts and archived ones |
| `GET /api/v1/inventions/{id}` | Owner view: draft, published version, history numbers |
| `PUT /api/v1/inventions/{id}/draft` | Save the whole draft against `expected_version` (`Idempotency-Key`); publication rules do not apply |
| `POST /api/v1/inventions/{id}/publish`, `.../archive` | Publish an immutable version; archive while keeping history |
| `GET /api/v1/inventions/{id}/public` | The published version, nothing private; `NOT_FOUND` when unpublished or archived |
| `POST /api/v1/documents/upload-intents` | Declare title, kind, type and size; unsupported or oversized files are refused before any byte |
| `PUT /api/v1/documents/upload-intents/{id}/content` | Stream the bytes into quarantine; the worker scans, then reads the text |
| `GET /api/v1/documents`, `GET /api/v1/documents/{id}` | The acting party's documents: versions with file, extraction and review states, and grants |
| `POST /api/v1/documents/{id}/grants`, `POST /api/v1/grants/{id}/revoke` | Share one version with one party; revoke and report copies already delivered |
| `GET /api/v1/documents/{id}/versions/{n}/content` | The gateway: re-authorizes every request and range, records grantee downloads, never issues a storage URL |
| `GET /api/v1/dev/mailbox?email=` | Development only: the codes and notes that would have been emailed |
| `GET /api/v1/operations/{id}` | Whether the acting party's operation committed, for a client that lost the response |

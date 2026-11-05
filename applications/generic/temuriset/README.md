# TemuRiset

TemuRiset helps inventors find investors and partners, then carries a deliberate pitch through review, revisions, meetings and a relationship both parties confirm. It records discussions and agreements; it never moves money or issues shares.

This is the base release: real navigation for both personas, the design system, the API contract and the capability manifest, with "Segera hadir" for every planned feature. The [roadmap](docs/roadmap/README.md) adds the features one pull request at a time.

- [Quick start](#quick-start)
- [Prerequisites](#prerequisites)
- [Running locally](#running-locally)
- [Testing](#testing)
- [All commands](#all-commands)
- [Troubleshooting](#troubleshooting)
- [Project layout](#project-layout)
- [Continue the work](#continue-the-work)

## Quick start

With [uv](https://docs.astral.sh/uv/getting-started/installation/), Docker (running) and Node 24 installed, from the root of the pertanian repository:

```bash
cd applications/generic/temuriset
make dev
```

The first run takes a few minutes while it installs everything. When it prints the addresses below, it is ready:

| Open | What you get |
|---|---|
| http://localhost:3020 | The web app |
| http://localhost:8020/docs | API reference, with "Try it out" |
| http://localhost:8020/health/ready | API and database health |

Check that it works:

1. Open http://localhost:3020/start, pick "Saya punya inovasi dan mencari dukungan", and press **Lanjutkan**.
2. Beranda shows **Layanan tersedia** and **Versi 0.1.0**. That message came from the API through the web app.
3. From another terminal, the same path the browser uses:

   ```bash
   curl http://localhost:3020/api/v1/capabilities
   ```

   You get JSON with `"composition": {"id": "generic-base", ...}` and every capability `"planned"`.

Press `Ctrl+C` in the first terminal to stop the web app, the API and Postgres.

## Prerequisites

| Tool | Version | Check it | Why |
|---|---|---|---|
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | any recent | `uv --version` | Python 3.13 and API dependencies |
| [Docker](https://docs.docker.com/get-started/get-docker/) | running | `docker info` | Local Postgres |
| [Node.js](https://nodejs.org/) via [nvm](https://github.com/nvm-sh/nvm) | 24 | `node -v` prints `v24.…` | The web app |
| make, curl, git | any | `make -v` | Commands and the start script |

<details>
<summary>Setting them up</summary>

```bash
# uv (installs Python 3.13 for you when needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node 24 with nvm; this folder has an .nvmrc, so plain `nvm use` picks 24
nvm install 24
nvm use

# Docker: install Docker Desktop or Docker Engine, then confirm it runs
docker info --format '{{.ServerVersion}}'
```

On Linux with Docker Desktop, start it with `systemctl --user start docker-desktop`. `make dev` uses nvm automatically when it is installed, and stops with a clear message if anything is missing.

</details>

## Running locally

### Everything at once

```bash
make dev
```

It runs four steps and tells you which one it is on:

1. Installs API and web dependencies (skipped when nothing changed).
2. Starts Postgres on port 5442 and applies migrations.
3. Starts the API on port 8020 and waits until it is healthy.
4. Starts the web app on port 3020 with hot reload.

Ports differ from HematDaya's, so both projects can run at once. If something else holds a port:

```bash
API_PORT=8030 WEB_PORT=3030 ./local-start.sh
```

### One part at a time

Use two terminals when you want to restart one side without the other.

```bash
# Terminal 1: Postgres and the API
cd applications/temuriset-api
make install           # first time only
make run-dependencies  # Postgres on port 5442
make migrate
make run               # http://localhost:8020, reloads on save
```

```bash
# Terminal 2: the web app
cd applications/temuriset-web
nvm use
make install           # first time only
make run               # http://localhost:3020, reloads on save
```

The web app forwards `/api/v1/*` and `/health/*` to `API_URL` (default `http://localhost:8020`), so the browser only ever talks to port 3020.

### Stop and reset

| You want to | Run |
|---|---|
| Stop everything started by `make dev` | `Ctrl+C` |
| Stop Postgres left running by `make check` or `make test-api` | `make stop` |
| Start again with an empty database | `make reset-db` |
| Choose the other persona | **Ubah** in the header, or open http://localhost:3020/start |

### Configuration

Each application creates its `.env` from `.env.example` on first run, and the defaults work locally. You only need to edit `.env` to change a port or the composition:

| Variable | Where | Default | Use |
|---|---|---|---|
| `COMPOSITION` | API `.env` | `generic-base` | Also `generic-with-review` or `project-support-only` |
| `DATABASE_URL` | API `.env` | Postgres on `localhost:5442` | Point at another database |
| `API_URL` | web `.env` | `http://localhost:8020` | Where the web app forwards API calls |

Full lists: [API configuration](applications/temuriset-api/README.md#configuration) and [web configuration](applications/temuriset-web/README.md#configuration).

## Testing

### The short version

```bash
nvm use        # once per terminal, for the web tests
make setup     # once, installs both applications
make test      # a few seconds, no Docker needed
make check     # before every pull request; needs Docker
```

`make test` is your fast loop. `make check` is exactly what a pull request must pass, and it leaves Postgres running; `make stop` stops it.

### What each command runs

| Command | API | Web | Needs |
|---|---|---|---|
| `make test` | Unit tests | Unit, page and accessibility tests | Nothing |
| `make test-api` | Unit and Postgres integration tests | | Docker |
| `make test-web` | | Unit, page and accessibility tests | Nothing |
| `make check` | Lint, format check, all tests, 80% coverage gate | Lint with no warnings, typecheck, all tests, 80% coverage gate | Docker |

`make check` also checks that the copied design-system stylesheets match their source and that every PRD requirement still has a spec.

### What the tests cover

| Area | Where | Checks |
|---|---|---|
| API capability manifest | `applications/temuriset-api/tests/unit/capabilities/` | Honest `planned` statuses, the three compositions, unknown composition stops startup |
| API errors and contract | `applications/temuriset-api/tests/unit/core/` | Indonesian messages, no leaked values, OpenAPI document, no money-movement routes |
| API health | `applications/temuriset-api/tests/unit/health/`, `tests/integration/` | Liveness without a database, readiness against real Postgres |
| Web components | `applications/temuriset-web/tests/components.test.tsx` | Ported design-system components behave as specified |
| Web pages | `applications/temuriset-web/tests/pages.test.tsx` | Every route, persona redirects, the persona form |
| Web service status | `applications/temuriset-web/tests/service-status.test.tsx` | Available, unreachable with retry, final failure with reference ID |
| Web accessibility | `applications/temuriset-web/tests/a11y.test.tsx` | axe on every base view (jsdom: contrast and reflow come with spec 003) |
| Feature registry | `applications/temuriset-web/tests/registry.test.ts` | Every planned feature, screen coverage, links to existing specs |
| Design-system copy | `applications/temuriset-web/tests/design.test.ts` | `src/design/*.css` equals the design-system source |

### Run one thing

```bash
# API, from applications/temuriset-api
uv run pytest tests/unit/capabilities/test_capabilities.py -v   # one file
uv run pytest tests -k "composition" -v                          # tests whose name matches
make test-integration                                            # integration only; needs make run-dependencies

# Web, from applications/temuriset-web
npx vitest run tests/pages.test.tsx                 # one file
npx vitest run -t "starts at Jelajahi"              # tests whose name matches
npx vitest                                          # watch mode: reruns on save
```

### Coverage reports

| Run | Then open |
|---|---|
| `make test-coverage` in `applications/temuriset-api` | `applications/temuriset-api/htmlcov/index.html` |
| `make test-coverage` in `applications/temuriset-web` | `applications/temuriset-web/coverage/index.html` |

### Before you open a pull request

1. `make check` passes.
2. You changed an API route or schema: run `make openapi` in `applications/temuriset-api`, then `make generate-api` in `applications/temuriset-web`, and commit both generated files.
3. The design system released a new version: run `make design` in `applications/temuriset-web`.
4. Your spec's **Status** line is updated (see [Continue the work](#continue-the-work)).

CI runs the same checks from `.github/workflows/temuriset-api.yml` and `temuriset-web.yml` at the pertanian repository root, plus contract drift, a production build, a container build with an image scan, and a dependency audit.

## All commands

From this folder; `make` alone prints the list.

| Command | Does |
|---|---|
| `make setup` | Install API and web dependencies |
| `make dev` | Run Postgres, API and web together; `Ctrl+C` stops all |
| `make test` | Fast tests, no Docker |
| `make test-api` | All API tests, including Postgres integration tests |
| `make test-web` | Web unit, page and accessibility tests |
| `make check` | Everything a pull request must pass |
| `make stop` | Stop the local Postgres |
| `make reset-db` | Delete the local database volume and start empty |

Each application has more targets, such as `make openapi`, `make build` and `make design`. See the [API README](applications/temuriset-api/README.md) and the [web README](applications/temuriset-web/README.md).

## Troubleshooting

| You see | Do this |
|---|---|
| `Docker is not running` | Start Docker Desktop (Linux: `systemctl --user start docker-desktop`), then run again |
| `Node 24 is required` | `nvm install 24 && nvm use` |
| `Port 8020 is in use` or `Port 3020 is in use` | `API_PORT=8030 WEB_PORT=3030 ./local-start.sh` |
| `Postgres did not start` | Port 5442 is taken. `docker ps` shows what holds it; `make stop` stops this project's Postgres |
| `The API did not become ready` | Read the API log just above the message; `make reset-db` helps after a broken migration |
| Beranda says **Layanan belum tersedia** | The API is not running or `API_URL` in the web `.env` is wrong. Check with `curl http://localhost:8020/health/ready` |
| `design.test.ts` fails | The design system changed; run `make design` in `applications/temuriset-web` |
| CI fails on `contracts/openapi.json` or `schema.generated.ts` | Run `make openapi` in the API, then `make generate-api` in the web app, and commit both |
| Integration tests fail with a connection error | Run `make run-dependencies` in `applications/temuriset-api` first, or use `make test-api` |

## Project layout

| Path | Purpose |
|---|---|
| `applications/temuriset-api/` | FastAPI service, the one authority for rules, matching, permissions, money and consent |
| `applications/temuriset-web/` | Next.js web client in Indonesian, built from the TemuRiset Design System |
| `contracts/openapi.json` | Generated API contract; the web client's types come from it |
| `docs/roadmap/` | Milestones, binding architecture decisions, traceability |
| `specs/` | One spec and plan per pull request, 001 to 045 |
| `docs/product/` | Links to the PRD, handoff, prototype and design system |
| `local-start.sh` | What `make dev` runs |

## Continue the work

1. Read [`docs/roadmap/README.md`](docs/roadmap/README.md) and [`docs/roadmap/architecture.md`](docs/roadmap/architecture.md).
2. Pick the lowest-numbered spec in `specs/` whose **Depends on** specs are merged.
3. Branch with the spec folder's exact name, for example `git checkout -b 003-browser-checks`.
4. Follow its `spec.md` and `plan.md`, test first, then run [the PR checklist](#before-you-open-a-pull-request).

# Agent Instructions

Read this file before choosing commands or authority sources. It is the single entry point for every coding agent; `CLAUDE.md` imports it.

`.specify/memory/constitution.md` is the authoritative source for project standards. Rules live once in `.claude/rules/`, skills once in `.claude/skills/`. `.cursor/` and `.windsurf/` hold symlinks to them. Never copy a rule; edit the file in `.claude/`.

## Repository layout

| Path | Purpose |
|---|---|
| `applications/temuriset-api/` | FastAPI modular monolith: code, tests, migrations, Makefile, Dockerfile |
| `applications/temuriset-web/` | Next.js web client: routes, views, design-system ports, tests, Makefile |
| `contracts/` | Generated API contract shared by service and client; golden responses from spec 019 |
| `.specify/` | Constitution, error policy, Spec Kit templates and scripts |
| `specs/<NNN-feature>/` | One spec and plan per pull request |
| `docs/roadmap/` | Milestones, pick-up steps, binding architecture decisions, traceability |
| `docs/product/` | Links to the PRD, application handoff, prototype and design system |
| `docs/error-handling/` | Error catalog, deviations, audits |

Product sources stay where they were written, under `docs/generic/temuriset/` at the pertanian repository root. This project links them instead of copying them.

## Rules to read when relevant

| When | Read |
|---|---|
| Writing Python | `.claude/rules/001-code-standards.md` |
| Writing docstrings or docs | `.claude/rules/002-documentation.md` |
| Writing tests | `.claude/rules/003-testing.md` |
| Reviewing code | `.claude/rules/004-code-review.md` |
| Creating or reorganizing a feature module | `.claude/rules/005-module-structure.md` |
| Architecture or performance decisions | `.claude/rules/006-architecture.md` |
| Branches, commits, or PRs | `.claude/rules/007-git-workflow.md` |
| Any code that produces or consumes failures (always) | `.claude/rules/008-error-handling.md` |
| Writing TypeScript or web screens | `.claude/rules/009-web.md` |

## Workflow

Specs 003 to 045 are already written. Do not run `speckit-specify` on them: follow "Pick up the next PR" in `docs/roadmap/README.md`, and read `docs/roadmap/architecture.md` before any feature work. New work that no spec covers follows Spec Kit from `speckit-specify`. Small fixes skip it and go straight to a test and a change.

## Skills

Listed in `.claude/skills/`; read `SKILL.md` and follow it when the task matches.

| Skill | Use for |
|---|---|
| `new-feature-module` | Adding a feature module to the API |
| `speckit-*` | Spec, plan, tasks, analysis, implementation |
| `pr-generate-description` | Writing a PR description from the branch diff |
| `pr-review` | Reviewing a branch against `main` |
| `robust-error-handling` | Auditing error handling into a remediation plan |
| `implement-error-handling` | Building or fixing failure behavior, or one `EH-Tnn` subtask |

## Commands

From this folder:

```bash
make                   # list every command
make setup             # install both applications
make dev               # Postgres, API on 8020 and web on 3020; Ctrl+C stops all
make test              # API unit tests and web tests, no Docker
make test-api          # all API tests, including integration; needs Docker
make test-web          # web tests only
make check             # everything a pull request must pass; needs Docker
make e2e               # browser checks in Chromium against a production build; needs Docker
make stop              # stop the Postgres that make check leaves running
make reset-db          # delete the local database volume
```

From `applications/temuriset-api/`:

```bash
make install           # uv sync and pre-commit hooks
make run-dependencies  # local Postgres on host port 5442
make migrate           # Alembic migrations
make run               # API on port 8020 with reload
make worker            # outbox and job worker: python -m app.worker
make test-unit         # unit tests, no services needed
make test-integration  # integration tests, needs Postgres
make openapi           # export the API contract to contracts/openapi.json
make check             # lint, format check, all tests, coverage gate
```

From `applications/temuriset-web/`, on the Node version in `.nvmrc`:

```bash
make install           # npm ci
make run               # Next.js dev server on port 3020, forwarding /api/v1 to API_URL
make generate-api      # regenerate the client contract after make openapi
make design            # recopy the design-system stylesheets after a design-system release
make check             # lint, typecheck, tests, coverage gate
make build             # production build
```

## Adding an application

A second Python service: copy `applications/temuriset-api/` without `.venv`, rename it in `pyproject.toml`, change its ports in `Makefile`, `Dockerfile` and `dev-compose.yml`, and add it to the `app` matrix in `.github/workflows/temuriset-api.yml` at the pertanian repository root. Each service keeps its package named `app`, so imports never change.

## Agent rules

- Prefer Makefile targets over raw tool commands.
- Run targeted tests before the full suite.
- Treat a failing bootstrap (no Docker, no network) as an environment blocker, not a product regression.
- Never claim a check passed without running it and reading its output.
- Register every new API data route in `tests/integration/test_isolation.py`; the harness fails until you do.
- Authorize through `app/access/service/policy.py` only: `NOT_FOUND` for what the active party cannot see, `FORBIDDEN` for a missing capability.
- A browser check in jsdom never proves contrast, focus visibility or reflow; say which runtime was exercised.

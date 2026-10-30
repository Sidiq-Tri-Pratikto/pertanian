# Agent Instructions

Read this file before choosing commands or authority sources. It is the single entry point for every coding agent; `CLAUDE.md` imports it.

`.specify/memory/constitution.md` is the authoritative source for project standards. Rules live once in `.claude/rules/`, skills once in `.claude/skills/`. `.cursor/` and `.windsurf/` hold symlinks to them. Never copy a rule; edit the file in `.claude/`.

## Repository layout

| Path | Purpose |
|---|---|
| `applications/<app>/` | One deployable service: code, tests, migrations, Makefile, Dockerfile |
| `applications/<mobile>/` | Expo mobile client: routes, API client, tests, Makefile |
| `contracts/` | Generated API contract shared by service and clients |
| `.specify/` | Constitution, error policy, Spec Kit templates and scripts |
| `specs/<NNN-feature>/` | Feature specs, plans, tasks |
| `docs/error-handling/` | Error catalog, deviations, audits |
| `docs/roadmap/` | Milestones, pick-up steps, binding architecture decisions, traceability |
| `docs/product/` | PRD and design handoff: what the product does |
| `docs/design/` | Design system reference |
| `docs/reference/prototype/` | Browser prototype: oracle source, never production code |

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
| Writing TypeScript or mobile screens | `.claude/rules/009-mobile.md` |

## Workflow

Feature work follows Spec Kit: `speckit-specify`, `speckit-clarify` (when vague), `speckit-plan`, `speckit-tasks`, `speckit-analyze`, `speckit-implement`. Small fixes skip it and go straight to a test and a change.

Specs 003 to 046 are already written. Do not run `speckit-specify` on them: follow "Pick up the next PR" in `docs/roadmap/README.md`. Read `docs/roadmap/architecture.md` before any feature work.

## Skills

Listed in `.claude/skills/`; read `SKILL.md` and follow it when the task matches.

| Skill | Use for |
|---|---|
| `bootstrap-project` | Turning this template into a new project from a requirement |
| `new-feature-module` | Adding a feature module to an application |
| `speckit-*` | Spec, plan, tasks, analysis, implementation |
| `pr-generate-description` | Writing a PR description from the branch diff |
| `pr-review` | Reviewing a branch against `main` |
| `robust-error-handling` | Auditing error handling into a remediation plan |
| `implement-error-handling` | Building or fixing failure behavior, or one `EH-Tnn` subtask |

## Commands

Run from `applications/<service>/`:

```bash
make install           # uv sync and pre-commit hooks
make run-dependencies  # local Postgres via dev-compose.yml
make migrate           # Alembic migrations
make run               # API on port 8000 with reload
make test-unit         # unit tests, no services needed
make test-integration  # integration tests, needs Postgres
make openapi           # export the API contract to contracts/openapi.json
make check             # lint, format check, all tests, coverage gate
```

Run from `applications/<mobile>/`, on the Node version in `.nvmrc`:

```bash
make install           # npm ci
make run               # Metro dev server
make generate-api      # regenerate the client contract after make openapi
make check             # lint, typecheck, tests, coverage gate
make doctor            # expo-doctor
make export            # JavaScript bundles for Android, iOS and web
```


## Adding a second application

1. Copy `applications/<app>/` to `applications/<new-app>/` without `.venv`.
2. Rename the project in its `pyproject.toml` and change its port in `Makefile`, `Dockerfile`, and `dev-compose.yml`.
3. Add `<new-app>` to the `app` matrix in `.github/workflows/ci.yml`.

These steps apply to a Python service. A mobile app comes from `scripts/init.py --mobile`.

Each application keeps its package named `app`, so imports never change.

## Agent rules

- Prefer Makefile targets over raw tool commands.
- Run targeted tests before the full suite.
- Treat a failing bootstrap (no Docker, no network) as an environment blocker, not a product regression.
- Never claim a check passed without running it and reading its output.

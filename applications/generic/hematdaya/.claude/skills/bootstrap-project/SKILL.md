---
name: bootstrap-project
description: Turn this template into a new project from a requirement. Runs scripts/init.py, fills the constitution, removes unused parts, and starts the first spec. Use when starting a new project from this template or when given a product requirement in an uninitialized copy.
---

# Bootstrap Project

Input: the user's requirement. Run this once, in a fresh copy of the template. If `scripts/init.py` is gone, the project is already initialized: stop and use `speckit-specify` instead.

## 1. Understand the requirement

Derive and confirm with the user:

- **Project name** and **first application name**, both lowercase-hyphenated.
- **Is it a mobile product?** Decides `--mobile`, with a mobile application name and a `--bundle-id`. The identifier is permanent once the app is published, so confirm it.
- **One-line description.**
- **Main features** and **out of scope**.
- **Does it store data?** Decides step 3.

Ask only what the requirement does not answer.

## 2. Instantiate

```bash
python scripts/init.py --name <project> --app <app> --description "<one line>" \
  [--mobile <mobile-app> --bundle-id <reverse.domain.id>]
git init -b main
```

Make the first commit before `make install`: its hooks block commits on `main`.

## 3. Remove what the project does not use

Keep the example module until the first real feature exists to copy from, then delete it:

**`app/items/` no longer needed:** delete `app/items/`, `tests/unit/items/`, its router lines in `app/main.py`, its model import in `migrations/env.py`, `migrations/versions/0001_create_items.py` (keep the folder with a `.gitkeep`), and the items tests and `TRUNCATE` setup in `tests/integration/test_api.py`. Then run `make openapi`, plus `make generate-api` in the mobile app. If a local database already ran `0001`, reset it with `docker compose -f dev-compose.yml down -v`. A merged migration can never be edited, so do this before the first merge when the example will not ship.

**No database at all:** remove `app/items/` as above, then, inside `applications/<app>/`:

- Delete `app/core/database.py`, `app/core/errors/database.py`, `migrations/`, `alembic.ini`, `dev-compose.yml`, `tests/integration/`.
- `app/main.py`: remove the database imports, the `lifespan` function and argument, and the `SQLAlchemyError` handler.
- `app/health/router.py`: remove `/ready` and its imports.
- `app/core/settings.py` and `.env.example`: remove `database_url`.
- `app/core/errors/codes.py` and `public.py`: remove the `APP_DB_*` entries.
- `tests/conftest.py`: remove the `DATABASE_URL` default.
- `tests/unit/core/test_errors.py`: remove the database tests and imports.
- `pyproject.toml`: remove `alembic`, `asyncpg`, `sqlalchemy`, and the coverage `concurrency` line, then run `make lock`.
- `Dockerfile`: remove the `alembic.ini` and `migrations` copies. `entrypoint.sh`: remove the migration block.
- `Makefile`: remove `migrate`, `run-dependencies`, `stop-dependencies`.
- `.github/workflows/ci.yml`: remove the `postgres` service and `DATABASE_URL`.
- `docs/error-handling/catalog.md`: remove the `APP-DB-*` rows.
- `AGENTS.md`: remove the matching commands.

After either removal, run `uv run ruff check --fix . && uv run ruff format .` to tidy imports.

## 4. Fill the constitution

In `.specify/memory/constitution.md`:

- Replace every `TODO:` in **Project Overview** from step 1.
- Add a principle only if the requirement demands one that is not there. Do not restate existing ones.
- Set the ratification date in the Sync Impact Report to today.

## 5. Verify

From `applications/<app>/`:

```bash
make install
make run-dependencies   # skip when there is no database
make check
```

With a mobile application, also run from `applications/<mobile-app>/`, on the Node version in `.nvmrc`:

```bash
make install
make check
make doctor
make export
```

A failure here is a bootstrap blocker. Fix it before writing features. Report the output.

## 6. Start the first feature

Hand the requirement to `speckit-specify`. Continue with `speckit-plan`, `speckit-tasks`, `speckit-implement`.

Do not commit or push unless the user asks.

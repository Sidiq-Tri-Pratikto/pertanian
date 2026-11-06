---
name: new-feature-module
description: Scaffold a feature module in an application following rule 005, with router, service, storage, migration, and tests. Use when adding a new feature or resource to an application.
---

# New Feature Module

Input: feature name and its fields or operations.

1. Read `.claude/rules/005-module-structure.md`. Use `app/items/` as the reference if it still exists; otherwise use the most recent feature in `app/`.

2. Create only the layers the feature needs, under `applications/<app>/app/<feature>/`. A feature with no storage has no `repository/`.

3. Write tests first, in `tests/unit/<feature>/`: happy path and failure paths, against a fake repository. See `.claude/rules/003-testing.md`.

4. Build inward to outward: `model/`, `repository/base_repository.py`, `service/service.py`, `repository/sqlalchemy/`, `router.py`.

5. Add failures to the error family, never `HTTPException`: extend `AppError` in `app/core/errors/base.py`, register the code in `codes.py`, map it in `public.py`, and add a row to `docs/error-handling/catalog.md`.

6. Wire it in:
   - Register the router in `app/main.py`.
   - Import the ORM module in `migrations/env.py`.
   - Generate the migration and read it before keeping it:

     ```bash
     uv run alembic revision --autogenerate -m "create <feature>"
     ```

7. Add an integration test through the HTTP interface in `tests/integration/`.

8. Run `make check` and report the output.

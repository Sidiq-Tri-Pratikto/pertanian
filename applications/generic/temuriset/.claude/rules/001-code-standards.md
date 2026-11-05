---
description: Python, FastAPI, and SQLAlchemy code standards. Use when writing or changing Python.
globs: "**/*.py"
alwaysApply: false
trigger: glob
paths:
  - "**/*.py"
---
# Code Standards

## Python

- Python 3.13. Line length 120. Ruff formats and lints; do not hand-format.
- Type hints on all parameters and returns: `str | None`, `dict`, `list`, `tuple`, `set`. Never `Optional`, `Dict`, `List`.
- Absolute imports: `from app.items.service.service import ItemService`.
- Descriptive names. No abbreviations that need decoding.
- Remove duplication when it appears a third time, not before.

## FastAPI

- Pydantic models validate every request and response.
- Inject dependencies with `Depends()`.
- Async route handlers; `await` all I/O.
- Raise errors from the project family in `app/core/errors/`, never `HTTPException` (see `008-error-handling`).
- Document endpoints with `summary` and response models so OpenAPI stays complete.

## SQLAlchemy

- Async engine and session from `app/core/database.py`.
- Declarative models inherit `Base` from the same module.
- Every schema change is an Alembic migration. Never edit a merged migration.
- Avoid N+1 queries; paginate list endpoints.

## Pydantic

- `Field()` for validation and documentation.
- `ConfigDict(from_attributes=True)`, not `class Config`.
- Separate request and response schemas.

## Configuration

- Read settings through `get_settings()` in `app/core/settings.py`. Do not call `os.getenv` elsewhere.
- Add every new setting to `.env.example`.

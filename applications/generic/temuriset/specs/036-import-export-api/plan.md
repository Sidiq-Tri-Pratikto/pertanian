# Implementation Plan: JSON import and export

**Branch**: `036-import-export-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/portability/
├── router.py                     # /imports/validate, /imports/{id}, /imports/{id}/apply, /exports, /exports/{id}
├── service/schema_v1.json        # JSON Schema for import files
├── service/imports.py, service/exports.py
└── repository/sqlalchemy/        # import_runs, external_references, export_jobs
applications/temuriset-web/src/app/inventions/import/page.tsx
migrations/versions/0020_portability.py
```

## Test Plan

AC06, AC61–AC63; schema validation messages; job progress and cancel; isolation.

## Task Outline

1. Schema and validation job.
2. Preview with conflict detection.
3. Apply with external references.
4. Export with gateway; web screen; flip.

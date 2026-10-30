# Implementation Plan: Import preview

**Branch**: `025-import-preview` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/imports/
├── router.py
├── model/schema.py
├── repository/{base_repository.py, sqlalchemy/}
└── service/{preview.py, classify.py}
migrations/versions/0009_create_imports.py
```

## Summary

Stage previews in Postgres and classify every row against the file and stored data.

## API Contract

| Route | Behaviour |
|---|---|
| `POST /api/v1/sites/{site_id}/imports/preview` | Multipart file or text, plus mapping. Returns the preview or questions that need answers |
| `GET /api/v1/imports/{import_id}` | Status, counts, first 50 row errors, assumptions |
| `GET /api/v1/imports/{import_id}/errors?cursor=` | Paged row errors |

Preview response: `total_rows`, `accepted_rows`, `invalid_rows`, `duplicate_rows`, `conflict_rows`, `blocked`, `block_reasons[]`, `needs_acknowledgment`, `mapping`, `assumptions[]`, `period`, `errors[]`.

## Data Model

`imports` and `import_rows` as in `docs/roadmap/architecture.md`. Status: `previewed`, `committing`, `committed`, `rejected`. Previews expire after 24 hours.

## Errors

`APP-IMPORT-TOO-LARGE` (413), `APP-IMPORT-STRUCTURE` (400), `APP-IMPORT-BLOCKED` (409), each with an Indonesian correction.

## Prototype Reference

`buildPreview`, `defaultMapping`, `mappingIssues`; tests AT-30, AT-33/34.

## Test Plan

Reconciliation; thresholds; duplicates in file and against stored; conflicts; same-name assets; other-source target; unknown overlap; expiry; no measurement change; foreign site; injection-looking names stored verbatim.

## Out of Scope

Commit (026), screens (027).

## Task Outline

1. Migration.
2. Classification with tests.
3. Preview service.
4. Router with limits.
5. Contract.

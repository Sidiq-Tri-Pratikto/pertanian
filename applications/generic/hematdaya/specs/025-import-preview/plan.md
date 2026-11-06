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
| `GET /api/v1/imports/{import_id}` | Status, counts, first 50 row errors, next error cursor, assumptions |
| `GET /api/v1/imports/{import_id}/errors?cursor=` | Paged row errors |

Preview response fields include `total_rows`, `accepted_rows`, `invalid_rows`, `duplicate_rows`, `conflict_rows`, `blocked`, `block_reasons[]`, `needs_acknowledgment`, `mapping`, `assumptions[]`, `period`, the first 50 `errors[]`, and `next_error_cursor` when more errors exist. Error pagination is ordered by data row and bounded by the API list limit. Counts always cover the full file.

## Data Model

`imports` and `import_rows` follow [the architecture](../../docs/roadmap/architecture.md). Store `previewed`, `committed`, or `rejected` as the last confirmed state. Uncommitted previews expire after 24 hours. Record the normalized source mapping and the site's `measurement_revision` and `binding_revision` from the same snapshot used for classification. Revalidate against these revisions at commit.

## Classification

Group by resolved source. Classify exact repeats and changed values at the same identity separately. Check each candidate interval for non-identical overlaps within the file and against accepted stored intervals. An unresolved overlap blocks commit. Adjacent intervals do not overlap. Resolve duplicate or conflicting counter points before deriving adjacent deltas. Classify each nonblank data row once. Block files with neither usable rows nor duplicates. A duplicate-only reimport reports zero new rows and does not create assets, sources, or bindings.

## Errors

`APP-IMPORT-TOO-LARGE` (413), `APP-IMPORT-STRUCTURE` (400), `APP-IMPORT-BLOCKED` (409), each with an Indonesian correction.

## Prototype Reference

`buildPreview`, `defaultMapping`, `mappingIssues`; tests AT-30, AT-33/34.

## Test Plan

- Reconciliation, thresholds, duplicates in file and against stored, duplicate-only reimport.
- No usable rows, non-identical interval overlaps in-file and against stored data, adjacent intervals, duplicate counter points.
- Error pagination across the inline limit, same-name assets, other-source target, unknown overlap.
- Expiry, no measurement change, foreign site, injection-looking names stored verbatim.

## Out of Scope

Commit (026), screens (027).

## Task Outline

1. Migration.
2. Classification with tests.
3. Preview service.
4. Router with limits.
5. Contract.

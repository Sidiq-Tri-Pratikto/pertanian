# Implementation Plan: Import commit

**Branch**: `026-import-commit` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/imports/service/commit.py
tests/integration/test_import_commit.py
```

## Summary

One transactional commit, with status lookup and idempotent replay.

## API Contract

`POST /api/v1/imports/{import_id}/commit` with `Idempotency-Key` and `{acknowledge_skipped}`. Returns the result. Repeat returns the same result with `replayed: true`.

## Design

`SELECT … FOR UPDATE` on the import row, check status and staleness, ingest through `IngestService` with staged rows, set `committed`, write audit, commit via `SessionDep`. A timeout after commit is recovered by `GET /imports/{id}`. No background worker for v1; if the benchmark exceeds the target, 041 records it and a worker becomes its own spec.

## Prototype Reference

`applyImport`, `commitImport`, `checkOperation`; test AT-33/34.

## Test Plan

Atomic rollback with injected failure; replay; concurrent commit; stale preview; blocked preview; acknowledgment required; counter reset; insight revision; audit; result counts equal rows.

## Out of Scope

Screens (027), background processing.

## Task Outline

1. Failing atomicity tests.
2. Commit service.
3. Status and replay.
4. Recompute hook into insights.
5. Flip `csv` adapter.

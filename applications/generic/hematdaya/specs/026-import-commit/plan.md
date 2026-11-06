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

Authorize the import through the acting principal. Acquire the shared site row lock from 005 and 006, then lock the import row for same-ID replay. For a new commit, recheck the site's `measurement_revision` and `binding_revision` and the overlap classifications from 025. The lock spans revalidation and writes, so another import ID cannot change the affected data between them. Reject stale previews before any writes.

Ingest through `IngestService` with the same session. Write the data and audit, and mark the affected insight identities and periods invalid. Store the result and set the status to `committed` in the same transaction, committed by `SessionDep`. The read path from 021 evaluates invalidated observations before returning active evidence. A duplicate-only result records completion and an audit outcome with no affected period, without changing domain data. Replaying the same operation returns its first result without side effects. Reject reuse of a key for a different operation or acceptance payload.

If the response is lost, `GET /imports/{id}` retrieves the committed result or the last confirmed state. An in-flight transaction does not publish a separate `committing` status. If the operation remains unresolved, retry with the same key. No background worker for v1. If the benchmark exceeds the target, 041 records it and a worker becomes its own spec.

## Prototype Reference

`applyImport`, `commitImport`, `checkOperation`; test AT-33/34.

## Test Plan

- Atomic rollback with injected failure, same-ID concurrent replay, distinct import IDs with conflicting source intervals or bindings, unchanged earlier data on stale or blocked preview.
- Acknowledgment required, key reused with a different payload, duplicate-only reimport, counter reset.
- Invalidated insight re-evaluated on next read, audit, result counts equal rows, foreign import IDs.

## Out of Scope

Screens (027), background processing.

## Task Outline

1. Failing atomicity tests.
2. Commit service.
3. Status and replay.
4. Record insight invalidation atomically and verify re-evaluation on read.
5. Flip `csv` adapter.

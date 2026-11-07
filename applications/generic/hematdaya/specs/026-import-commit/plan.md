# Implementation Plan: Import commit

**Branch**: `m5/import-commit` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/imports/
├── router.py                                     # POST /imports/{import_id}/commit, and result on GET
├── dependencies.py                               # ImportCommitServiceDep
├── model/{models.py, schema.py}                  # commit_result, the commit request and responses
├── repository/{base_repository.py, sqlalchemy/}  # get_import_locked, find_by_key, accepted_page, mark_committed
└── service/
    ├── commit.py                                 # ImportCommitService
    ├── commit_plan.py                            # Pure rules: streams, readings, ranges, staleness, totals
    ├── errors.py                                 # Three errors
    ├── mapping.py                                # source_label over 120 characters
    ├── classify.py                               # MAX_IMPORT_STREAMS and its block reason
    └── preview.py                                # Insert before purge, and the stream count
app/assets/service/service.py and repository/     # add_binding gains effective_to (P1)
app/audit/dependencies.py                         # build_audit_service (P1)
app/capabilities/service/service.py               # csv becomes available (P1)
app/core/errors/{codes.py, public.py}
migrations/versions/0009_add_import_commit_result.py
docs/error-handling/catalog.md
contracts/openapi.json
../hematdaya-mobile/src/api/schema.generated.ts
.github/workflows/hematdaya-api.yml               # At the pertanian repository root
README.md
tests/unit/imports/{test_commit_plan.py, test_import_errors.py, test_mapping.py, test_classify.py, test_contract.py}
tests/unit/capabilities/test_capabilities.py
tests/integration/{test_import_commit.py, test_import_performance.py, test_import_storage.py}
tests/integration/{test_import_preview.py, test_assets.py, test_isolation.py, conftest.py}
```

## Summary

One transactional commit, with status lookup and idempotent replay.

## API Contract

| Route | Behaviour |
|---|---|
| `POST /api/v1/imports/{import_id}/commit` | Required header `Idempotency-Key`, pattern `^[A-Za-z0-9_-]{22,128}$`. Body `{"acknowledge_skipped": false}`, extra fields forbidden. 200 with `ImportCommitResponse`. A repeat returns the first result with `replayed: true` |
| `GET /api/v1/imports/{import_id}` | Gains `result`: null until committed, then the first result. It takes no lock |

Result fields:

| Field | Meaning |
|---|---|
| `import_id`, `status` | The import, and `committed` |
| `rows_added`, `rows_skipped`, `rows_duplicate` | Rows stored, invalid rows acknowledged, and exact repeats |
| `assets_created`, `assets_mapped` | Each `{id, name}`, in stream order |
| `period` | `{start_date, end_date, timezone}` from the affected range, or null when nothing changed |
| `affected_from`, `affected_to` | UTC bounds of the changed data, including replaced counter deltas, or null |
| `rows_after_site_clock` | Accepted rows ending after `site_clock(site)` at commit |
| `acknowledge_skipped` | What the first request sent |
| `committed_at` | Wall-clock time |
| `replayed` | On the POST response only: false for the first result, true for a repeat |

Fields US3 fills (`assets_created`, `assets_mapped`, `period`, `affected_from`, `affected_to`, `rows_after_site_clock`) have defaults in the schema, and the response always includes them.

## Data Model

Migration `0009_add_import_commit_result.py`, `down_revision = "0008"`. `0008`'s `idempotency_key`, its unique index and the `committed` status already exist. Merged migrations are never edited.

```sql
ALTER TABLE imports ADD COLUMN commit_result jsonb;
ALTER TABLE imports ADD CONSTRAINT imports_commit_result
    CHECK ((status = 'committed') = (commit_result IS NOT NULL)) NOT VALID;
ALTER TABLE imports ADD CONSTRAINT imports_commit_key
    CHECK (status <> 'committed' OR idempotency_key IS NOT NULL) NOT VALID
```

`NOT VALID` enforces both rules on every new write and skips existing rows. It is needed because 025's tests leave `committed` rows with no result in the shared development database, and a downgrade to `0008` and back would do the same. A plain constraint would stop those upgrades. Downgrade drops both constraints and the column.

The ORM column is `JSONB(none_as_null=True)`, because JSON null would pass the CHECK as a result. Staged rows stay after a commit. Retention belongs to 038.

## Design

**Locks.** Read the import with no lock, for its `site_id` only. Acquire the shared site row lock from 005 and 006 through `lock_owned`, so a foreign site answers `NOT_FOUND` with no lock taken. Then lock the import row with `populate_existing`, because the session's identity map would otherwise return the state from before the wait. The lock spans revalidation and writes, so another import ID cannot change the affected data between them.

**Preview order.** A preview must insert its import before purging, because a foreign key check takes `FOR KEY SHARE` on the site row. Purging first deadlocks with a commit. This changes 025's code, and it is reproduced in tasks.md's Notes.

**Gate.** Before any write, in this order: the key cases, replay when committed, `require_committable`, expiry by `wall_now()`, equality of both revisions and the timezone, then acknowledgment. Equal revisions mean the stored data is what the preview read, so rows are not classified again. tasks.md holds the full table of key cases. A refused attempt stores nothing, so its key stays free.

**Apply.** Ingest through `IngestService` with the same session. Read `import_rows.parsed` in pages of 5,000 and build `ReadingInput` from `value`, never `raw_value`. Interval kinds go through one `ingest` per 5,000 rows, and each counter stream through one `ingest`, because `_rederive_counter` runs per call. Only streams with accepted rows create anything.

**Assets, sources, bindings, relations.** New assets use `ScopeKind.DEVICE`. New sources use `mapping`'s label, `origin = import`, `transport_status = historical` and no resolution. Each uncovered part of the accepted rows' span gets one authoritative binding, ending at the next binding's start or left open. `scope` writes its relation for each pair of the file's assets that `scope_issues` reports as `unconfirmed`. Advance `binding_revision` once when anything was created.

**Finish.** Check that `IngestResult` agrees with the preview, and raise `APP-UNKNOWN` and roll back if not. Write one audit event, store the result and set `committed` in the same transaction, committed by `SessionDep`. A duplicate-only result records completion and an audit outcome with no affected period, without changing domain data.

**Insights.** No invalidation operation. Every insight read path calls `InsightService.evaluate`, which takes the site lock, recomputes and publishes a new revision only when the evidence hash changed, keeping the old one. The commit holds the same lock and advances `measurement_revision` with its data, so the next read cannot return evidence from before it. Imported sources have unknown resolution, so a period served only by imported data stays descriptive and never publishes an observation.

**Status.** If the response is lost, `GET /imports/{id}` retrieves the committed result or the last confirmed state. An in-flight transaction does not publish a separate `committing` status. Retrying with the same key waits on the lock and replays. No background worker for v1. If the benchmark exceeds the target, 041 records it and a worker becomes its own spec.

Decisions and their evidence are in [tasks.md](tasks.md).

## Errors

| Code | Public | HTTP | Recovery | Trigger |
|---|---|---|---|---|
| `APP-IMPORT-BLOCKED` | `IMPORT_BLOCKED` | 409 | Not retryable | Commit of a blocked preview. Registered by 025, first reached here |
| `APP-IMPORT-STALE` | `IMPORT_STALE` | 409 | Not retryable | Expired preview, or a changed revision or timezone. `details[0].type` says which |
| `APP-IMPORT-ACK-REQUIRED` | `IMPORT_ACK_REQUIRED` | 409 | Not retryable | Skipped rows not acknowledged |
| `APP-IMPORT-KEY-CONFLICT` | `CONFLICT` | 409 | Not retryable | Key used for another import, or with a different acknowledgment |

Exact messages are in `tasks.md`. Specifics travel in `details`, because `handle_app_error` drops a custom `message`. That is P1's item, and 026 neither depends on it nor fixes it. 026 never writes `rejected`, because a refusal rolls back.

## Composition and ownership

Import is core, so no route calls `CapabilityGuard`, and the tests also run under `COMPOSITION=core-only`. A foreign import answers `NOT_FOUND`, and the route joins `FOREIGN_ROUTES` in `test_isolation.py`. `app/imports/` imports no other module's repository, which `test_module_boundary.py` enforces.

## Prototype Reference

`applyImport`, `commitImport`, `checkOperation`; test AT-33/34.

## Test Plan

- Atomic rollback with injected failure, same-ID concurrent replay, distinct import IDs with conflicting source intervals or bindings, unchanged earlier data on stale or blocked preview, and a commit racing a preview purge.
- Acknowledgment required, key reused with a different payload, duplicate-only reimport, counter reset, and appending to a stored counter.
- Bindings for earlier rows, for a later binding, after a closed binding, and on append. Relations for `disjoint`, `unknown_overlap`, existing pairs and pairs outside the file.
- Next insight read after commit: a descriptive path reachable in production, and a revision path on a stored source with known resolution. Audit, result counts equal rows, foreign import IDs, rows after the site clock.
- Every failure path: message, code, details, `request_id`, record, recovery and fake secrets.
- The migration, including downgrade and single head. `core-only`. The contract shape. The flip.

## Performance

Target: PRD §18's 60 seconds covers validation and commit on the benchmark server, which 041 measures. Evidence before implementation, on a commit-shaped script (tasks.md Notes): 9.43 s for 150,000 interval rows and 21.23 s for 150,000 counter rows, on an Apple M3 with Postgres 17 in local Docker, plus about 9 to 10 s of preview. Through the routes, on that same machine (T053): preview plus commit took 18.93 s for 150,000 interval rows (commit 9.30 s, 37.7 MiB peak), 29.60 s for counters (commit 20.62 s, a 2.06 s stall, 938.7 MiB peak), and 23.01 s for 100 streams (commit 13.92 s, 210.9 MiB peak). All are under 60 s here, and 041 still owes the formal number.

## Handoff to 027

- A timeout is an unknown result, not a failure. Call `GET /imports/{id}`. If it says `previewed`, retry with the same key. The client's `TIMEOUT_MS` is 10 s, and a large commit can take longer.
- Branch on the public code. `IMPORT_ACK_REQUIRED` links to the checkbox, `IMPORT_STALE` leads back to a new preview, `IMPORT_BLOCKED` shows the preview's reasons, and `CONFLICT` needs a new key.
- Render `rows_after_site_clock` when it is above zero. See Open questions in tasks.md, item 1.
- `HDProvenanceTag` shows `Data impor`. The spec's text is `Data historis · Impor CSV`.
- The first-reading assumption can be wrong on an append to a stored counter. Totals are right.
- Flip `impor-data` to `available`.

## Out of Scope

Screens and copy (027), background processing, per-principal rate limits (036), retention of staged rows (038), changing spec 008's clock, and replacing a source's authority or confirming scope across files (028).

## Task Outline

1. Failing atomicity tests.
2. Commit service.
3. Status and replay.
4. Prove with tests that the next insight read reflects a commit and keeps earlier revisions. No invalidation code.
5. Flip `csv` adapter.

# Implementation Plan: Import preview

**Branch**: `m5/csv-parser` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/imports/
├── router.py
├── dependencies.py
├── model/{models.py, schema.py}      # models.py comes from 024; this adds ImportStatus, ImportModel, ImportRowModel
├── repository/{base_repository.py, sqlalchemy/}
└── service/{preview.py, classify.py, mapping.py, assumptions.py, errors.py}
app/measurements/service/service.py and repository/   # two read methods
app/core/errors/{base.py, handlers.py, codes.py, public.py}
app/main.py, migrations/env.py, pyproject.toml, uv.lock
migrations/versions/0008_create_imports.py
docs/error-handling/{catalog.md, deviation.md}
contracts/openapi.json
../hematdaya-mobile/src/api/schema.generated.ts
.github/workflows/hematdaya-api.yml                   # at the pertanian repository root
tests/unit/imports/, tests/unit/core/test_errors.py
tests/integration/{test_import_preview.py, test_import_storage.py, test_import_performance.py}
tests/integration/{test_isolation.py, test_measurements.py, conftest.py}
```

## Summary

Stage previews in Postgres and classify every row against the file and stored data, using 006's own rules.

## API Contract

| Route | Behaviour |
|---|---|
| `POST /api/v1/sites/{site_id}/imports/preview` | Multipart: `file` part or `text` field, plus `mapping` as JSON text. Returns 201 with the stored preview, including questions that need answers |
| `GET /api/v1/imports/{import_id}` | Status, counts, first 50 row errors, next error cursor, assumptions |
| `GET /api/v1/imports/{import_id}/errors?cursor=&limit=` | Paged row errors, `limit` from 1 to 100, default 50 |

The POST route takes `Request`, not `UploadFile`, because FastAPI parses declared forms before dependencies. It resolves the owned site first, then wraps `receive` with a counter capped at 10 MiB + 64 KiB, then calls `form(max_part_size=...)`. `openapi_extra` documents the body. This needs `python-multipart`, a new dependency justified in the PR.

Mapping request: `value_kind`, `power_meaning`, `timezone_confirmed`, `interval_minutes` (by stream key), `asset_map` (asset name to asset ID or `"new"`), `scope` (`disjoint` or `unknown_overlap`).

Preview response fields include `id`, `status`, `file_name`, `expires_at`, `total_rows`, `accepted_rows`, `invalid_rows`, `duplicate_rows`, `conflict_rows`, `pending_rows`, `blocked`, `block_reasons[]`, `needs_acknowledgment`, `questions[]`, `mapping`, `assumptions[]`, `period`, the first 50 `errors[]`, and `next_error_cursor` when more errors exist. `status` is the stored status, or `expired` when an uncommitted preview has passed `expires_at`. A question carries `kind`, `message`, `streams[]`, `asset_name` and, for a name shared by assets, `candidates[]` with `id`, `name`, `location`, `category` and `scope_kind`. `period` carries `start_date`, `end_date` and `timezone`. Error pagination is ordered by data row and bounded by the API list limit. Counts always cover the full file.

## Data Model

`imports` and `import_rows` follow [the architecture](../../docs/roadmap/architecture.md). Migration `0008_create_imports.py`, `down_revision = "0007"`. `tests/unit/core/test_migrations.py` requires a single Alembic head, so a parallel migration that merges first means taking the next number and re-pointing `down_revision`.

```sql
CREATE TABLE imports (
    id uuid PRIMARY KEY,
    site_id uuid NOT NULL REFERENCES sites ON DELETE CASCADE,
    status text NOT NULL CHECK (status IN ('previewed', 'committed', 'rejected')),
    file_name text NOT NULL CHECK (char_length(file_name) BETWEEN 1 AND 255),
    content_sha256 text NOT NULL,
    mapping jsonb NOT NULL,
    total_rows integer NOT NULL,
    accepted_rows integer NOT NULL,
    invalid_rows integer NOT NULL,
    duplicate_rows integer NOT NULL,
    conflict_rows integer NOT NULL,
    pending_rows integer NOT NULL,
    blocked boolean NOT NULL,
    block_reasons jsonb NOT NULL,
    needs_acknowledgment boolean NOT NULL,
    questions jsonb NOT NULL,
    assumptions jsonb NOT NULL,
    period_start timestamptz,
    period_end timestamptz,
    measurement_revision bigint NOT NULL,
    binding_revision bigint NOT NULL,
    idempotency_key text,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT imports_counts_reconcile CHECK (
        accepted_rows + invalid_rows + duplicate_rows + conflict_rows + pending_rows = total_rows
    )
);
CREATE UNIQUE INDEX ux_imports_site_idempotency ON imports (site_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;
CREATE INDEX ix_imports_site_created ON imports (site_id, created_at);
CREATE INDEX ix_imports_expiry ON imports (expires_at) WHERE status = 'previewed';
CREATE TABLE import_rows (
    import_id uuid NOT NULL REFERENCES imports ON DELETE CASCADE,
    data_row integer NOT NULL,
    file_line integer NOT NULL,
    status text NOT NULL CHECK (status IN ('accepted', 'invalid', 'duplicate', 'conflict')),
    reason text,
    field text,
    message text,
    parsed jsonb,
    PRIMARY KEY (import_id, data_row),
    CONSTRAINT import_rows_message CHECK ((status IN ('invalid', 'conflict')) = (message IS NOT NULL))
);
CREATE INDEX ix_import_rows_errors ON import_rows (import_id, data_row) WHERE status IN ('invalid', 'conflict');
```

`previewed`, `committed` and `rejected` are the last confirmed state. 025 writes only `previewed`, and 026 writes the others. Pending rows are counted, not staged. `parsed` is stored for accepted rows only. `mapping` holds `value_kind`, `power_meaning`, `timezone`, `timezone_confirmed`, `interval_minutes`, `scope`, `columns` (asset, time and value headers with units) and `streams[]`, each with `stream_key`, `label`, `asset_name`, `asset_id`, `source_id`, `kind`, `unit`, `cadence_seconds`, `period_start`, `period_end` and `interval_basis`.

Read the site's `measurement_revision` and `binding_revision` first, before the asset snapshot and stored rows, with no lock. A request runs at READ COMMITTED, so its reads share no snapshot. Reading revisions first means a write that lands during classification leaves an older revision behind, and revalidation at commit refuses it. Uncommitted previews expire after 24 hours by `wall_now()`. Each new preview deletes up to 20 expired uncommitted imports anywhere and keeps the newest 5 uncommitted per site. Per-principal rate limits belong to 036.

## Classification

**Reads.** `IngestService` gains `current_rows(source_id, identity_keys)` and `stored_intervals(source_id, start, end)`, so `app/imports/` never imports another module's repository. Parsing and staging run through `asyncio.to_thread`. A thread cannot be cancelled, so the byte and row caps bound that work in place of a parsing timeout.

**Identity.** Build `ReadingInput` from `RowResult.value` and `unit`, with `source_record_id=None`, and call 006's `normalize` with `MeasurementKind(row.kind.value)`. The returned `identity_key` is the identity. `MeasurementRow.same_observation` decides "same", so `raw_value` and `raw_unit` count as well as `energy_mwh`, and a preview duplicate cannot become a revision at commit. Stored energy is integer mWh in BIGINT, so `energy_mwh` above `2**63 - 1` makes the row invalid.

**Source resolution.** `sources` has no stream column, so a stream reaches its stored source through its target asset and a fixed label, `Impor CSV · {stream_key}`. A source matches when it is bound to the target asset, has `origin = import`, the row's kind and that label. A `new` target has no stored source. Any other source whose binding overlaps the stream's period raises `other_source`. Bindings closed before the period do not count. Stream and asset must be one to one.

**Order.** Group by resolved source. Classify exact repeats and changed values at the same identity separately. Check each candidate interval for non-identical overlaps within the file and against accepted stored intervals. `measurements` has no exclusion constraint, so overlapping intervals with different identities would both be stored and summed: this check is the only guard, and it blocks commit. Adjacent intervals do not overlap. Precedence per group: invalid, in-file changed value, in-file overlap, stored changed value, stored overlap, stored exact repeat, then accepted first and duplicates after. Resolve duplicate or conflicting counter points before deriving adjacent deltas. Points take no part in overlap. Classify each nonblank data row once. Block files with neither usable rows nor duplicates. A duplicate-only reimport reports zero new rows and does not create assets, sources, or bindings. A one-row counter file is accepted as an anchor, with its assumption.

**Thresholds.** `invalid * 5 <= total` in integers. `needs_acknowledgment` is `invalid > 0 and not blocked`.

## Errors

| Code | Public | HTTP | Recovery | Trigger |
|---|---|---|---|---|
| `APP-IMPORT-TOO-LARGE` | `IMPORT_TOO_LARGE` | 413 | Not retryable | Body over the cap, or 024's `too_large` or `too_many_rows` |
| `APP-IMPORT-STRUCTURE` | `IMPORT_INVALID` | 400 | Not retryable | Any other 024 structural reason |
| `APP-IMPORT-BLOCKED` | `IMPORT_BLOCKED` | 409 | Not retryable | Commit of a blocked preview. Registered here, raised from `require_committable`, reached from a route in 026 |

Default messages are in `tasks.md`. Register each in `codes.py`, `public.py` and `docs/error-handling/catalog.md`, with typed errors in `app/imports/service/errors.py`. The specific Indonesian correction travels in `error.details` (`loc`, `msg`, `type`), because `handle_app_error` renders only the catalog message. Add an optional `details` attribute to `AppError`, pass it in that handler, and widen the EH-07 deviation. Details hold alias headers, line numbers and sizes, never a CSV value. A blocked preview is a normal 201 response. Row messages may echo the user's own cell in their own preview, and they never reach logs.

## Composition and ownership

Import is core, so no route calls `CapabilityGuard`, and the tests also run under `COMPOSITION=core-only`. The manifest's `csv` adapter stays `planned` until 026. Foreign sites and imports return `NOT_FOUND` before any body is read, and all three routes join `FOREIGN_ROUTES` in `test_isolation.py`.

## Prototype Reference

`buildPreview`, `defaultMapping`, the asset and scope part of `mappingIssues` (L722–L733), `fmtDateTime`, `fmtGap`; tests AT-30, AT-33/34 (L276–L280), AT-27a's `blocked`, AT-27b's assumption text and AT-32's invalid count.

## Test Plan

- Reconciliation, thresholds, duplicates in file and against stored, duplicate-only reimport.
- No usable rows, non-identical interval overlaps in-file and against stored data, adjacent intervals, duplicate counter points, jittered timestamps.
- Error pagination across the inline limit, same-name assets, other-source target, unknown overlap, one stream with two assets, two streams on one asset.
- Expiry, the per-site cap, no measurement change, foreign site, foreign import, foreign asset in the mapping, injection-looking names stored verbatim.
- Every failure path: 413 at the parser limit and at the body cap, 400 for structure, 422 for a bad mapping, with message, code, details, `request_id`, record, recovery and fake secrets.
- The migration, including downgrade and single head. Demo end and reset. `core-only`. The contract shape.

## Performance

Target: PRD §18's 60 seconds covers validation and commit on the benchmark server, which 041 measures. Measured 2026-11-07 for the preview alone, through the route with Postgres 17 in local Docker, on an Apple M3 with 16 GiB, Darwin 27.2.0, Python 3.13.16: 8.72 s for 150,000 explicit-interval rows (9,450,044 bytes), and a `tracemalloc` peak of 156.6 MiB (31.82 s under tracing), against the 256 MiB bound. Commit is not included, so this is not a measurement of the PRD target.

## Handoff to 026

The preview stores everything below, so 026 needs no re-parse.

- **Row data.** `import_rows.parsed` for `accepted` rows: `stream_key`, `asset_name`, `kind`, `unit`, `value` (canonical string), `identity_key`, `interval_start`, `interval_end`, `measured_at` (UTC), `raw_value`, `raw_start`, `raw_end`. Build `ReadingInput` from `value`, never from `raw_value`, or a reimport becomes a revision.
- **Validation inputs.** `measurement_revision`, `binding_revision`, `content_sha256`, `blocked`, `needs_acknowledgment`, `expires_at`, and `mapping`. Call `require_committable` first.
- **Idempotency.** `idempotency_key` is created empty and is unique per site. 026 adds its own column for the stored result.
- **Assets.** Create new ones with `ScopeKind.DEVICE`, as the prototype does (L831).
- **Sources.** Create with `label` from `source_label(stream_key)`, `origin = import`, `transport_status = historical` and the stream's `cadence_seconds`. Keep the label format, or reimports stop matching.
- **Counters.** `cadence_seconds` is null, so 006's `counter_deltas` assumes one hour and flags any delta over two hours as `long_gap`. That is conservative, not wrong: totals still hold.
- **Bindings.** `effective_from` must be at or before the stream's earliest row, or the read path finds no valid binding for those intervals. A reimport with earlier rows needs another binding. An open-ended authoritative binding collides with any later authoritative one, so end it at that binding's start.
- **Scope.** `scope_issues` adds assets only with a `disjoint` relation, so `scope = disjoint` must write `RelationKind.DISJOINT` for each pair. The prototype writes nothing there (L842), and copying that would refuse every total. `unknown_overlap` writes `UNKNOWN_OVERLAP`.
- **Blocking code.** `APP-IMPORT-BLOCKED` first reaches a route in 026. Stale previews need their own decision there.
- **Insights.** 026's FR-004 and 021's plan describe an invalidation operation, but `app/insights` has none: it evaluates on every read under the site lock, so a commit that advances `measurement_revision` is picked up on the next read. The preview stores nothing for this, because `IngestResult.affected_from` and `affected_to` give the range. 026 must reconcile its spec with this code.
- **Provenance.** Pass `import_id`, `file_name` and the timezone assumption to `ingest(..., provenance=...)`, per PRD §10.1.

## Out of Scope

Commit (026), screens (027), per-principal rate limits (036), replacing a source's authority (028).

## Task Outline

1. Errors with details.
2. Migration and repository.
3. Measurement reads.
4. Classification with tests.
5. Preview service.
6. Router with limits.
7. Mapping by identity.
8. Contract.

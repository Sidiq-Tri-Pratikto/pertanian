# Implementation Plan: Measurements

**Branch**: `006-measurements` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

The normalized store and one internal ingestion service. No public write route: CSV (026), demo (008) and adapters (046) call this service.

## Technical Context

**Storage**: Postgres `measurements`, bulk insert with `ON CONFLICT`
**Testing**: pure unit tests for normalization; integration for identity and concurrency

## Constitution Check

Unknown is never zero: no row means no data. The rule lives here so no adapter can bypass it.

## Project Structure

```text
app/measurements/
├── model/models.py                 # MeasurementModel, kinds, quality
├── repository/{base_repository.py, sqlalchemy/}
└── service/
    ├── normalize.py                # pure: interval, average power, counter segments
    └── service.py                  # IngestService.ingest(batch) -> IngestResult
app/core/types.py                   # DecimalString: string-only Pydantic type
migrations/versions/0004_create_measurements.py
```

## Data Model

```sql
measurements(id bigint generated always as identity pk, source_id uuid references sources not null,
  source_record_id text, kind text not null, interval_start timestamptz, interval_end timestamptz,
  measured_at timestamptz, energy_mwh bigint check (energy_mwh >= 0), raw_value text, raw_unit text,
  counter_segment int, received_at timestamptz not null, quality text not null, revision int not null default 1,
  check (interval_end > interval_start))
```

Unique on `(source_id, kind, interval_start, interval_end, revision)`, plus partial unique on `(source_id, source_record_id, revision)`. Index `(source_id, interval_start)`.

## Contract

`IngestResult`: `added`, `repeated`, `revised`, `rejected[]`, `affected_from`, `affected_to`. Revisions use the highest revision per identity at query time, through a view `current_measurements`.

## Errors

Invalid readings return structured rejections to the caller. They are diagnostics, not stored as valid data (FR-05 quarantine).

## Prototype Reference

`parseDecimal`, the counter handling in `buildPreview`, `assetSlice`. Tests AT-27a, AT-27b in `domain.test.js`.

## Test Plan

Port AT-27a and AT-27b. Add: idempotent repeat, revision, late reading range, reset, long counter gap flag, negative, non-finite, `end <= start`, float rejected by `DecimalString`, 10,000-row batch.

## Out of Scope

Summaries (009), CSV parsing (024), live adapters.

## Task Outline

1. `DecimalString` and tests.
2. Pure normalization with oracles.
3. Migration and `current_measurements` view.
4. Repository bulk insert.
5. `IngestService`.
6. Integration tests.

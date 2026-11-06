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
  created_at timestamptz not null)
```

Require both ordered UTC bounds for interval inputs and a capture time for point inputs. Keep raw counter points distinct from the derived interval deltas. A point cannot carry interval energy.

Use disjoint partial unique keys for raw revisions: `(source_id, source_record_id, revision)` when the capture ID exists, `(source_id, kind, interval_start, interval_end, revision)` for fallback interval identity, and `(source_id, kind, measured_at, revision)` for fallback point identity. Check the key fields are non-null for their row type. Index `(source_id, interval_start)` for interval reads and source/capture time for adjacent counter lookup. Derive current deltas from current neighboring counter points or replace their versioned derived rows in the same transaction. A displaced interval must leave the current read view.

## Contract

`IngestResult`: `added`, `repeated`, `revised`, `rejected[]`, `affected_from`, `affected_to`. The `current_measurements` view uses the same identity precedence as ingestion and shows only the active revision. Take 005's shared site write lock before allocating revisions and changing adjacent deltas. Import orchestration that holds the lock calls ingestion in the same transaction and session. Increment the site's monotonic `measurement_revision` once per committed change, leaving it unchanged on a repeat or rollback. For late or corrected counters, return the union of old and new affected intervals and preserve the raw history, reset and long-gap flags.

Convert exact decimal inputs to integer mWh once using nearest mWh with ties to even. Keep the raw decimal value and unit so the conversion is reproducible. Resolve owner, site and asset from the source and effective bindings. Preserve the original import timezone or offset assumption with the ingest provenance rather than trusting a site or asset ID from the payload.

## Errors

Invalid readings return structured rejections to the caller. They are diagnostics, not stored as valid data (FR-05 quarantine).

## Prototype Reference

`parseDecimal`, the counter handling in `buildPreview`, `assetSlice`. Tests AT-27a, AT-27b in `domain.test.js`.

## Test Plan

Port AT-27a and AT-27b. Test replay and concurrent delivery for ID-based, fallback interval and fallback point identities. Test a corrected or inserted middle counter reading replacing both neighboring delta ranges, reset, long counter gap flag, negative, non-finite, missing or reversed bounds, fractional-mWh conversion, JSON numbers rejected by `DecimalString`, and a 10,000-row batch.

## Out of Scope

Summaries (009), CSV parsing (024), live adapters.

## Task Outline

1. `DecimalString` and tests.
2. Pure normalization with oracles.
3. Migration and `current_measurements` view.
4. Repository bulk insert.
5. `IngestService`.
6. Integration tests.

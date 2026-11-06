# Implementation Plan: Demo fixtures

**Branch**: `007-fixtures` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Port the fixture generator from the prototype to pure Python. No HTTP and no sessions yet.

## Project Structure

```text
app/demo/
├── fixtures.py                     # HOUSEHOLD, FACTORY definitions, generate()
└── scenarios.py                    # SCENARIOS catalog, build_scenario()
tests/unit/demo/test_fixtures.py
```

## Constitution Check

Test-first: the oracles are the tests, written before the generator.

## Design

`generate(definitions, variant) -> Iterable[ReadingSpec]` yields interval readings with asset/source keys, UTC bounds and integer Wh. `build_scenario(id) -> ScenarioPlan` also returns the timezone, source resolution and provenance, virtual now, initial period, optional inputs, relations and flags, with no database access. Seeding through 006 ingestion belongs to 008. Optional input fixtures stay declarative until their tables arrive in 018, 030 and 032.

Scenario quirks to keep from the prototype. The learning scenario starts 12 October, Pompa Air stops 24 October, Kulkas gap 22 October 14.00–16.00. The stale scenario ends Router at 25 October 18.00 and marks its transport simulated-live. The scope scenario adds Meter utama containing Kulkas, Router and TV, a second Kulkas source, and unknown overlap with Pompa Air. For historical/offline, retain the historical date range, input timezone and the simulated-fixture label. Assign imported origin only to records actually handled by the CSV path.

## Prototype Reference

`HOUSE`, `FACTORY`, `SCENARIOS`, `buildScenario`, `pushHourly`, `buildScopeExtras`, `inWeek` in `hematdaya-domain.js`. Tests FX-01, FX-CUR, AT-05, AT-06.

## Test Plan

Row counts, explicit zeros and exact hourly values at chosen hours, selected-week-only variants, deterministic output, scenario metadata, every scenario including empty, no asset named AC, and sums using plain integer addition. Verify ingestion against persisted data in 008, reset through the session contract in 008 and actionable CSV failure in 027.

## Out of Scope

Persistence, tokens, HTTP (008). Totals through the API (009).

## Task Outline

1. Port oracles as failing tests.
2. Write definitions and generator.
3. Port scenarios.
4. Verify determinism.

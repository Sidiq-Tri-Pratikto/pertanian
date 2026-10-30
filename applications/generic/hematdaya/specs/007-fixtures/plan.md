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

`generate(definitions, variant) -> Iterable[ReadingSpec]` yields `(asset_key, interval_start_utc, wh)`. `build_scenario(id) -> ScenarioPlan` returns assets, sources, readings, virtual now, initial period, tariff, schedule, metric, relations and flags, with no database access. Seeding is 008's job.

Scenario quirks to keep from the prototype: learning scenario starts 12 October, Pompa Air stops 24 October, Kulkas gap 22 October 14.00–16.00; stale scenario ends Router at 25 October 18.00 and marks its transport simulated-live; scope scenario adds Meter utama containing Kulkas, Router and TV, a second Kulkas source, and unknown overlap with Pompa Air.

## Prototype Reference

`HOUSE`, `FACTORY`, `SCENARIOS`, `buildScenario`, `pushHourly`, `buildScopeExtras`, `inWeek` in `hematdaya-domain.js`. Tests FX-01, FX-CUR, AT-05, AT-06.

## Test Plan

Row counts; exact hourly values at chosen hours; variant only in the selected week; determinism; every scenario builds; no asset named AC; sums reproduce the oracles using plain integer addition.

## Out of Scope

Persistence, tokens, HTTP (008). Totals through the API (009).

## Task Outline

1. Port oracles as failing tests.
2. Write definitions and generator.
3. Port scenarios.
4. Verify determinism.

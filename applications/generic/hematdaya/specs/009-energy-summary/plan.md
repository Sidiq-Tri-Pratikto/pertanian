# Implementation Plan: Energy summary

**Branch**: `009-energy-summary` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

The core read: SQL aggregation over `current_measurements` resolved against effective bindings, plus shared scope validity, coverage and ranking. Persistence and user resolution of scope selection belong to 028.

## Project Structure

```text
app/energy/
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{periods.py, coverage.py, summary.py, ranking.py}
app/scope/
└── service/validity.py              # refuses overlapping selections
contracts/golden/summary-h-week.json, summary-i-week.json, summary-scope.json
```

## API Contract

`GET /api/v1/sites/{site_id}/summary?preset=last_7_days` or `?start_date=&end_date=`. Validate the inclusive local-date span against a 366-day maximum before querying. This example is for the H fixture's known disjoint selection:

```json
{
  "window": {"start": "2026-10-18T17:00:00Z", "end": "2026-10-25T17:00:00Z", "effective_end": "...",
             "start_date": "2026-10-19", "end_date": "2026-10-25", "timezone": "Asia/Jakarta", "is_current": false},
  "scope": {"valid": true, "issues": [], "included": [{"asset_id": "...", "name": "Kulkas"}], "excluded": []},
  "energy_kwh": "14.700",
  "energy_unavailable_reason": null,
  "coverage": {"minimum": "1.000", "concurrent": "1.000", "allocated_estimate": false},
  "assets": [{"asset_id": "...", "name": "Kulkas", "scope_kind": "device", "energy_kwh": "8.400",
              "share_percent": "57.14", "coverage": "1.000", "gaps": [], "conflict_sources": null}],
  "latest_measurement_at": "...",
  "origins": ["simulated"],
  "revision": 12
}
```

`GET /api/v1/assets/{asset_id}/summary` returns one asset in the same shape and is the parent-only read path until 028. The default site read considers all active assets but publishes a combined total and percentages only when the scope service can prove disjointness. Use the H/I fixture's known scope from 007/008 rather than treating missing relations as disjointness. Unresolved alternative-source overlap withholds that asset's combined value and returns separate source values. Scope persistence and resolution stay in 028, including its selection tables.

## SQL Notes

- Keep only completed observations with `interval_end <= now`. Resolve authority over half-open time ranges, then intersect an eligible reading with its binding range and the query window. Never count the portion after an old binding ends or before a new one begins. Do not add candidates for the same load and time when authority is unresolved.
- For an ordinary interval where uniform allocation is defensible, compute each boundary fragment as the difference between cumulative integer allocations from the original interval start. Use exact arithmetic and the same rounding rule in every query so adjacent fragments reconcile. Set `allocated_estimate`. If allocation would mislead, omit the affected value and expose its reason. A long counter delta may contribute only when its whole span is supported by one binding and fits the query. Keep its known energy span separate from time resolution and never prorate it for a narrower period or bucket.
- Derive gaps and per-asset coverage from the union of valid measured fragments using `range_agg(tstzrange(..., '[)'))`. For concurrent coverage intersect the selected assets' covered ranges. Report unresolved authority or unknown overlap separately from time gaps. Reuse these eligibility, allocation and coverage rules for history in 010.

## Prototype Reference

`assetSlice`, `summarize`, `ranking`, `scopeIssues`, `activeSelection`, `periodBounds`, `fmtGap`.

## Test Plan

Port the applicable API oracles for AT-05, AT-06, FX-CUR, FX-NOW, AT-19, AT-21, AT-36, AT-36b and AT-35. Test unrelated unconfirmed meters, one-asset parent read, alternative-source detail, effective binding change inside an interval, a long counter span in whole and narrower requests, adjacent-fragment conservation, Asia/Makassar, maximum date span, golden JSON, owner isolation and a 3,000-row query timing note.

## Out of Scope

Cost (018), explicit selection save (028), history buckets (010).

## Task Outline

1. Golden files from oracles, failing.
2. Period resolution with site clock.
3. Repository aggregation.
4. Coverage and gaps.
5. Scope validity.
6. Ranking and shares.
7. Router, schemas, contract.

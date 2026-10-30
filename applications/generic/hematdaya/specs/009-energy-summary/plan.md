# Implementation Plan: Energy summary

**Branch**: `009-energy-summary` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

The core read: SQL aggregation over `current_measurements` joined through authoritative bindings, plus scope validity, coverage and ranking.

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

`GET /api/v1/sites/{site_id}/summary?preset=last_7_days` or `?start_date=&end_date=`:

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

`GET /api/v1/assets/{asset_id}/summary` returns one asset in the same shape.

## SQL Notes

- Coverage: `range_agg(tstzrange(interval_start, interval_end, '[)'))` intersected with the window; gaps are its complement.
- Only readings bound authoritatively at `interval_start` count; `interval_end <= now`.
- Boundary crossing: compute the fraction in Python only for the few crossing rows, in integers, and flag `allocated_estimate`.

## Prototype Reference

`assetSlice`, `summarize`, `ranking`, `scopeIssues`, `activeSelection`, `periodBounds`, `fmtGap`.

## Test Plan

Port AT-05, AT-06, FX-CUR, FX-NOW, AT-19, AT-21, AT-36, AT-36b, AT-35 at the API. Add period boundaries, Asia/Makassar window, crossing interval conservation, golden JSON, owner isolation, plus a 3,000-row query timing note.

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

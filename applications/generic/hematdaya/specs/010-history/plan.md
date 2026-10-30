# Implementation Plan: History buckets

**Branch**: `010-history` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Bucketed asset history from the same query path as the summary.

## API Contract

`GET /api/v1/assets/{asset_id}/measurements?start_date=&end_date=&bucket=day|hour`:

```json
{"window": {"...": "..."}, "bucket": "day", "origins": ["simulated"], "resolution_mwh": 1000,
 "buckets": [{"start": "...", "end": "...", "local_date": "2026-10-19", "energy_kwh": "1.200",
              "state": "measured", "coverage": "1.000"}]}
```

## Project Structure

Extend `app/energy/` with `service/history.py` and a repository method using `generate_series` for local-day boundaries, left-joined to aggregates so missing buckets appear as rows.

## Errors

| Code | Public | HTTP |
|---|---|---|
| `APP-RANGE-TOO-LARGE` | `RANGE_TOO_LARGE` | 400 |

## Prototype Reference

`history` in `hematdaya-domain.js`. Its `ref` median arrives in 020, not here.

## Test Plan

Sum equals summary for H and I; missing, measured zero, partial, future states; hour buckets; range limit; other timezone; foreign asset.

## Out of Scope

Reference series (020), chart UI (015).

## Task Outline

1. Failing reconciliation tests.
2. Bucket query.
3. State and coverage mapping.
4. Router and contract.

# Implementation Plan: History buckets

**Branch**: `010-history` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Bucketed asset history from the same query path as the summary.

## API Contract

`GET /api/v1/assets/{asset_id}/measurements?start_date=&end_date=&bucket=day|hour`:

```json
{"window": {"...": "..."}, "bucket": "day", "origins": ["simulated"], "resolution_mwh": 1000,
 "highest_bucket": {"start": "2026-10-18T17:00:00Z"},
 "buckets": [{"start": "2026-10-18T17:00:00Z", "end": "2026-10-19T17:00:00Z",
              "local_date": "2026-10-19", "energy_kwh": "1.200", "unavailable_reason": null,
              "state": "measured", "coverage": "1.000"}]}
```

## Project Structure

Extend `app/energy/` with `service/history.py` and a repository method generating local-day boundaries in the site's IANA zone, left-joined to aggregates so missing buckets appear as rows. For hours, step between the actual UTC bounds of each local day and label each bucket with local date, time and UTC offset. Reject ranges exceeding 009's date cap or the actual 1,000-bucket limit before the read.

Reuse 009's effective binding, scope, allocation and coverage rules. A blocked bucket carries `state: "unavailable"`, null energy, and a reason such as `scope_conflict` or `insufficient_resolution`. Keep unavailable and future buckets distinct from gaps and measured zero. Choose the fully covered measured bucket with the greatest unrounded value, breaking ties by earliest UTC start. Return its UTC start in `highest_bucket`, or null when no bucket qualifies.

## Errors

| Code | Public | HTTP |
|---|---|---|
| `APP-RANGE-TOO-LARGE` | `RANGE_TOO_LARGE` | 400 |

## Prototype Reference

`history` in `hematdaya-domain.js`. Its `ref` median arrives in 020, not here.

## Test Plan

Sum equals summary for H and I at supported granularity. Test missing, measured zero, partial, future and unavailable states, repeated local hour with distinct offsets, both DST transitions, 1,000 actual buckets and date limits, highest bucket ties and null, unresolved source conflict, long counter spans and foreign assets.

## Out of Scope

Reference series (020), chart UI (015).

## Task Outline

1. Failing reconciliation tests.
2. Bucket query.
3. State and coverage mapping.
4. Router and contract.

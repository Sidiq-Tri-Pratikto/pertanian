# Implementation Plan: Matched baseline

**Branch**: `020-baseline` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Comparison engine with no alert logic. Insights (021) read its result.

## Project Structure

```text
app/baseline/
├── router.py                       # GET /assets/{id}/comparison
├── model/{models.py, schema.py}
└── service/{windows.py, mask.py, compare.py}
```

## API Contract

`GET /api/v1/assets/{asset_id}/comparison?start_date=&end_date=` returns `state`, `reason`, `current`, `historical[]`, `baseline_kwh`, `mad_kwh`, `delta_kwh`, `percent`, `resolution_kwh`, `mask_coverage`. History gains `reference_kwh` per bucket.

## Design

Load slots keyed by offset from each window start, in one query across the four windows. Mask is the intersection of offset and duration across current and eligible windows. Keep `compare` pure: slots in, comparison out. Differing cadence across windows gives `not_comparable`.

## Prototype Reference

`slots`, `compareAsset`, `median`, `history` (`ref`). Tests AT-05b, AT-19, AT-16.

## Test Plan

Port tests; add elapsed windows at 21 Oktober 12.00, differing cadence, unknown resolution, zero baseline, conflict asset, more than seven days, and reference median with only two windows.

## Out of Scope

Alert thresholds and evidence storage (021), outside-window (030).

## Task Outline

1. Pure mask and compare with tests.
2. Slot query.
3. Router, contract.
4. Reference series in history.

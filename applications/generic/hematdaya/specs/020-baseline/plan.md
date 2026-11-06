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

`GET /api/v1/assets/{asset_id}/comparison?start_date=&end_date=` returns `state`, `reason`, `current`, `historical[]`, `baseline_kwh`, `mad_kwh`, `delta_kwh`, `percent`, `resolution_kwh`, `mask_coverage` and the actual aligned `common_mask`. Each window includes local and UTC bounds, measured and common-mask energy, and coverage. History gains `comparison_kwh` and `reference_kwh` on the same valid mask alongside the separate full `energy_kwh`. Label per-bucket reference medians separately from the median of full matched periods. Their sum need not equal the period median.

## Design

Load slots in one query across the four windows. Align by relative calendar day, local clock time, duration and occurrence of a repeated local time. Use UTC interval bounds to measure coverage and elapsed duration. Exclude ambiguous or unmatched transition slots from the common mask. Exclude historical windows with incompatible cadence, measurement kind, asset selection or applicable schedule. If too few eligible windows or insufficient common coverage remain, return the corresponding non-comparable state. Keep `compare` pure. Preserve fractional allocations, even-sample medians and MAD as exact scaled integers or ratios until serializing the response.

## Prototype Reference

`slots`, `compareAsset`, `median`, `history` (`ref`). Tests AT-05b, AT-19, AT-16.

## Test Plan

Port the tests. Add elapsed windows at 21 Oktober 12.00, differing cadence and measurement kinds, IANA timezone transitions, unknown resolution, zero baseline, conflict asset, more than seven days, and an exact fractional median with two windows. Verify both series use the same mask and full totals remain available separately.

## Out of Scope

Alert thresholds and evidence storage (021), outside-window (030).

## Task Outline

1. Pure mask and compare with tests.
2. Slot query.
3. Router, contract.
4. Reference series in history.

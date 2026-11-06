# Implementation Plan: History chart

**Branch**: `015-history-chart` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Port `HD.HistoryChart` to `react-native-svg`, with the existing data alternative.

## Project Structure

```text
src/components/hd/HDHistoryChart.tsx   # introduced by 022, merged a round earlier; extend it for buckets, states and reference
src/features/assets/useHistory.ts
src/app/(tabs)/(beranda,perangkat,saran)/asset/[id].tsx
```

## Mobile

Draw bars as `Rect`, gaps as an SVG `Pattern` with `color-chart-missingMarker`, and zero as a baseline tick. Use text for the scale note and legend. Use `color-chart-*`, `size-stroke-chart` and `size-chart-plotHeight` tokens. The whole `Svg` has `role="img"` with an `aria-label`. The summary below it formats the service's `highest_bucket` or its null state. Render actual bucket count, UTC bounds and local labels from 010, including short or long local days and repeated-hour labels that distinguish their offsets.

Resolve `highest_bucket.start` against the same series by UTC start. The service chooses a fully covered measured bucket and breaks ties by earliest start. Preserve the service's distinct unavailable reasons in the chart's text alternative and table.

## Prototype Reference

`Asset` history block in `hematdaya-app.js`, `HistoryChart` in `docs/design/components/`.

## Test Plan

Test every bucket state, 23-hour and 25-hour days, highest-bucket ties and the no-eligible-bucket state. Verify table parity, large text, and access to values without hover.

## Out of Scope

Reference series until 020 data exists; the prop is ready but unused here.

## Task Outline

1. Component with states and tests.
2. `useHistory`.
3. Wire Lihat riwayat and Lihat data.

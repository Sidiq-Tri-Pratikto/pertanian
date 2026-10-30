# Implementation Plan: History chart

**Branch**: `015-history-chart` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Port `HD.HistoryChart` to `react-native-svg`, with the existing data alternative.

## Project Structure

```text
src/components/hd/HDHistoryChart.tsx
src/features/assets/useHistory.ts
src/app/(tabs)/(beranda,perangkat,saran)/asset/[id].tsx
```

## Mobile

Bars as `Rect`; gap hatch as an SVG `Pattern` with `color-chart-missingMarker`; zero as a baseline tick. Scale note and legend are text. Tokens: `color-chart-*`, `size-stroke-chart`, `size-chart-plotHeight`. The whole `Svg` has `role="img"` with an `aria-label`; the summary is plain text below it.

## Prototype Reference

`Asset` history block in `hematdaya-app.js`, `HistoryChart` in `docs/design/components/`.

## Test Plan

All bucket states; dense hourly; table parity; large text; no hover dependency.

## Out of Scope

Reference series until 020 data exists; the prop is ready but unused here.

## Task Outline

1. Component with states and tests.
2. `useHistory`.
3. Wire Lihat riwayat and Lihat data.

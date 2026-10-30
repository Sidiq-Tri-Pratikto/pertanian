# Implementation Plan: Perangkat and asset detail

**Branch**: `014-perangkat-s04-s06` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

List and detail read paths. The chart arrives in 015 and editing in 016.

## Project Structure

```text
src/components/hd/HDAssetRow.tsx
src/features/assets/{useAssets.ts, useAssetSummary.ts}
src/app/(tabs)/(perangkat)/perangkat.tsx
src/app/(tabs)/(beranda,perangkat,saran)/asset/[id].tsx
```

## Mobile

`FlatList`, not FlashList, per the architecture decisions. Keep scroll offset in the navigation context keyed by route. `HDAssetRow`: one pressable row, no nested buttons, `meter` maps from `site_total`.

## Prototype Reference

`Assets`, `Asset` in `hematdaya-app.js`.

## Test Plan

Sorting and tie-break; scope kinds; gap versus zero rows; stale row; conflict row; back restores scroll; failure keeps list; long Indonesian names at 320 px.

## Out of Scope

History chart (015), edit and archive (016), source setup (035).

## Task Outline

1. HDAssetRow with states.
2. List screen.
3. Detail screen and source section.
4. Scroll restore.
5. Flip registry.

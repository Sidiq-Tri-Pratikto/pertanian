# Implementation Plan: Perangkat and asset detail

**Branch**: `m2/perangkat` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

List and detail read paths, with no API change. The chart arrives in 015 and editing in 016. Decisions, states, copy and evidence are in [tasks.md](tasks.md).

## Project Structure

```text
# New
src/components/hd/HDAssetRow.tsx
src/features/assets/{useAssets.ts, useAssetSummary.ts, useLastConfirmed.ts}
src/features/assets/{asset-model.ts, ReadFailure.tsx, PerangkatScreen.tsx, AssetDetailScreen.tsx}
src/app/(tabs)/(beranda,perangkat,saran)/asset/[id].tsx
tests/perangkat.test.tsx
tests/asset-model.test.ts
tests/fixtures/assets.json

# Changed
src/app/(tabs)/(perangkat)/perangkat.tsx            # composes PerangkatScreen
src/app/(tabs)/(beranda,perangkat,saran)/pengaturan.tsx  # lists only coming_soon
src/features/registry.ts                            # the flip
src/lib/format.ts                                   # cadence and resolution

# Changed in P1's modules, flagged for review
src/api/client.ts                                   # three reads and their guards
src/features/navigation.ts                          # openAsset
src/components/hd/HDScreen.tsx                      # focus without scrolling
src/components/hd/HDContributionRanking.tsx         # rows open their asset
src/features/energy/beranda-model.ts                # ranking assetId, shownOrigins
src/app/(tabs)/(beranda)/beranda.tsx                # Lihat perangkat terbesar
../hematdaya-api/tests/integration/test_summary.py  # pins the two summary routes to one row
```

## Mobile

**Reads.** The list joins P1's `useSummary` with `useAssets` by asset ID, because the summary row has no location or category and the asset row has no energy. Staleness comes from P1's `useInsights` notices with `kind: "stale"`. Detail reads `GET /assets/{id}/summary` for the shared period and `GET /assets/{id}` for sources and bindings. Its row is `assets[0]`, and it never renders `share_percent` or `scope.excluded`, which a one-asset summary fills with `100.00` and every other asset.

**Keys.** Reads key by site, asset where there is one, and period. No scope key yet, because no route takes a scope until 028.

**List.** Rows render with `.map` inside `HDScreen`'s `ScrollView`. A `FlatList` there would nest two vertical scrollers and stop virtualizing. Architecture rules out FlashList until a measured need and does not ask for `FlatList`, and PRD §18's working scale is 20 sources. Rows keep the service's order. `HDAssetRow`: one pressable row, no nested buttons, keeping `HD.AssetRow`'s contract, with `kind` `meter` mapped from `site_total` and shown as "Meter lokasi".

**Scroll.** The stack keeps the list mounted, so its scroll view keeps its offset. What loses the place on web is `HDScreen` calling `focus()` on the heading at every return, which scrolls to it. Measured: 1200 to 0, and 1200 to 1200 with `preventScroll`. So `HDScreen` passes `{ preventScroll: true }` and no offset is stored.

**Failure.** `useSummary`'s `keepPreviousData` covers pending reads only, so a failed period change leaves `data` undefined. `useLastConfirmed` keeps the last confirmed value, and each body mounts under a `key` for its site, so nothing crosses workspaces. `ReadFailure` shows the message and reference ID, and retry only when `recovery.retryable` is true.

**Detail.** Build on `berandaModel` and P1's `HD` components. A conflicted asset shows `HDNotice` with one value per source, because `HDEnergyMetric`'s conflict copy describes a combined total. Lihat periode data sets `workspace.initialPeriod`, as Beranda does, and hides when already there, since the service has no per-asset data range. Origin comes from the asset's sources, because `origins` is empty on a no-data period and on a conflict.

**Beranda.** Wire the ranking rows and Lihat perangkat terbesar to the shared detail route, preserving the current period.

**Entry points.** Use the existing Segera hadir routes for source setup and import until their owning specs ship, and render conflict notices without an S11 link until 029.

**Smoke flow.** `e2e/smoke.yaml` reaches Perangkat with no API and no workspace, so S04's no-workspace branch keeps the exact text "Belum ada perangkat" and makes no request. The flow is not edited.

## Prototype Reference

`Assets`, `Asset` in `hematdaya-app.js`. An oracle only: its one-or-the-other quality label and its client-side `dataRange` are not copied.

## Test Plan

Jest from responses recorded from the service. Rendered order and stable ties from the service, category and scope labels, gap and zero rows, stale and conflicting sources, an imported source with unknown cadence and resolution, one-tap detail from Beranda, return without a remount, preserved content on failure, retry and reference ID, empty and no-workspace states, not-found, session end, and the registry flip with its Settings effect. A browser walk against a live API covers scroll offsets and long Indonesian names at 320 px, recorded as a web run. Android stays not run beyond the smoke flow.

## Out of Scope

History chart (015), edit and archive (016), import (027), scope resolution (029), source setup (035), any API or contract change. Related insights on S06 have no owning spec yet and are not built here (see spec.md, Open Items).

## Task Outline

1. Record responses. Client reads, labels, hooks, and the `HDScreen` focus fix.
2. HDAssetRow with states.
3. List screen.
4. Detail screen and source section.
5. Beranda entry points.
6. Flip registry, and Settings honors the status.
7. Browser walk and scroll measurement.

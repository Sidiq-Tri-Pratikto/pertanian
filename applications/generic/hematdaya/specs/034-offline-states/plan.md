# Implementation Plan: Offline and combined states

**Branch**: `034-offline-states` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
src/features/offline/{useConnectivity.ts, persist-queries.ts}
src/components/hd/HDDataQuality.tsx   # all rows
app/energy/service/freshness.py       # stale from cadence, policy stale v1
```

## Summary

Client persistence for reads, plus a matrix of state tests over real scenarios.

## Technical Context

**New dependencies**: `@react-native-community/netinfo`, `@tanstack/query-async-storage-persister`, `@react-native-async-storage/async-storage`, through `npx expo install`. `expo-sqlite` stays out.

## Design

Persist only successful reads, keyed by site, period and selection revision. Clear on workspace change, so nothing crosses principals. Never persist tokens or drafts of secrets. The API returns `freshness` per source: `state`, `last_capture_at`, `cadence_seconds`, `policy_version`.

## Prototype Reference

Scenarios `h-stale-offline`, `h-historical-offline`, `h-learning-partial`, `h-zero`; `qualityBlock`, `api.refresh`, `api.checkSource`.

## Test Plan

Every combination; offline save; refresh failure; cache cleared on workspace change; stale threshold boundary; retry does not add readings; tests on web and Android.

## Out of Scope

Offline writes, background sync.

## Task Outline

1. Freshness in the API.
2. Connectivity hook.
3. Query persistence.
4. HDDataQuality complete.
5. Combination tests.
6. Flip registry.

# Implementation Plan: Offline and combined states

**Branch**: `034-offline-states` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
src/features/offline/{useConnectivity.ts, persist-queries.ts, persist-drafts.ts}
src/components/hd/HDDataQuality.tsx   # all rows
app/energy/service/freshness.py       # stale from cadence, policy stale v1
```

## Summary

Persist confirmed reads and non-secret drafts locally. Test the independent recovery and freshness states against real scenarios.

## Technical Context

**New dependencies**: `@react-native-community/netinfo`, `@tanstack/query-async-storage-persister`, `@react-native-async-storage/async-storage`, through `npx expo install`. `expo-sqlite` stays out.

## Design

Persist successful confirmed reads with fetch time, keyed by principal, workspace, site, period, and selection revision. Persist only allowlisted non-secret draft fields in the same workspace namespace with separate draft keys. Restore neither until the workspace provider confirms the current principal and workspace. Cancel old persistence and clear its stored cache and drafts on workspace change or demo reset. Expose the same cleanup to the logout flow in 037. If storage is unavailable, retain drafts in memory and do not claim restart recovery. Never persist session tokens, pending writes, or selected file bytes through these stores.

The API returns `freshness` per source with `state`, `last_capture_at`, `cadence_seconds`, and `policy_version`. Apply the stale threshold only when the source expects recurring captures and its cadence is known. Historical CSV retains historical provenance. Client offline and source freshness remain separate.

## Prototype Reference

Scenarios `h-stale-offline`, `h-historical-offline`, `h-learning-partial`, `h-zero`; `qualityBlock`, `api.refresh`, `api.checkSource`.

## Test Plan

Test every core-only combination on web and Android, including a real CSV import from 027, learning plus partial data, valid measured zero, and scope conflict. The core-only display never fabricates cost. Cover offline save, refresh failure, same- and different-workspace cold starts, workspace teardown, demo reset, the stale threshold boundary, unknown cadence, and retry without adding readings.

After 019 is available, run and record separate integration cases for learning plus partial plus missing tariff and valid zero plus missing tariff. These cases verify the unavailable-cost display and do not block core-only acceptance.

## Out of Scope

Offline writes, background sync, saved-account sign-in and explicit retry after login (037).

## Task Outline

1. Freshness in the API.
2. Connectivity hook.
3. Confirmed query and non-secret draft persistence.
4. HDDataQuality complete.
5. Combination tests.
6. Flip registry.

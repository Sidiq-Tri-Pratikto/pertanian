# Implementation Plan: Demo onboarding and data layer

**Branch**: `012-demo-onboarding-data-layer` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Add the client data layer and the first real journey: choose a scenario, get a session, land on a labelled Beranda shell.

## Technical Context

**New dependencies**: `@tanstack/react-query`, `expo-secure-store` (through `npx expo install`)

## Project Structure

```text
src/api/client.ts                   # bearer token, one failure path
src/api/query-client.ts             # retry honours recovery
src/features/workspace/
├── workspace-store.ts              # secure store, sessionStorage on web
├── WorkspaceProvider.tsx
├── useDemoSession.ts               # one operation ID and secret proof per intentional create
└── DemoSheet.tsx
src/features/navigation-context/NavigationContextProvider.tsx   # period, scope
src/components/hd/HDSheetDialog.tsx
src/components/hd/HDProgressStatus.tsx
src/components/hd/HDProvenanceTag.tsx
src/app/index.tsx                   # resolve the stored workspace before redirect
```

## Mobile

- `HDSheetDialog`: RN `Modal`, focus to title, `onRequestClose`, Escape on web, focus returns to the opener. Verify return focus: this is the risk that removed `@gorhom/bottom-sheet` from the plan.
- `HDProgressStatus`: always mounted polite live region.
- Query retry follows `recovery.retryable`, `retry_after_seconds` and `max_attempts` including the initial attempt. A stored demo token rejected by `SESSION_EXPIRED` or `UNAUTHORIZED` ends that workspace and clears its cached state.
- For creation, generate an `Idempotency-Key` with at least 128 random bits and a separate secret `X-Demo-Replay-Proof` with at least 256 random bits. Keep the pair with the unchanged request for 008's bounded replay window. Keep the proof out of logs and ordinary drafts. Retry with the same pair and body. After a terminal replay conflict, show the unknown outcome and require an explicit new start with a fresh pair.
- Initialize navigation from the acknowledged `site_id` and `initial_period`. On restart, resolve the stored workspace before entering Beranda and separate cached state by workspace.

## Prototype Reference

`Welcome`, `DemoSheet`, `Empty` in `hematdaya-app.js`.

## Test Plan

Verify the returned initial period, Industri preselection, cancellation, the empty workspace, restart, and expired or purged tokens. Test API outage, a lost response after creation, an expired replay window, and the server retry limit. Check provenance and web focus restoration. Record web and Android journey evidence using the 003 runner.

## Out of Scope

Real Beranda content (013), account sign-in (037).

## Task Outline

1. Add dependencies with `expo install`.
2. Client with token and query retry policy, tests first.
3. Workspace store and provider.
4. HDSheetDialog, HDProgressStatus, HDProvenanceTag.
5. DemoSheet and S01, S02 wiring.
6. Navigation context.
7. Flip `demo` in the registry.

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
├── useDemoSession.ts
└── DemoSheet.tsx
src/features/navigation-context/NavigationContextProvider.tsx   # period, scope
src/components/hd/HDSheetDialog.tsx
src/components/hd/HDProgressStatus.tsx
src/components/hd/HDProvenanceTag.tsx
src/app/index.tsx                   # redirect when a workspace exists
```

## Mobile

- `HDSheetDialog`: RN `Modal`, focus to title, `onRequestClose`, Escape on web, focus returns to the opener. Verify return focus: this is the risk that removed `@gorhom/bottom-sheet` from the plan.
- `HDProgressStatus`: always mounted polite live region.
- Query retry: follow `recovery.retryable`, `retry_after_seconds`, `max_attempts`; never retry `SESSION_EXPIRED`.

## Prototype Reference

`Welcome`, `DemoSheet`, `Empty` in `hematdaya-app.js`.

## Test Plan

Demo opens; Industri preselected; cancel keeps nothing; empty workspace; restart resumes; expired session; API down keeps sheet; retry; no retry beyond `max_attempts`; provenance tag present; focus return on web.

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

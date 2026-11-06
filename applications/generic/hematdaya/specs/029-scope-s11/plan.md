# Implementation Plan: Scope screen

**Branch**: `029-scope-s11` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
src/features/scope/{useSelection.ts, useScopeDraft.ts}
src/app/(tabs)/(beranda,perangkat,saran)/cakupan.tsx
src/components/hd/HDScopeSummary.tsx   # parent/child and unknown variants
```

## Summary

S11 over the scope API, using a server-validated preview rather than client arithmetic.

## Mobile

Call `POST /sites/{site_id}/aggregation-selection/preview` from 028 with the full draft, including proposed authority or skip, disjoint confirmations, and period. Render the server's totals and group child values under their parent. Keep all changes local until confirmation. Confirm with one `PUT /sites/{site_id}/aggregation-selection` carrying that proposal and its expected revisions. On stale rejection, retain the draft and request a fresh preview. After success, refresh the confirmed summary and affected queries.

## Prototype Reference

`Scope` in `hematdaya-app.js`, including its fake-zero bug and fix.

## Test Plan

- Parent view, child view, source choice preview without mutation, unknown confirmation.
- Stale and failed save, cancel after selecting authority, draft edit invalidates preview, disabled reason.
- No fake zero, labels separate.

## Out of Scope

Topology editing.

## Task Outline

1. Wire the preview and aggregate save from 028.
2. HDScopeSummary variants.
3. Draft hook.
4. Screen.
5. Links from Beranda and Perangkat.
6. Flip registry.

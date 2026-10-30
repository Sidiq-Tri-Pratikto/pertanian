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

The prototype computed its preview in the client. Here a `dry_run` flag on `PUT` returns the resulting total, so the client stays free of arithmetic. Add that flag in this PR. Group parent/child by parent, as the prototype's fix did: "Kulkas, Router, TV saja" with the summed child value from the service.

## Prototype Reference

`Scope` in `hematdaya-app.js`, including its fake-zero bug and fix.

## Test Plan

Parent view; child view; source choice first; unknown confirmation; rejection; cancel; disabled reason; no fake zero; labels separate.

## Out of Scope

Topology editing.

## Task Outline

1. `dry_run` on the API.
2. HDScopeSummary variants.
3. Draft hook.
4. Screen.
5. Links from Beranda and Perangkat.
6. Flip registry.

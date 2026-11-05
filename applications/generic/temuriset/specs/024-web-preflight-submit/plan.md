# Implementation Plan: Preflight screen and submission

**Branch**: `024-web-preflight-submit` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/
├── app/pitches/new/page.tsx
├── features/pitches/{submit-state.ts, api.ts}   # idle -> sending -> sent | lost | stale | duplicate | failed
└── views/pitches/{PreflightView, FilePicker, BriefEditor}.tsx
e2e/j01-project-pitch.spec.ts, e2e/j02-company-raise.spec.ts
```

## Prototype Reference

`vm.preflight`, `Preflight.dc.html`; walker `j01` and `j02` in `journeys.browser.js` (port assertions, not the walker).

## Test Plan

Submit state machine; each failure state view; Playwright J01 and J02 to submission; axe; overflow.

## Out of Scope

Workspace and decisions (026).

## Task Outline

1. Submit state machine with tests.
2. Preflight view, file picker, brief editor.
3. Failure states.
4. J01 and J02 journeys.
5. Registry and manifest flips.

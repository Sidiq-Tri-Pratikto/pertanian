# Implementation Plan: Profile, privacy and reports screens

**Branch**: `035-web-settings-privacy` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/views/settings/{ReportForm, PrivacyRequests}.tsx
applications/temuriset-web/src/app/settings/page.tsx
applications/temuriset-web/src/app/pitches/[id]/page.tsx
applications/temuriset-web/src/views/pitches/WorkspaceView.tsx
applications/temuriset-web/e2e/privacy.spec.ts
```

## Prototype Reference

`vm.settings`, `Settings.dc.html`.

## Task Outline

1. Report form with validation.
2. Privacy requests and status.
3. Room entry point; Playwright; registry flip.

The authorized S13 workspace shipped in 026. Reuse its session and pitch read. A report link uses only the opaque pitch ID and type. Verify a participant can enter S18 from the room and an unrelated account never sees the link. The separate discussion and scheduling features from 027–029 are outside this flow.

# Implementation Plan: Profile, privacy and reports screens

**Branch**: `035-web-settings-privacy` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/views/settings/{ReportForm, PrivacyRequests}.tsx
applications/temuriset-web/src/app/settings/page.tsx
e2e/privacy.spec.ts
```

## Prototype Reference

`vm.settings`, `Settings.dc.html`.

## Task Outline

1. Report form with validation.
2. Privacy requests and status.
3. Room entry point; Playwright; registry flip.

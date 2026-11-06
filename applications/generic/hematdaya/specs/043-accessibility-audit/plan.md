# Implementation Plan: Accessibility and platform audit

**Branch**: `043-accessibility-audit` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
docs/evidence/accessibility-<date>.md
```

## Summary

A recorded audit with fixes as small PRs. No new features.

Record the build, device/browser, assistive technology, measured contrast and hit areas, and result per task. Link evidence from other specs for UX checks outside this audit's focus. Track each task blocker until a fix is verified on the affected runtime, and keep G4 open while any blocker remains.

## Test Plan

Task list: demo, read total, largest contributor, history data alternative, evidence, import with errors, scope resolution, tariff, schedule. Run with TalkBack, VoiceOver, keyboard on web, 200% text, reduced motion, short phone, 320 px.

## Out of Scope

Formal WCAG audit by a third party.

## Task Outline

1. Audit checklist.
2. Run per platform.
3. File findings, fix task blockers and rerun affected checks.
4. Record evidence.

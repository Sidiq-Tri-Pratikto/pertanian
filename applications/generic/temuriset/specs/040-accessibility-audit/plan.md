# Implementation Plan: Accessibility audit of assembled journeys

**Branch**: `040-accessibility-audit` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Evidence surfaces

Use the existing 003 production-build Chromium suite in `applications/temuriset-web/e2e/` as supporting evidence. Follow the rendered journeys and dynamic states separately. The integrated baseline has J01–J03 and 035 settings/privacy. J04 needs M8 (027–029), J05 needs M9 (030–032), and approved staging needs 037. The full audit remains gated wherever those prerequisites are missing.

## Task outline

1. Audit keyboard operation, focus and dialogs on the available journeys and settings. Measure rendered contrast, including focus and states, and inspect non-color signals.
2. Run separate checks for actual 200% browser zoom, text resize and 320 CSS px reflow, with supporting 360/768/1280 CSS px layouts.
3. Record screen-reader output from NVDA with Firefox and VoiceOver with Safari when those pairings are available. Report browser accessibility-tree, axe and media-feature emulation results under the modes actually tested.
4. Record evidence and failure disposition in `docs/roadmap/accessibility-audit.md`. Preserve distinct local, staging and assistive-technology results.

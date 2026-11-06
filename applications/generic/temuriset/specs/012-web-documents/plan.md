# Implementation Plan: Documents in the editor and pitch room

**Branch**: `012-web-documents` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/
├── components/tr/{DocumentItem, Dialog}.tsx    # ports
├── features/documents/{upload.ts, use-document-state.ts, api.ts}
└── views/portfolio/EditorView.tsx               # step 2 gains DocumentsPanel
e2e/documents.spec.ts                            # fixtures: small PDF, image-only PDF, renamed .exe
```

## Prototype Reference

`uploadSim` and `docProps` in `views.js`; `DocumentItem` usage in `Editor.dc.html` and `Workspace.dc.html`.

## Test Plan

Upload state transitions with a mocked API; polling stops at final states; dialog focus and Escape; Playwright with the development scanner; axe.

## Out of Scope

Choosing files for a pitch (024), the pitch-room document tab (026).

## Task Outline

1. Port DocumentItem and Dialog.
2. Upload and polling hooks.
3. Step 2 panel and grant list.
4. Revocation dialog.
5. Playwright, registry flip.

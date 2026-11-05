# Implementation Plan: Inovasi Saya, detail and four-step editor

**Branch**: `011-web-portfolio-editor` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/
├── app/inventions/page.tsx, [id]/page.tsx, [id]/edit/page.tsx
├── components/tr/                # port Steps, SaveState, VersionConflict, FactSource, InventionCard, SummaryList, TextArea
├── features/portfolio/
│   ├── editor-state.ts           # step values, dirty flag, save state machine: local -> saving -> saved | failed | conflict
│   └── api.ts                    # typed calls: saveDraft, publish, archive
└── views/portfolio/{InventionsView, InventionView, EditorView, PublicPreview}.tsx
e2e/portfolio.spec.ts
```

## Prototype Reference

`views.js`: `vm.editor`, `vm.invention`, `vm.inventions`; `Editor.dc.html`, `Invention.dc.html`. Copy and states transfer; the prototype's in-memory store does not.

## Test Plan

Editor state machine unit tests (save, fail, retry, conflict, back); view tests for each step and the preview; partner versus owner detail; axe per view; Playwright journey; 003 overflow on new routes.

## Out of Scope

Documents (012), support and funding forms (015).

## Task Outline

1. Port components with tests.
2. Editor state machine.
3. Steps 1, 2 and 4; step 3 placeholder.
4. Detail and list.
5. Playwright, registry flip.

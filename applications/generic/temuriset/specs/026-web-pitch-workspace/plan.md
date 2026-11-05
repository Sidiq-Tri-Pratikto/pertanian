# Implementation Plan: Pitch lists and workspace

**Branch**: `026-web-pitch-workspace` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/
├── app/pitches/page.tsx, app/pitches/[id]/page.tsx
├── components/tr/{Tabs, RevisionItem, Dialog}.tsx
├── features/pitches/{list-filters.ts, decision.ts, revisions.ts}
└── views/pitches/{PitchListView, WorkspaceView, SummaryTab, RevisionTab, DocumentsTab, HistoryTab}.tsx
e2e/j03-revision.spec.ts
```

## Prototype Reference

`vm.pitches`, `vm.workspace`, `vm.revisions`, `pitchTurn`; `Workspace.dc.html`, `Revisions.dc.html`; walker `j03`.

## Test Plan

List filters; each tab's states; dialogs; view-only member; denied; J03 Playwright; axe; keyboard on dialogs.

## Out of Scope

Discussion and schedule tabs (029).

## Task Outline

1. Ports: Tabs, RevisionItem, Dialog.
2. Lists with filters.
3. Workspace summary and decisions.
4. Revision tab.
5. Documents and history tabs.
6. J03 journey, registry flip.

### Reporting integration

When the authorized workspace is available, link **Laporkan** to the shared settings report form with `reportHref("PITCH", pitchId)`. Pass only the subject type and opaque ID. The 035 browser acceptance case must start in the workspace and submit a prefilled report.

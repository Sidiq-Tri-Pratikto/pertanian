# Implementation Plan: Decision path (revamp R2b)

**Spec**: [spec.md](spec.md)

1. `features/pitches/workspace.ts`: `primaryFor(step, tab, pitchId)`. `views/pitches/WorkspaceView.tsx`: facts row (counterpart, mandate, active version, status) and the `NextStep` action link.
2. `views/pitches/PreflightView.tsx`: "Yang akan diterima {nama}" with `SummaryList` rows and `changeHref` anchors to `#brief-pitching` and `#berkas-pilihan`; `briefPreview()`.
3. `features/portfolio/editor-state.ts`: `resumeStep()`. `app/home/page.tsx`: the draft resume item, then the matches item, sorted with this party's work first. `features/destinations.ts` and `views/DestinationView.tsx`: `savedLink` for the partner home.
4. Tests: `tests/workspace.test.tsx`, `tests/pitches.test.tsx`, `tests/pages.test.tsx`, `tests/portfolio.test.tsx`.

# Tasks for the accessibility audit of assembled journeys

**Input** [spec.md](spec.md), [plan.md](plan.md), the application handoff and PRD section 18. Paths are relative to the TemuRiset project.

## Phase 1. Setup

- [X] T001 Inventory the integrated web build, browser and operating-system tooling, J01–J05 and settings/privacy. Map the available automated baselines in `applications/temuriset-web/e2e/` to the screen and interaction inventory in `docs/roadmap/accessibility-audit.md`. Use synthetic accounts and fixtures.

## Phase 2. Foundation

- [X] T002 Define the matrix and evidence protocol in `docs/roadmap/accessibility-audit.md`. Record the build, environment, browser/version, assistive technology/version, viewport in CSS px, zoom and result for every check. Use PASS, FAIL, NOT RUN or BLOCKED, with reproducible evidence and reasons for unresolved rows.

## Phase 3. User Story 1, Evidence for WCAG 2.2 AA (P1)

**Independent test.** Run spec 003 browser checks and traverse the available core journeys on a production build. Compare automatic findings with rendered focus and color, reflow, labels, errors, announcements and motion checks. Give unexecuted environments and interaction states their own rows.

- [X] T003 [US1] Run browser keyboard checks for J01–J03 and settings/privacy using `applications/temuriset-web/e2e/keyboard.spec.ts` plus the actual journey routes and dialogs. Verify logical tab and reverse-tab order, operability, visible/unobscured focus, modal containment, close and return. Record the exact checks in `docs/roadmap/accessibility-audit.md`.
- [X] T004 [US1] Measure rendered text, icon, control, focus and state contrast on those surfaces. Verify that non-color indicators communicate errors and states, including the current versus planned distinction. Record the foreground and effective rendered background, measured ratios, states reached and applicable exceptions in `docs/roadmap/accessibility-audit.md`. Use 4.5:1 for normal text, 3:1 for large text, and 3:1 for applicable non-text control, icon and focus boundaries.
- [X] T005 [US1] Run `applications/temuriset-web/e2e/overflow.spec.ts` and inspect live journey controls at 320, 360, 768 and 1280 CSS px. Record genuine 200% browser zoom separately from CSS text-only scaling. Verify that content and primary actions remain operable, and list any applicable reflow exceptions in `docs/roadmap/accessibility-audit.md`.
- [X] T006 [US1] Check accessible labels, error associations, status announcements, 24×24 CSS px targets or documented exceptions, and prefers-reduced-motion behavior in rendered journeys. Run NVDA with Firefox and VoiceOver with Safari when available. In `docs/roadmap/accessibility-audit.md`, separate actual screen-reader speech/navigation from browser accessibility-tree, axe and media emulation evidence.
- [ ] T007 [US1] Repeat the full matrix on approved staging. Retain separate local and staging evidence in `docs/roadmap/accessibility-audit.md`. Mark the unsupported J04 and J05 rows BLOCKED pending 027–029 and 030–032 respectively. Record any missing assistive-technology pairing with a specific reason.
- [X] T008 [US1] Triage each actual FAIL in `docs/roadmap/accessibility-audit.md` with the reproduction, affected users and status. Fix in-scope regressions in the affected files under `applications/temuriset-web/src/` with a browser regression when feasible, then re-run the failed checks, or attach the filed issue reference. When filing is unavailable, include a ready-to-file issue with reproduction and mark disposition open.

## Phase 4. Polish

- [X] T009 Verify that each UX-19 to UX-22 check has a row for every scoped journey with a build, result, evidence or blocking reason in `docs/roadmap/accessibility-audit.md`. Update `specs/040-accessibility-audit/spec.md` with local and externally gated status.

## Dependencies and execution order

- T001/T002 establish the protocol and matrix. T003–T006 may be executed in parallel on independently provisioned synthetic browser contexts, recording results in distinct matrix sections before they are assembled. Only the final recorder edits the shared report.
- T008 follows the applicable observations. T009 can close local documentation while T007 remains gated.
- The MVP is a check-by-check audit of the currently available runtime, with an explicit evidence gap for each unreached surface, environment or mode.

## Requirements coverage

| Requirement | Tasks |
|---|---|
| FR-001, reproducible audit record | T001–T007, T009 |
| FR-002, disposition of each failure | T008–T009 |
| UX-19, keyboard and focus | T003, T007 |
| UX-20, contrast and non-color cues | T004, T007 |
| UX-21, zoom and reflow | T005, T007 |
| UX-22, AT, labels, status, targets and motion | T006–T007 |
| SC-001, complete evidence matrix | T002–T009 |

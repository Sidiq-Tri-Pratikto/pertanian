# Tasks for the usability study kit

**Input** [spec.md](spec.md), [plan.md](plan.md), PRD section 20 and the 040 evidence inventory. Paths are relative to the TemuRiset project.

## Phase 1. Setup

- [X] T001 Map the proposed 5–8-person sample, personas, synthetic cases, and currently available journey steps to `docs/research/README.md`. Identify J04/J05 and any 040 findings that affect a task or study condition.

## Phase 2. Foundation

- [X] T002 Define a facilitator checklist, inclusion and accommodation plan, resets and equivalent setup for keyboard-only, mobile and assistive-technology conditions in `docs/research/README.md`. Establish the consent and data-handling workflow before any participant session.

## Phase 3. User Story 1, Learn from 5–8 people (P1)

**Independent test.** A facilitator can follow one representative inventor, company manager and partner task from the kit using a synthetic case, classify a blocked task without treating it as participant failure, and transfer an empty observation row into the results template with explicit denominators and timing rules.

- [X] T003 [P] [US1] Write neutral Indonesian prompts for inventors, company managers and partners in `docs/research/task-scripts.md`. Keep success criteria and optional moderator assistance in a separate facilitator section. Include an open-ended approval-versus-funding comprehension prompt. Keep prepared-profile pitch and slot selection tasks mapped to the PRD measures, with J04/J05 dependencies visible and those tasks gated.
- [X] T004 [P] [US1] Draft Indonesian invitation and consent copy and the facilitator's data-handling instructions in `docs/research/consent.md`. Make participation voluntary, recording separately opt-in, and specify pseudonyms, approved storage, access, retention/deletion, withdrawal and exclusions from version control.
- [X] T005 [P] [US1] Create blank observation and results templates in `docs/research/observations.md` and `docs/research/results-template.md`. Capture completion, error, assistance, time, device and assistive technology, and comprehension that approval opens discussion. Define timing start/stop rules and distinct categories for unassisted, assisted, failed, skipped and blocked tasks. Include the PRD's proposed ≥80% unassisted completion, <5 min prepared-profile pitch and <2 min slot selection targets as hypotheses, with denominators for each measure and a separately reported comprehension count.
- [X] T006 [US1] Verify the documents together with an internal synthetic walkthrough. Record the checked setup and unresolved task dependencies in `docs/research/README.md`. Leave the results blank pending independently consented sessions with real participants.

## Phase 4. Polish

- [X] T007 Check Markdown links, persona and condition coverage, neutral phrasing, and the absence of participant records or contact details in `docs/research/`. Record the kit's verified status in `specs/041-usability-kit/spec.md`.

## Dependencies and execution order

- T001 uses the 040 surface and condition inventory. T002 defines the shared facilitation protocol before T003–T005.
- T003, T004 and T005 can be drafted in parallel once the protocol is fixed. T006 reconciles them and T007 follows.
- The MVP is a ready-to-facilitate kit with empty templates and unavailable tasks labelled. A human study is a separate activity after consent and approved setup.

## Requirements coverage

| Requirement | Tasks |
|---|---|
| FR-001, keyboard, mobile and assistive-technology conditions | T001–T003, T005–T007 |
| Acceptance 1, persona scripts, consent and templates | T002–T006 |
| Acceptance 2, observed metrics, denominators and sample limits | T003, T005–T007 |
| SC-001, kit in docs/research and participant data excluded | T004–T007 |

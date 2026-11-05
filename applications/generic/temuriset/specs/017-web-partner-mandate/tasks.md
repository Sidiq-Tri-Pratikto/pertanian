# Tasks: Partner profile and mandate editor

**Input**: `specs/017-web-partner-mandate/spec.md`, `plan.md`, generated against commit `5e566fb` (spec 016)
**Branch**: `f/m4-partner-intake`, one commit per spec as in M3
**Tests**: Required. The roadmap says test first, and the plan has a test plan. Tests are written first and must fail.

**Paths** start at `applications/generic/temuriset/applications/temuriset-web/`. The reference screens are `src/views/needs/` and `src/features/needs/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 or US2 from `spec.md`

## Decisions resolved against the code

| ID | Decision | Why |
|---|---|---|
| D1 | "Tinjau mandat" is a client-side step that saves nothing. "Aktifkan versi N" sends `PUT`, then `POST /activate` unless the mandate is already `ACTIVE`, so N is the current number for a draft and the next number for a live mandate. If `PUT` succeeded and activation did not arrive, a retry does not save again while the values are unchanged. | 016 D1 and D14. A second `PUT` on a paused mandate would create a version nobody asked for. |
| D2 | After `STALE_VERSION`, `TR.VersionConflict` keeps every value. Its action reads the latest mandate and keeps the person's values, so the next attempt targets the new version. | US2 scenario 3. |
| D3 | A new requirement is one of a bounded list: narrative, stage, relationship form, document, current feature, budget range, contribution range, authority, entity. Narrative is labelled "Ditinjau manual". The client builds field, operator and value; the service still validates them. | The prototype adds narrative rows only, which would leave a new partner unable to state a typed requirement (FR09). |
| D4 | Profile editing lives on `/partners/[partyId]`, as a form under the empty state for a first profile and in a `TR.Disclosure` afterwards. | 017 FR-001 lists no other route. |
| D5 | Editing needs the own party and `edit_portfolio`. Without them, `/opportunities/[id]/edit` shows a denied state, and cards and forms offer no change. | Web rule: every screen has a permission-denied state. |
| D6 | "Tutup penerimaan" closes one mandate, after a confirming dialog, because a closed mandate cannot reopen. Pausing and resuming need no dialog. | 016 states; PRD: closing stops new pitches. |
| D7 | The external link is a real link that opens in a new tab. Clicking also records the handoff, without blocking the person. If recording fails, the screen says so. The copy says it opens another site, is not a sent pitch, and that TemuRiset notes the opening. | AC24. The prototype's "tidak tercatat" would be false, because the API records it. |
| D8 | A `per_investment` range shows its basis in the label, not as "selama per investasi". | `FinancialScope` writes "selama" before any period. |
| D9 | `closes_at` and `kind` have no control yet: a save keeps the stored `closes_at`, and new mandates are `SPECIFIC`. A general intake still shows its label when one exists. | S09 lists timing as text, and neither field is in this spec's scenarios. |
| D10 | `TR.RequirementRow` gains an optional `headingLevel`, and `Link` runs `onClick` without preventing navigation. | Heading order under an `h2`; D3 in `architecture.md` already chose real links. T022 records both. |
| D11 | The source-reported scenario (US1 scenario 2) runs in jsdom, and Playwright covers the external route with an owner-confirmed profile. | The API refuses to create a source-reported profile, and 021 seeds them later. |

---

## Phase 1: Setup

- [X] T001 [P] Add the `external` icon from the design system to `src/components/tr/Icon.tsx`
- [X] T002 [P] Write the intake types, labels and money helpers in `src/features/intake/model.ts`
- [X] T003 [P] Write the API calls in `src/features/intake/api.ts`: save profile, create, save, read and move mandate, record handoff

---

## Phase 2: Foundational

- [X] T004 Write failing tests for the ports in `tests/components.test.tsx`: `RequirementRow` result "Tidak berlaku" and later-stage note, `Disclosure`, external `Link` with its hidden "membuka situs lain"
- [X] T005 Port `src/components/tr/RequirementRow.tsx`, `src/components/tr/Disclosure.tsx` and `src/components/tr/Link.tsx` (D10)

**Checkpoint**: Ports pass, and no screen uses them yet

---

## Phase 3: User Story 1 - Partner profile reads clearly to both sides (Priority: P1) 🎯 MVP

**Goal**: S08 and the mandates list read clearly to the owner and to an inventor

**Independent Test**: Render Mitra A as owner and Recipient E as an inventor.

- [X] T006 [P] [US1] Write failing tests in `tests/intake.test.tsx`: owner card shows status, version, outcome, support and `FinancialScope` with "Ubah mandat" and "Tutup penerimaan" (scenario 1); E shows "Dilaporkan sumber", "Ketersediaan belum dikonfirmasi" and the external copy (scenario 2); a click records one handoff with a key and failure says so (D7); no profile shows the empty state, and a first save sends `expected_version: null`; a member without `edit_portfolio` gets no controls (D5); list status and version (FR-002); pause, resume, close through its dialog (D6); `per_investment` label (D8); axe on each view
- [X] T007 [US1] Write `src/views/intake/MandateCard.tsx`: status, version, outcome, support, timing, `FinancialScope`, general intake label, availability reason, requirements in a `Disclosure`
- [X] T008 [P] [US1] Write `src/features/intake/MandateActions.tsx` and `src/features/intake/NewMandate.tsx`
- [X] T009 [P] [US1] Write `src/features/intake/ExternalRoute.tsx` (D7)
- [X] T010 [P] [US1] Write `src/features/intake/RangeFields.tsx` and `src/features/intake/ProfileForm.tsx`
- [X] T011 [US1] Write `src/views/intake/PartnerView.tsx` and `src/views/intake/MandatesView.tsx`
- [X] T012 [US1] Write `src/app/partners/[partyId]/page.tsx`, and replace `src/app/opportunities/page.tsx`

**Checkpoint**: US1 tests pass

---

## Phase 4: User Story 2 - Edit, review, then activate a mandate (Priority: P1)

**Goal**: S09 edits, reviews and activates a mandate without ever losing the person's values

**Independent Test**: Add a requirement to a draft, review it, and activate it. Repeat with a stale version.

- [X] T013 [P] [US2] Write failing tests in `tests/intake-editor.test.tsx`: stage and mode chosen on a new requirement, narrative labelled "Ditinjau manual", a typed stage requirement (scenario 1, D3); review shows `SummaryList` before "Aktifkan versi N", and nothing is sent until then (scenario 2, D1); a draft sends `PUT` then `POST /activate`, a live mandate `PUT` only; a retry after a lost activation does not save twice; validation returns to the form with a linked summary, including `partner_profile`; stale keeps edits and then targets the latest version (scenario 3, D2); `closes_at` and typed rows survive a save (D9); closed is read-only; denied state (D5); axe
- [X] T014 [US2] Write `src/views/intake/MandateReview.tsx`
- [X] T015 [US2] Write `src/features/intake/MandateForm.tsx`
- [X] T016 [US2] Write `src/views/intake/MandateEditView.tsx` and `src/app/opportunities/[id]/edit/page.tsx`

**Checkpoint**: Both stories pass in jsdom

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T017 Flip `profil-mitra` and `mandat` to `available` with `home: '/opportunities'` in `src/features/registry.ts`, and update `tests/registry.test.ts`
- [X] T018 Add `/api/v1/opportunities` to the server mock in `tests/pages.test.tsx`
- [X] T019 [P] Add `makePartnerProfile`, `makeMandate` and path tokens to `e2e/fixtures.ts`, and add the new routes to `e2e/routes.ts`, so overflow, axe with contrast and keyboard checks cover them
- [X] T020 [P] Write `e2e/intake.spec.ts`: edit, review and activate version 2 of A1 (SC-001), stale version keeps edits, external route with its copy and a recorded handoff
- [X] T021 [P] Update `README.md` if it lists routes, and set **Status** to `Built, awaiting review` in `../../specs/017-web-partner-mandate/spec.md`
- [X] T022 [P] Record D10 in the deviations table of `../../docs/roadmap/architecture.md`
- [X] T023 From the project folder, run `python3 docs/roadmap/check_traceability.py`, `make check` and `make e2e`, read the output, and name the runtime exercised in the PR description

---

## Requirement coverage

| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 routes | T006, T013, T020 | T012, T016 |
| FR-002 list | T006 | T011 |
| US1 scenario 1 | T006, T020 | T007, T008, T011 |
| US1 scenario 2 | T006 | T009, T011 |
| US2 scenarios 1–3 | T013, T020 | T015 |
| No-profile empty state, "Tidak berlaku" | T004, T006 | T005, T010, T011 |
| SC-001 | T019, T020 | T015–T017 |

---

## Dependencies & Execution Order

- **Setup → Foundational → US1 → US2 → Polish.** US2 needs `RangeFields` from T010 and `MandateCard` from T007.
- **Within a story**: tests, then components, then views, then routes.
- **Later specs**: 020 links to `/partners/[partyId]`, and 024 reads `target_availability`.

### Parallel Opportunities

- T001, T002 and T003
- T008, T009 and T010
- T019–T022

## Parallel Example: User Story 1

```text
Task: "Write src/features/intake/MandateActions.tsx and NewMandate.tsx"
Task: "Write src/features/intake/ExternalRoute.tsx"
Task: "Write src/features/intake/RangeFields.tsx and ProfileForm.tsx"
```

## Implementation Strategy

1. Finish Setup and Foundational.
2. Finish US1 and run its tests. S08 then reads clearly to both sides.
3. Finish US2 and run its tests.
4. Finish Polish, flip the registry only for what shipped, and land one commit: `feat(temuriset): add partner profile and mandate screens (spec 017)`.

## Notes

- A jsdom test never proves contrast, focus visibility or reflow, so T023 names the runtime.
- The client never decides a rule: it shows `target_availability`, and every refusal comes from the service.

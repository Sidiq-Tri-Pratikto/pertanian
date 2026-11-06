# Tasks for relationship and public profile screens

**Inputs** [Specification](spec.md), [plan](plan.md), the S15/S16 canvases, TR.PartnershipConsent and J05. Paths are relative to the TemuRiset project.

## Setup and foundations

- [X] T001 Inspect S15, S16, the J05/J05b prototype, the design-system component and the shipped S13 room.
- [X] T002 Generate the typed client from 030/031 and map the API's actions, eligibility, effective public fields and error envelopes in `applications/temuriset-web/src/features/relationships/`.

## US1 · Review and confirm one version

- [X] T003 [US1] Write consent and form behavior tests in `applications/temuriset-web/tests/relationships.test.tsx` for single/mutual confirmation, field locks, accessible errors and server-owned disclosure.
- [X] T004 [US1] Port TR.PartnershipConsent in `applications/temuriset-web/src/components/tr/PartnershipConsent.tsx`. Render the API's effective fields and keep choices unchecked until a person opts in.
- [X] T005 [US1] Build proposal and detail routes in `applications/temuriset-web/src/app/partnerships/` and their views in `applications/temuriset-web/src/views/relationships/`. Connect the actual room in `applications/temuriset-web/src/views/pitches/WorkspaceView.tsx`. Implement versioned confirmation, correction dialog, decline, live restriction and contest with acting context, stable intent keys and draft-preserving recovery.

## US2 · Read the public profile

- [X] T006 [US2] Implement the signed-out route at `applications/temuriset-web/src/app/profiles/[partyId]/page.tsx` and its view. Render only fields returned by the public projection. Link the active party's profile from Settings and provide biography publication controls for permitted editors.
- [X] T007 [US2] Exercise published/empty/denied views and profile disclosure with Testing Library and axe in `applications/temuriset-web/tests/relationships.test.tsx`.

## US3 · J05 and verification

- [X] T008 [US3] Use the real API and two browser sessions in `applications/temuriset-web/e2e/j05-relationship.spec.ts` to verify completed meeting, proposal, correction, same-version confirmation, live narrowing, and the signed-out public profile. Include an unrelated-account denial and responsive axe/reflow checks.
- [X] T009 [US3] Register accessible route states in `applications/temuriset-web/e2e/routes.ts`; flip only the two intended entries in `applications/temuriset-web/src/features/registry.ts`, and update corresponding tests and the web README.
- [X] T010 Run project checks, production Chromium and traceability. Record evidence and any design-system port deviation in `docs/roadmap/architecture.md` and `specs/032-web-relationship-profile/spec.md`.

## Order and coverage

T002 requires 030/031. T003 precedes T004/T005. T006/T007 can proceed independently of private forms. T008 follows the three routes, then T009/T010. FR-001 maps to T005/T006, UX-15/UX-16 to T003–T005/T008, S16 to T006–T008, and SC-001/J05 to T008–T010.

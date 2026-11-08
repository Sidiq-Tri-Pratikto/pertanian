# Tasks — Explore-first onboarding

- [x] T001 Align the constitution, error-copy policy, canonical PRDs, design handoff, affected specs, and roadmap.
- [x] T002 Prepare the spec, plan and tasks in `specs/047-explore-first-onboarding/` and check their consistency before coding.
- [x] T003 [US1] Extend router regressions in `applications/hematdaya-mobile/tests/demo-journey.test.tsx`.
- [x] T004 [US1] Update Welcome, returning-user routing, and Settings in `applications/hematdaya-mobile/src/app/`.
- [x] T005 [US2] Update Home and Devices CSV entries and exercise explicit import in `applications/hematdaya-mobile/tests/import.test.tsx`.
- [x] T006 [US2] Update the standalone prototype, reference copy, and `applications/hematdaya-mobile/e2e/smoke.yaml`.
- [x] T007 Verify local acceptance and record evidence here.

## Analysis

FR-001 through FR-003 map to T003 and T004. FR-004 maps to T005 and FR-005 to T006. Both success criteria are exercised by T007. Continue and demo confirmation have separate request assertions. CSV onboarding uses the existing workspace start. The bilingual policy describes the planned 049–050 transition, with Indonesian continuing as the default.

## Verification evidence

- Mobile `make check` passed lint, type checking and 576 tests across 29 suites. Expo exported Android, iOS and web bundles.
- Chrome verified Continue, returning to empty Home, explicit CSV entry and both demos in Expo Web and the standalone prototype. Expo used the core-only API and PostgreSQL 16. Continue created no workspace and each demo confirmation created one. No file chooser opened when entering the CSV screen.
- Prototype domain tests and roadmap traceability passed. The handoff snapshot and SHA-256 match the canonical English PRD. Native Android evidence comes from the hosted smoke.

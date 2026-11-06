# Tasks for same-version relationship records

**Inputs** [Specification](spec.md), [plan](plan.md), the J05 prototype oracle, and M9 starting commit `13e8132`. Paths are relative to the TemuRiset project.

## Setup and foundations

- [X] T001 Audit the carried API, migration and test paths in `applications/temuriset-api/app/relationships/` and `applications/temuriset-api/migrations/versions/0016_relationships.py`. Verify the migration applies after M8.
- [X] T002 Run the carried consent and relationship tests with the route coverage gate in `applications/temuriset-api/tests/integration/test_isolation.py`. Record the uncovered routes before editing.

## US1 · Propose, correct and confirm

- [X] T003 [US1] Register each private relationship route with a real fixture and valid unrelated-party request in `applications/temuriset-api/tests/integration/test_isolation.py`. Verify missing rights, wrong acting context, replay and same-version checks.
- [X] T004 [US1] Serialize proposals for the same completed pitch and expose eligibility for the form from the same authority in `applications/temuriset-api/app/relationships/service/service.py` and `applications/temuriset-api/app/relationships/router.py`. Verify an ineligible equity proposal, early proposal and a concurrent second proposal.
- [X] T005 [US1] Verify AC21 and AC52–AC54 with the carried tests in `applications/temuriset-api/tests/integration/relationships/test_partnerships.py` and the consent invariant in `applications/temuriset-api/tests/unit/relationships/test_consent.py`.

## US2 · Narrow and contest

- [X] T006 [US2] Verify restrictions apply to the effective projection, expansion keeps the prior confirmed version until both sides confirm, and contest hides public fields while private history stays in `applications/temuriset-api/tests/integration/relationships/test_partnerships.py`.

## Integration and polish

- [X] T007 Regenerate `contracts/openapi.json`, verify migration upgrade/downgrade/drift and run API checks. Record evidence in `specs/030-partnerships-api/spec.md`.

## Order and coverage

T001–T002 precede T003–T006. T007 gates 032's generated client. FR-001/FR-003 and AC21/AC52–AC54 map to T003–T005. FR-002 and the restriction/contest story map to T005–T006. SC-001 maps to T005–T007.

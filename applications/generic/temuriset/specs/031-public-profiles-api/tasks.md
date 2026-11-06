# Tasks for public profiles

**Inputs** [Specification](spec.md), [plan](plan.md), and the S16 prototype. Paths are relative to the TemuRiset project.

## Setup

- [X] T001 Inspect carried public profile routes, migration `applications/temuriset-api/migrations/versions/0017_public_profiles.py`, and the AC55–AC57 cases in `applications/temuriset-api/tests/integration/relationships/test_profiles.py`.

## US1 · Publish only what is authorized

- [X] T002 [US1] Add a signed-out regression for a relationship without name consent, a live name restriction, and cache headers in `applications/temuriset-api/tests/integration/relationships/test_profiles.py`. Keep own settings scoped and register route exceptions and denials in `applications/temuriset-api/tests/integration/test_isolation.py`.
- [X] T003 [US1] Withhold counterpart identifiers and cross-party links when the name is private, keep published inventions distinct from private drafts, and send a no-store public response in `applications/temuriset-api/app/relationships/service/public_profile.py` and `applications/temuriset-api/app/relationships/router.py`.
- [X] T004 [US1] Verify AC55–AC57, unpublished biography, absence of private strings, and one relationship with two authorized published invention links in `applications/temuriset-api/tests/integration/relationships/test_profiles.py`.

## Integration and polish

- [X] T005 Regenerate `contracts/openapi.json`, verify migration and tests, and record the outcome in `specs/031-public-profiles-api/spec.md`.

## Order and coverage

T002 precedes T003. T004 verifies the projection with 030. T005 gates 032's public read. FR-001, FR-002 and AC55–AC57 map to T002–T004. SC-001 maps to T004–T005.

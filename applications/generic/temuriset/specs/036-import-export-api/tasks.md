# Tasks: JSON import and export

**Input**: `specs/036-import-export-api/spec.md` and `specs/036-import-export-api/plan.md`, checked against the M7 main baseline and the carried 034 work.
**Tests**: AC06 and AC61–AC63, job lifecycle, API isolation, browser preview and the 1,000-invention scenario. Observe the targeted tests fail before implementing each increment.
**Paths**: API paths are relative to `applications/temuriset-api/`. Paths starting with `applications/temuriset-web/`, `contracts/`, `docs/` or `specs/` are relative to the TemuRiset project.

## Phase 1: Setup

- [X] T001 Confirm the worker, access, portfolio, intake and document service interfaces in `app/worker/registry.py`, `app/access/service/policy.py`, `app/portfolio/service/service.py`, `app/intake/service/service.py` and `app/documents/service/service.py`. Confirm 010 and 016 are present and identify the active Alembic head under `migrations/versions/`.
- [X] T002 Create the portability module under `app/portability/` and record the v1 file contract, bounds, provenance, supported field mapping and result expiry in `specs/036-import-export-api/plan.md`.

## Phase 2: Foundational

- [X] T003 Add import run, external reference and export job records in `app/portability/repository/sqlalchemy/models.py` and their queries and state transitions in `app/portability/repository/sqlalchemy/repository.py`. Enforce a unique external reference per managing party, system and ID, and retain the staged digest, stage job references, progress, version and recorded export dependencies.
- [X] T004 Add the next portability revision in `migrations/versions/` after the integrated single head. Register the models in `migrations/env.py`, add cleanup in `tests/integration/conftest.py`, and verify upgrade, downgrade, re-upgrade and `alembic check`. Keep existing migrations intact.
- [X] T005 Define validated payloads and projections in `app/portability/model/schema.py`. Define ownership, context, live membership and resource access through `app/access/service/policy.py` and `app/access/service/service.py`, with private references hidden from another account or party.

## Phase 3: User Story 1 - Preview before apply; never duplicate or overwrite silently (P1)

**Goal**: Validate and preview a managing party's JSON, apply only safe updates, and download a job result only while the dependencies remain authorized.

**Independent test**: Validate and preview 1,000 records without changing any invention. Apply twice against the same external IDs and confirm a reviewed conflict stays unchanged. Export a result with a document dependency, remove its grant or the requester's membership, and confirm the gateway denies and expires the result.

### Tests

- [X] T006 [P] [US1] Write schema and boundary tests in `tests/unit/portability/test_schema.py` for missing or unknown schema version, invalid or repeated external IDs, malformed and oversized input, provenance, unknown values, explicit private field mapping, the optional source-reported partner profile and no organization merge by name. Assert that a claimed confirmed relationship stays source-reported.
- [X] T007 [P] [US1] Write API/worker tests in `tests/integration/portability/test_imports.py` for validation, preview and apply jobs and their separate status, observable progress, cancel before apply, a 1,000-invention import, repeated and concurrent applies scoped by party (AC61), and conflicts with reviewed rights in draft or published history (AC62). Assert no writes before apply, preserve fields omitted from the import, and exercise stale preview, retry and race behavior.
- [X] T008 [P] [US1] Write API/worker tests in `tests/integration/portability/test_exports.py` for a successful authorized JSON attachment, a grant revoked or expired before generation and between generation and download (AC63), membership removed at either point (AC06), expiry surviving denial, context switch, and an unrelated caller unable to invalidate someone else's result.
- [X] T009 [P] [US1] Add route probes to `tests/integration/test_isolation.py` and registered error-envelope and sanitized logging checks to `tests/integration/portability/test_failure_paths.py`. Verify a raw file, private preview value, source label and storage key stay out of diagnostics and job responses.

### Implementation

- [X] T010 [US1] Implement the versioned JSON contract in `app/portability/service/schema_v1.json` and enforce it in `app/portability/service/imports.py`. Use bounded private staging and typed domain validation. Reject duplicate or invalid references within a file and keep raw payloads out of jobs and audit events.
- [X] T011 [US1] Implement separate validation and preview jobs and bounded progress in `app/portability/service/imports.py` and `app/portability/service/jobs.py`. Capture normalized row actions, permissions, source provenance, conflict keys and the exact versions compared. Read reviewed facts and claims through `app/portfolio/service/service.py`. Keep source-reported relationship assertions separate from confirmed records.
- [X] T012 [US1] Implement apply and cancel in `app/portability/service/imports.py` and `app/portability/repository/sqlalchemy/repository.py`. Lock the run and external key for upsert, use portfolio writes and the 016 first-source directory profile service, and recheck authorization and versions inside the worker before changes. Skip unresolved conflicts and preserve reviewed facts and immutable published versions. Use idempotent bounded units of work with durable progress, and check cancellation before the next unit.
- [X] T013 [US1] Implement queued generation, bounded expiry and authenticated attachment delivery in `app/portability/service/exports.py` and `app/documents/service/service.py`. Check exact resource dependencies at enqueue, generation and gateway access, persist denied-result expiry before the error is returned, and schedule private artifact cleanup. A hidden request by an unrelated account must have no effect.
- [X] T014 [US1] Wire portability job registration in `app/worker/__main__.py` and the HTTP routes in `app/portability/router.py` and `app/main.py`. Use platform jobs, idempotency, version checks, audit and outbox. Include the operation ID on consequential responses and bound request bodies and status/preview output.
- [X] T015 [US1] Run `make openapi` and verify `contracts/openapi.json` documents stage state, private preview, cancellation, expiry and failure responses. Run `make generate-api` from `applications/temuriset-web/` and check `applications/temuriset-web/src/api/schema.generated.ts`.
- [X] T016 [US1] Write focused view and browser tests in `applications/temuriset-web/tests/portability.test.tsx` and `applications/temuriset-web/e2e/portability.spec.ts`. Verify file selection, separate validate/preview/apply state, review before confirmation, skipped conflicts, progress, cancellation and failure with no lost selection. Verify authorized export and denial, keyboard flow, 320 CSS-pixel reflow and axe.
- [X] T017 [US1] Add the authorized upload, preview and minimal export controls in `applications/temuriset-web/src/app/inventions/import/page.tsx`, `applications/temuriset-web/src/features/portability/api.ts` and `applications/temuriset-web/src/views/PortabilityView.tsx`. Reuse generated types and the shared same-origin API and failure helpers. Show acting context before apply, and render the server's actions, conflicts and status.

## Phase 4: Polish and release checks

- [X] T018 Update `applications/temuriset-api/README.md` and `applications/temuriset-web/README.md` with the file envelope, supported fields, bounds, preview, progress, cancellation and download route. Document how an owner resolves a conflict and obtains a fresh preview.
- [X] T019 When the route and acceptance checks pass, switch only `impor-ekspor` to `available` with home `/inventions/import` in `applications/temuriset-web/src/features/registry.ts` and update `applications/temuriset-web/tests/registry.test.ts`.
- [X] T020 Run targeted API and web tests, migration checks, `make check`, browser checks and `python3 docs/roadmap/check_traceability.py` from the paths documented in `AGENTS.md`. Record AC06, AC61–AC63, the 1,000-record job and any outstanding checks in this file. Update the status in `specs/036-import-export-api/spec.md` only after its acceptance criteria pass.

## Requirement coverage

| Requirement | Evidence | Implementation |
|---|---|---|
| FR-001 and SC-001 | T006, T007, T016, T020 | T003–T005, T010–T012, T014–T017 |
| FR-002 and AC61 | T006, T007 | T003, T010–T012 |
| AC62 | T006, T007, T016 | T011, T012, T017 |
| FR-003, AC06 and AC63 | T008, T009, T016 | T005, T013–T015, T017 |
| Explicit mapping, no name-based merges and source-reported relationships | T006, T007 | T005, T010–T012 |
| Progress and cancellation | T007, T016 | T003, T011, T012, T014, T017 |
| Registry availability | T016, T019, T020 | T017, T019 |

## Dependencies and execution order

- Setup precedes foundation. T004 follows T003. The API tests precede the corresponding implementations.
- T010 → T011 → T012 → T014 for import. T013 follows the foundation and can proceed separately from T010–T012. Both flows need T014 before contract generation. Browser tests and implementation follow T015.
- The portability revision number follows the actual integrated head. Specs 027–033 do not need to ship for the source-reported v1 import. Specs 034 privacy requests and 036 portability exports have separate contracts and authorization scopes.

## Parallel example for US1

Run T006 for schema validation, T007 for import lifecycle, T008 for export permission changes and T009 for isolation and diagnostics in separate test files after the foundation. Use a single owner for the shared router and generated contracts.

## Implementation strategy

Deliver the API-backed validate, preview and apply flow first. Add queued export and verify grant and membership revocation. Verify the minimal web workflow against the generated contract before changing the registry.


## Standalone verification

- PostgreSQL migration 0015 upgraded from the M7 head, downgraded, re-upgraded, and passed `alembic check` both times. The integrated revision follows the moderation revision.
- API `make check` passed 773 tests with 95.68% line coverage. Twelve focused schema cases passed after the final schema tests were added.
- AC06 and AC63 passed for removal or expiry before generation and before delivery. The requester lost access permanently, a replacement grant could not revive the original result, and a different account could not invalidate it.
- AC61 passed for scoped replay, preservation of omitted fields, source-only assertions, and two competing first applies. AC62 passed for reviewed rights in the draft and published version.
- The 1,000-invention test completed the preview with no invention writes. One 50-record apply checkpoint committed before cancellation and no later checkpoint wrote records.
- Web `make check` passed 248 tests with 87.57% line coverage. Production Chromium passed all 8 feature checks across 320, 360, 768 and 1280 CSS pixels. Eleven standard route checks passed, covering axe, reflow, 200% text and keyboard focus.
- OpenAPI and generated TypeScript were regenerated. Traceability mapped 143 requirements across 45 specs.

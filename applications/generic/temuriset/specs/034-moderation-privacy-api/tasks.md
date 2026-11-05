# Tasks: Reports, moderation and privacy requests

**Input**: `specs/034-moderation-privacy-api/spec.md`, `plan.md`, generated against commit `c90da37` (`origin/main`, end of M4)
**Branch**: `f/m10-moderation-privacy`, one commit per spec as in M3 and M4
**Tests**: Required. The roadmap says test first. Tests are written first and must fail.

**Paths** start at `applications/generic/temuriset/applications/temuriset-api/`.

## Decisions resolved against the code

The spec and plan leave these open, or assume work that is not built yet. T028 records them.

| ID | Decision | Why |
|---|---|---|
| D1 | The migration is `0009_moderation.py`, after `0008`. | The plan's `0019` assumes M5–M9 are merged, and they are not. Specs 018 onward pick their number when they are built. |
| D2 | Operators are rows in `operator_grants` (account, scope `moderation`), granted by a command, not a route. Everyone else gets `NOT_FOUND` on `/operator/*`. | FR-001: a scoped capability, not a persona. 007 FR-002's list is per organization, and an operator acts for no organization. The isolation harness also expects `NOT_FOUND`. |
| D3 | A case-specific file grant is a row in `operator_file_grants` (report, document version, operator, written purpose, expiry), created by a command. The central access policy checks case visibility and the exact grant on every download, including range requests. Return `NOT_FOUND` for hidden resources and `FORBIDDEN` for a visible case whose file action is denied. Record a sanitized refusal that survives the failed request. | US1 scenario 3, SC-001, and the PRD authorization table: "documented case-specific grant". |
| D4 | A suspendable listing is `INVENTION`, `OPPORTUNITY` or `PARTNER_PROFILE`. Discovery (018) does not exist, so "public discovery hides it" applies to today's public reads: `/inventions/{id}/public`, `/partners/{id}`, others' opportunity reads and lists. `listing.suspended` and `listing.restored` are published for 018's projection. | US1 scenario 2. These are the only public surfaces. |
| D5 | "New actions stop": saving and publishing an invention, new references to it, saving a profile, starting, saving or activating a mandate, and handoffs. New public code `LISTING_SUSPENDED` (409). "Ongoing cases stay handled": the owner keeps reading, can archive, pause and close, and `target_availability` answers `SUSPENDED`. | PRD FR22. Winding down must stay possible. |
| D6 | A report accepts any object by type and optional id, plus a label, and never checks that the object exists. Suspending does check. | Checking on report would let anyone probe for private objects. The object may be a pitch or message that does not exist in the system yet. |
| D7 | The reporter response exposes the case number and status. Operator notes, actions, identities and private reasons stay in the operator case. Reports are found by account with access checked through the central policy. | US1 scenario 1 and AC64. The case number also supports the confirmation in 035. |
| D8 | `retention_policies` rows are seeded by the migration. The API derives each deletion answer from the applicable policy and audit holds, including retained categories, reasons and `policy_version`. Recheck applicable holds before applying removal. Each `REMOVE` row must have a remover in code, enforced by a test. | FR-002 and AC66. A category can be marked removed only after its remover succeeds. |
| D9 | A deletion request answers at once with `to_remove` and `retained`. An authorized operator starts fulfilment. Commit the database removals, audit and erase jobs together. A category stays pending while its erase job is outstanding, including after a retryable failure. Move it to `removed` after successful erasure and record one final delivery intent for the original address. Verify delivery with the existing dev mailbox. Production mail depends on 042, so it remains a pilot dependency. The answer explains that copies already downloaded cannot be recalled and that retained backups expire under their own policy. | US2 scenario 1, AC66, and the binding audit/outbox rules. Adds `/operator/privacy-requests`. |
| D10 | Removers: anonymize the account and personal party, delete sign-in codes and revoke sessions, withdraw personal listings (archive inventions, close requests and mandates, delete the partner profile), and erase personal document bytes through a worker job, with grants revoked. Listing history, audit, download events, reports, organization data and backups are `RETAIN`. | Everything listed as removed is really removed. History stays because versions are referenced, and the answer says so. |
| D11 | Retention periods read "Periode final ditetapkan sebelum pilot". | PRD: publish periods before a real pilot. No legal period is invented here. |
| D12 | `GET /privacy-requests/{id}/export` rebuilds the export on each read. Apply the central access policy to request ownership, current acting context and each included resource. Define an explicit requester-data field allowlist. Include organization data only where the export policy authorizes that data for the requester. `edit_portfolio` alone does not grant bulk export. Include permitted document metadata only. | US2 scenario 2 and the binding authorization rules for exports. |
| D13 | Consequential POSTs use the platform `Idempotency-Key` and return `operation_id`. First creates send `expected_version: null`; mutations of an existing request or case send its current version. Carry the acting context where required. Apply the same rules to operator fulfilment, with one committed effect across retries or competing operators. | Constitution principles 6 and 11, and the binding acting-context, version and idempotency rules. |

---

## Phase 1: Setup

- [X] T001 Create `app/moderation/` per rule 005: `__init__.py`, `model/`, `repository/sqlalchemy/`, `service/`
- [X] T002 [P] Add `APP_LISTING_SUSPENDED` to `app/core/errors/codes.py` and `app/core/errors/public.py`, with a row in `../../docs/error-handling/catalog.md`

## Phase 2: Foundational

- [X] T003 Write the ORM records in `app/moderation/repository/sqlalchemy/models.py`: reports, operator actions, operator grants, operator file grants, listing suspensions, privacy requests, retention policies
- [X] T004 Write `migrations/versions/0009_moderation.py` after the merged `0008_intake.py`, seeding `retention_policies` and adding account-level `retention_holds`
- [X] T005 Import the records in `migrations/env.py` and register the new tables except `retention_policies` in `tests/integration/conftest.py`. Run the migration up, down and up, then run `alembic check`
- [X] T006 Write `app/moderation/model/schema.py` and `app/moderation/repository/sqlalchemy/repository.py`. Define the request versions, acting context, operation results and status fields used by both stories (D9, D13)

## Phase 3: User Story 1 - Report privately; operators act within scope (Priority: P1) 🎯 MVP

**Independent Test**: Report an impersonation, act on it as an operator, and read it back as the reporter and as a stranger.

- [X] T007 [P] [US1] Write failing tests in `tests/integration/moderation/test_reports.py`: private case with status only (AC64), reason required, no target existence probe, scope-limited queue and actions, transitions, audit, stale context/version, replay and key conflict. Verify reports have no public reputation effect and reporting reasons or private content stay out of analytics
- [X] T008 [P] [US1] Write failing tests in `tests/integration/moderation/test_suspension.py`: current public reads hide, new actions stop with `LISTING_SUSPENDED` including activation of already-linked requests, the owner keeps reading and can wind down, `target_availability` says `SUSPENDED`, lifting restores, events are published
- [X] T009 [P] [US1] Write failing tests in `tests/integration/moderation/test_operator_files.py`: refusal audited without a grant, exact grant served and audited, wrong case/version and expired or revoked grant refused, range requests reauthorized, hidden resources indistinguishable from missing resources (SC-001)
- [X] T010 [US1] Implement `app/moderation/service/suspension.py`
- [X] T011 [US1] Apply suspension in `app/portfolio/service/service.py`. Enforce it when starting or activating linked requests through `app/needs/service/service.py` and `app/funding/service/service.py`, including drafts linked before suspension
- [X] T012 [US1] Apply suspension in `app/intake/service/service.py` and `app/intake/router.py`, and add `SUSPENDED` to `AvailabilityReason` in `app/intake/model/models.py`
- [X] T013 [US1] Implement `app/moderation/service/reports.py` with a private reporter projection, scoped operator actions, transactional audit and D13. Implement central access decisions in `app/access/service/policy.py`
- [X] T014 [US1] Reuse the protected download gateway in `app/documents/router.py` and `app/documents/service/service.py`. Authorize case-specific access through `app/access/service/policy.py` and persist sanitized audit evidence for successful and denied attempts (D3)
- [X] T015 [US1] Add report and operator routes in `app/moderation/router.py`, and register the router in `app/main.py`
- [X] T016 [US1] Add operator and case-file grant management in `app/moderation/__main__.py`, including withdrawal. Verify command scope, case binding and grant audit in `tests/integration/moderation/test_commands.py`

## Phase 4: User Story 2 - Privacy requests tell the truth (Priority: P1)

**Independent Test**: Request a deletion, read the answer, fulfil it as an operator, then check that what it says was removed is gone and what it says was kept is still there.

- [X] T017 [US2] Write failing tests in `tests/integration/moderation/test_privacy.py`: an applicable audit hold retains the affected category with its reason and policy version, the answer explains limits on prior copies and backups (AC66), and each `REMOVE` row has a remover (FR-002). Cover delayed/failed erase, successful erase and one final delivery intent and dev mailbox outcome, one open deletion per account, scoped and audited fulfilment, stale version, competing operators, replay and key conflict. Assert permitted requester data only, including a same-organization editor denied an ungranted resource and permission loss after the export request
- [X] T018 [US2] Add party-wide removal functions in `app/identity/service/service.py`, `app/access/service/service.py`, `app/portfolio/service/service.py`, `app/needs/service/service.py`, `app/funding/service/service.py`, `app/intake/service/service.py` and `app/documents/service/service.py`, each through its own repository
- [X] T019 [US2] Add `delete` to `app/documents/service/storage_service.py` and an idempotent `documents.erase` job in `app/documents/service/jobs.py`. Persist successful erase completion for the request and exercise failure and retry
- [X] T020 [US2] Implement policy- and hold-based retention answers and removers in `app/moderation/service/retention.py` (D8–D11)
- [X] T021 [US2] Implement request lifecycle, export and fulfilment in `app/moderation/service/privacy.py`. Enforce D12 through `app/access/service/policy.py` at download time. Use D13 for writes and finalize deletion and notification only when all removals are confirmed (D9)
- [X] T022 [US2] Add privacy routes in `app/moderation/router.py`

## Phase 5: Polish

- [X] T023 Add the new routes to `tests/integration/test_isolation.py`: creating one's own report or request is not a data route, and everything else reveals nothing
- [X] T024 [P] Write `tests/integration/moderation/test_failure_paths.py` per rules 003 and 008. Exercise report validation, denied file access, stale or conflicting fulfilment, and erase or notification failures. Assert the public message, code, reference, sanitized record and recovery guidance. Verify a fake secret in a reason or private file stays out of diagnostics
- [X] T025 Run `make openapi` and verify `../../contracts/openapi.json` covers the new routes, privacy states and version semantics. Run `make generate-api` in `../temuriset-web/` before 035 consumes the contract
- [X] T026 [P] Add routes and test rows to `README.md`
- [X] T027 [P] Update `../../specs/034-moderation-privacy-api/plan.md` with the actual migration, route inventory, policy and worker files. Set **Status** in `../../specs/034-moderation-privacy-api/spec.md` to match the evidence, recording the deferred discovery check
- [X] T028 [P] Record D2–D5 and D8–D13 in `../../docs/roadmap/architecture.md`. In `../../specs/018-discovery-api/plan.md` require a test that suspended listings disappear from discovery and restoration makes eligible listings visible again. In `../../specs/023-pitch-submission-api/plan.md` track the submission retention policy. Coordinate the room report link with `../../specs/026-web-pitch-workspace/plan.md` and 035
- [X] T029 Run `python3 docs/roadmap/check_traceability.py` and `make check` from the project folder, and read the output

## Requirement coverage

| Requirement | Tests | Implementation |
|---|---|---|
| FR-001, AC64, US1 scenario 1 | T007, T009, T016, T017 | T013–T016, T021 |
| US1 scenario 2 | T008 for current public reads; discovery projection test depends on 018 (T028) | T010–T012, T028 |
| US1 scenario 3, SC-001 | T009 | T014–T016 |
| FR-002, AC66, US2 scenario 1 | T017, T024 | T018–T022 |
| US2 scenario 2 | T017, T023 | T021, T022 |
| Edge cases: reports do not affect public reputation and analytics omit private contents | T007, T024 | T013–T015, T021 |

## Dependencies & Execution Order

- **Setup → Foundational → US1 → US2 → Polish.** Later specs: 035 reads these routes.
- T005 follows T003–T004 so migration validation sees the registered models. T007–T009 can be written in parallel after T006. T017 precedes privacy implementation. T025 must precede the 035 client integration.
- T015 and T022 break `test_every_route_is_covered` until T023 lands, so T023 belongs in the same commit.

## Implementation Strategy

Finish US1, then US2, then land one commit: `feat(temuriset): add reports, moderation and privacy requests (spec 034)`.

## Validation

- Migration 0009 passed upgrade, downgrade, upgrade and `alembic check` on an isolated PostgreSQL 16 database.
- API `make check` passed 532 tests at 92.37% line coverage. The focused moderation suite then passed all 9 tests with the final suspension, export and competing-fulfilment cases.
- OpenAPI matches the generated contract. Traceability maps 143 requirements across 45 specs. The discovery projection acceptance check remains with 018.

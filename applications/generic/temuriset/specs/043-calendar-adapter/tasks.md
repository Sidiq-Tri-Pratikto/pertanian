# Tasks for the gated external calendar adapter

**Input** [Specification](spec.md), [plan](plan.md) and PRD FR17/AC68.

## Phase 1 · Setup

- [X] T001 Locate the existing proposal, booking and ICS entry points in `applications/temuriset-api/app/scheduling/router.py`, `applications/temuriset-api/app/scheduling/service/service.py` and `applications/temuriset-web/src/features/scheduling/SchedulePanel.tsx`.

## Phase 2 · Foundations

- [X] T002 Reuse the 042 authenticated envelope in `applications/temuriset-api/app/core/secret_envelope.py`. Add the independent calendar key, default-off loopback settings and startup tests in `applications/temuriset-api/app/core/settings.py`, `applications/temuriset-api/app/capabilities/service/configuration.py`, `applications/temuriset-api/tests/unit/capabilities/test_configuration.py` and `applications/temuriset-api/.env.example` (FR-001, FR-004).

## Phase 3 · US1 (P1) · Viewer-owned free/busy availability

**Independent test.** Complete a synthetic account connection and read a visible proposal through the existing schedule route. Assert advisory busy and non-overlap states. Disconnect and confirm a slot and its ICS file with external availability unknown.

- [X] T003 [P] [US1] Add OAuth and relay contract tests for limited scope, single-use account/session-bound state, failure privacy, expiry, revocation and cross-account isolation in `applications/temuriset-api/tests/integration/scheduling/test_calendar.py` and register account calendar routes in `applications/temuriset-api/tests/integration/test_isolation.py` (FR-001, FR-004, SC-001).
- [X] T004 [P] [US1] Add advisory overlap, in-flight revocation, fallback, concurrent booking and ICS cases in `applications/temuriset-api/tests/integration/scheduling/test_scheduling.py` (FR-002, FR-003, SC-001).
- [X] T005 [P] [US1] Add accessible owner connect/disconnect and advisory/off UI tests in `applications/temuriset-web/tests/calendar.test.tsx` and `applications/temuriset-web/tests/schedule.test.tsx` (FR-002–FR-004, SC-001).
- [X] T006 [US1] Add a new migration after the current head in `applications/temuriset-api/migrations/versions/` and owner/version-scoped connection and pending state persistence in `applications/temuriset-api/app/scheduling/repository/sqlalchemy/models.py` and `applications/temuriset-api/app/scheduling/repository/sqlalchemy/repository.py` (FR-001).
- [X] T007 [US1] Implement the bounded local and off adapters and OAuth flow in `applications/temuriset-api/app/scheduling/service/calendar_adapter.py` and `applications/temuriset-api/app/scheduling/service/calendar_connection.py`. Expose owner-scoped routes in `applications/temuriset-api/app/scheduling/router.py` and `applications/temuriset-api/app/scheduling/model/schema.py`. Document mapped errors in `docs/error-handling/catalog.md`. Prevent callback-query logging in the local run path through `applications/temuriset-api/Makefile` and the application logging configuration (FR-001, FR-003, FR-004).
- [X] T008 [US1] Add the advisory schedule read projection in `applications/temuriset-api/app/scheduling/service/service.py` and `applications/temuriset-api/app/scheduling/model/schema.py`. Keep the existing booking and ICS paths independent of external availability (FR-002, FR-003).
- [X] T009 [US1] Add validated local manifest status in `applications/temuriset-api/app/capabilities/router.py` and `applications/temuriset-api/app/capabilities/service/service.py`. Wire S18 and S14 in `applications/temuriset-web/src/app/settings/page.tsx`, `applications/temuriset-web/src/views/SettingsView.tsx`, `applications/temuriset-web/src/views/settings/CalendarConnection.tsx`, and `applications/temuriset-web/src/features/scheduling/SchedulePanel.tsx` (FR-002–FR-004).

## Phase 4 · Verification and activation

- [X] T010 Refresh `contracts/openapi.json` and `applications/temuriset-web/src/api/schema.generated.ts`; run migrations, targeted tests and full gates in `Makefile`. Document safe settings and callback behavior in `applications/temuriset-api/README.md` and record local evidence here (SC-001).
- [ ] T011 Record contracted provider, approved free/busy consent and credential-handling review, and staging contract, disconnect and scheduling evidence in `specs/043-calendar-adapter/spec.md` (FR-004, SC-002).
- [ ] T012 After T011, enable the approved configuration in `applications/temuriset-api/app/capabilities/service/configuration.py` and promote only the calendar registry entry in `applications/temuriset-web/src/features/registry.ts` after deployment verification (FR-004).

## Dependencies and parallel work

T002 depends on the shared envelope from 042 T002. T003–T005 can run in parallel. T006 precedes T007 and T008. T009 consumes the route and manifest contracts. The local MVP is the viewer-owned connection and advisory read with the unchanged internal journey, verified in T010. T011–T012 are external activation work. Apply 043 migrations and regenerate contracts after 042.


## Local verification

- The isolated API `make check` passed 969 tests with 96.10% line coverage on native PostgreSQL 16. The focused startup, OAuth, scheduling and route isolation run passed 204 tests. The follow-up OpenAPI unit run passed five tests and verified the documented 303 redirects.
- The web `make check` passed 281 tests with 81.87% line coverage on Node 24. The refreshed client contract also passed `make typecheck`.
- Alembic upgraded to `0021`, downgraded to `0020` and upgraded again. The repository migration compatibility harness ran both API versions and workers with synthetic data across the `0020` to `0021` boundary in a disposable database.
- Chromium against a local production web build exercised read-only consent and the direct callback, own-only S14 availability, provider-confirmed disconnect, unknown fallback, internal slot confirmation and the ICS download. The S18 calendar region had no axe violations or horizontal overflow at 320 CSS pixels. The Uvicorn callback access record contained the path and 303 status without the query.
- These checks used synthetic accounts and a literal-loopback provider. T011 and T012 require the separately approved provider and staging evidence.

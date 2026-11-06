# Tasks for the gated email delivery adapter

**Input** [Specification](spec.md), [plan](plan.md) and PRD FR16/AC46.

## Phase 1 · Setup

- [X] T001 Identify existing delivery callers and the domain and worker transaction boundaries in `applications/temuriset-api/app/identity/service/service.py`, `applications/temuriset-api/app/access/service/service.py`, `applications/temuriset-api/app/moderation/service/privacy.py` and `applications/temuriset-api/app/worker/loop.py`.

## Phase 2 · Foundations

- [X] T002 Add the shared authenticated secret envelope in `applications/temuriset-api/app/core/secret_envelope.py` with a purpose/key separation test in `applications/temuriset-api/tests/unit/core/test_secret_envelope.py`. Add runtime dependencies to `applications/temuriset-api/pyproject.toml` and `applications/temuriset-api/uv.lock` as needed (FR-001).
- [X] T003 Add default-off loopback relay validation and safe environment examples in `applications/temuriset-api/app/core/settings.py`, `applications/temuriset-api/app/capabilities/service/configuration.py`, `applications/temuriset-api/tests/unit/capabilities/test_configuration.py` and `applications/temuriset-api/.env.example` (FR-001, FR-005).

## Phase 3 · US1 (P1) · Email with one decision

**Independent test.** Use a synthetic account and the real sign-in, invitation and decision routes. Verify a single valid delivery after an ambiguous relay acknowledgement, and verify no optional delivery after opt-out or lost authorization.

- [X] T004 [P] [US1] Add code and invitation route tests for queue/commit separation, actual verification, replay, privacy and off/development behavior in `applications/temuriset-api/tests/integration/identity/test_identity.py` and `applications/temuriset-api/tests/integration/access/test_access.py` (FR-001, FR-002, SC-001).
- [X] T005 [P] [US1] Add relay contract, delivery failure, retry, opt-in, revoked access and deduplication tests in `applications/temuriset-api/tests/integration/discussion/test_discussion.py` and `applications/temuriset-api/tests/integration/platform/test_worker.py`. Cover unchanged privacy fulfilment in `applications/temuriset-api/tests/integration/moderation/test_privacy.py` (FR-002–FR-005, SC-001).
- [X] T006 [P] [US1] Add accessible enabled/off settings, save failure and version handling tests in `applications/temuriset-web/tests/account.test.tsx` (FR-003, SC-001).
- [X] T007 [US1] Implement the async relay and transactional secret delivery job in `applications/temuriset-api/app/identity/service/mailbox_service.py` and `applications/temuriset-api/app/identity/service/mail_jobs.py`. Wire existing caller paths through `applications/temuriset-api/app/identity/service/service.py` and `applications/temuriset-api/app/access/service/service.py`. Preserve isolated erasure behavior in `applications/temuriset-api/app/moderation/service/privacy.py` and record mapped failures in `docs/error-handling/catalog.md` (FR-001, FR-002, FR-004, FR-005).
- [X] T008 [US1] Add the account preference with a new Alembic revision after the current head and persist and return it through `applications/temuriset-api/app/identity/repository/sqlalchemy/models.py`, `applications/temuriset-api/app/identity/model/models.py`, `applications/temuriset-api/app/identity/model/schema.py` and `applications/temuriset-api/app/identity/service/service.py` (FR-003).
- [X] T009 [US1] Register independent delivery through `applications/temuriset-api/app/discussion/service/notifications.py` and `applications/temuriset-api/app/worker/__main__.py`. Resolve active eligibility through `applications/temuriset-api/app/access/service/service.py` and `applications/temuriset-api/app/identity/service/accounts.py` (FR-002–FR-004).
- [X] T010 [US1] Advertise validated local availability in `applications/temuriset-api/app/capabilities/router.py` and `applications/temuriset-api/app/capabilities/service/service.py`. Add the S18 control in `applications/temuriset-web/src/app/settings/page.tsx`, `applications/temuriset-web/src/views/SettingsView.tsx` and `applications/temuriset-web/src/features/AccountForms.tsx` (FR-003, FR-005).

## Phase 4 · Verification and activation

- [X] T011 Refresh `contracts/openapi.json` and `applications/temuriset-web/src/api/schema.generated.ts`. Run the migration, targeted checks and full gates in `Makefile`. Document safe settings in `applications/temuriset-api/README.md` and record local runtime evidence here (SC-001).
- [ ] T012 Record approved processing terms, sender-domain checks and sandbox delivery and deduplication evidence in `specs/042-email-adapter/spec.md` (FR-005, SC-002).
- [ ] T013 After T012, enable the approved provider configuration in `applications/temuriset-api/app/capabilities/service/configuration.py` and promote only the email registry entry in `applications/temuriset-web/src/features/registry.ts` after deployment verification (FR-005).


### Local verification evidence

- The API `make check` passed 964 tests with 96.17% line coverage on the implementation commit `d1f2b6b`. After the compatibility and locking changes in `7e254a2`, 46 targeted identity, discussion and worker tests passed. Together these runs exercised a real synthetic loopback relay, a lost acknowledgement, concurrent workers, event replay, replaced codes, revoked invitations, live consent and membership checks, and verification during an outstanding relay acknowledgement.
- PostgreSQL 16 applied revision `0020` from an empty database and through downgrade and reapply. The repository's PR-base harness verified old and new API reads and writes and both workers across `a7b60e0` (revision `0019`) and `7e254a2` (revision `0020`).
- The web `make check` passed 279 tests with 81.74% line coverage. The API contract and generated web types were refreshed, and a fresh OpenAPI export matched the tracked file.
- A Chromium smoke check against the Next.js production build at 320 px signed up through the API and worker using the synthetic relay. It verified keyboard opt-in, the saved S18 preference, zero axe violations in the account section, no horizontal overflow, and a hidden control after switching the API to disabled mail.

The provider terms, sender-domain checks and provider sandbox evidence remain open in T012. Provider activation and registry promotion remain gated in T013.

## Dependencies and parallel work

T001–T003 establish the baseline and validated configuration. T004–T006 can run in parallel. T007 and T008 precede T009–T010. The local MVP is T004–T010 plus verification in T011. T012–T013 are external activation work. T002 provides the encryption primitive reused by 043. Integrate shared settings, manifest, migration head and generated contracts in spec order.

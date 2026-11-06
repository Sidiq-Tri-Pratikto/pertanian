# Tasks: Deployment and release

**Input:** `specs/037-deploy-release/spec.md`, `plan.md`, the constitution, the PRD, and binding `docs/roadmap/architecture.md`.
**Base:** `main` with the M10 squash at `828f2a6`. Earlier checks record their M7-based integration or M10-based implementation at `eeab59e` in `DEPLOY/validation.md`. Complete 037 topology checks before the 038 Compose rehearsal. Paths below are relative to the pertanian repository root unless defined as an alias.

| Alias | Path |
|---|---|
| API | `applications/generic/temuriset/applications/temuriset-api` |
| WEB | `applications/generic/temuriset/applications/temuriset-web` |
| PROJECT | `applications/generic/temuriset` |
| DEPLOY | `deployment/temuriset` |

## Phase 1: Setup

- [X] T001 Confirm the M10 baseline, Docker contexts, image entrypoints, Alembic head, supported compositions, and local testing tools. Read `API/Dockerfile`, `API/entrypoint.sh`, `WEB/next.config.ts`, `PROJECT/Makefile`, and both existing TemuRiset CI workflows before editing.

## Phase 2: Foundation

- [X] T002 Record the deployment decisions and non-secret release version sources in `PROJECT/docs/roadmap/architecture.md`. Use Compose on a Linux host, private Postgres, MinIO or another compatible S3 provider, ClamAV, and operator-supplied HTTPS hostname and TLS. Keep the existing build-time same-origin rewrite. Use the same internal API address at web build and runtime and record environment-specific builds where addresses differ. Document that 037 prepares deployment artifacts without provisioning an external host or publishing images.
- [X] T003 Define required variables and safe examples in `API/.env.example`, `WEB/.env.example`, and `DEPLOY/.env.example`. Separate non-secret environment/release identity from secret-store inputs. Document storage endpoint, bucket, region, private credentials, scanner settings, public web origin, and explicit disabled mail. Use GitHub secrets or local operator inputs for actual credentials.

## Phase 3: User Story 1 - A reproducible release on a real environment (P1)

**Independent test:** Build the two application images and exercise the isolated Compose stack with synthetic data. Confirm one migration role completes before API and worker, the web proxy and health routes work, configured private S3 handles a document lifecycle, and the manifest matches the image digests and actual runtime versions. Real staging evidence remains a separate gate.

### Tests first

- [X] T004 [P] [US1] Extend `API/tests/unit/capabilities/` with startup, secret-sanitization, and manifest tests for local/S3 selection, missing S3 configuration, forbidden dev scanner/mailbox outside development, and disabled mail. Assert disabled delivery gives an actionable error and stores no development-mailbox message. Exercise auth code requests, invitations, and deletion-outcome handling so the disabled mode cannot produce a false delivery claim.
- [X] T005 [P] [US1] Add storage adapter tests in `API/tests/unit/documents/test_storage.py` and end-to-end S3 lifecycle tests in `API/tests/integration/documents/test_s3_storage.py`. Cover oversize cleanup, bounded reads/ranges, private keys, missing-object deletion, sanitized provider failures and unchanged gateway grants.
- [X] T006 [P] [US1] Add checks for the release manifest and Compose contract in `DEPLOY/tests/test_release_manifest.py` and `DEPLOY/tests/smoke.sh`. Cover immutable digest fields, denied public backing-store access, API health through the web origin, and migration idempotence.

### Runtime and release

- [X] T007 [US1] Add explicit storage and disabled-mail settings in `API/app/core/settings.py`. Fail closed outside development in `API/app/capabilities/service/configuration.py`. Wire a disabled mailbox through `API/app/identity/service/{mailbox_service,service}.py` and `API/app/access/service/service.py` plus `API/app/moderation/service/privacy.py`. Refuse unavailable email-dependent actions with a registered error before commitment, or report nondelivery distinctly when the business operation is already committed. Keep development-mailbox endpoints unmounted and distinguish outcome readiness from delivery. Keep development mail available only for development and tests and do not add SMTP.
- [X] T008 [US1] Implement private, bounded S3-compatible storage behind the existing port in `API/app/documents/service/storage_service.py` and `API/app/documents/service/s3_storage_service.py`. Add and lock any justified SDK dependency in `API/pyproject.toml` and `API/uv.lock`. Keep provider calls off the event loop with timeouts and normalize provider failures without leaking credentials, keys, or payloads.
- [X] T009 [US1] Inject the configured storage across `API/app/documents/{router.py,service/service.py,service/jobs.py}` and the 034 erasure path. Provide a bounded managed local temp-file interface for MIME sniffing, ClamAV and extraction from S3, and clean files on failure or success. Keep range authorization and no-store headers at the gateway. Erasure reports completion only after the selected storage removes the object.
- [X] T010 [US1] Report the actual configured storage adapter in `API/app/capabilities/{router.py,model/schema.py,service/service.py}` using an additive contract where possible. Preserve the existing adapter ID and keep secret/provider configuration out of the public manifest. Register new codes centrally in `API/app/core/errors/{codes,public}.py` and `PROJECT/docs/error-handling/catalog.md` as needed.
- [X] T011 [P] [US1] Adapt `API/Dockerfile` and `API/entrypoint.sh` for one non-root image with explicit API, worker, and one-shot migrate roles. Preserve the existing default development invocation or document any necessary compatibility changes. In the staging topology only the migrate role runs Alembic. Pin the interpreter base and uv inputs by version/digest and avoid floating package upgrades that undermine reproducibility. Health checks for worker and migrate must reflect those roles.
- [X] T012 [P] [US1] Add `WEB/Dockerfile` and `WEB/.dockerignore`, configure standalone output in `WEB/next.config.ts`, and package public/static assets. Keep the image non-root, pin the base by version/digest, install from the lockfile, and compile the explicit internal `API_URL` without baking secrets into image args or layers.
- [X] T013 [US1] Create `DEPLOY/compose.staging.yml` with API, worker, web, migrate, Postgres, a private S3-compatible store and ClamAV. Gate API/worker startup on the successful migration and required healthy dependencies. Provision a private bucket via a repeatable initialization step, keep backend dependencies on an internal network, and expose the app only behind an HTTPS edge with operator-supplied certificates. Pin service images, keep certificates/credentials out of build contexts, and provision app access with bucket-scoped credentials. Exercise the topology with an isolated synthetic configuration and local TLS where available.
- [X] T014 [P] [US1] Add a release manifest schema and deterministic validator/generator in `DEPLOY/release-manifest.schema.json` and `DEPLOY/release_manifest.py`. Record source commit/tag, configuration schema/version, tested composition and effective capability versions, adapter choices/versions, Alembic head, and image digests for API/worker/web. Include an environment inventory that distinguishes a published artifact from a separately recorded rollout.
- [X] T015 [US1] Add `.github/workflows/temuriset-release.yml` for PR build-only validation and trusted version-tag release. Run the existing application suites and a matrix of supported composition checks, build images, scan HIGH/CRITICAL findings with pinned Trivy and validate the manifest. Do not pass untrusted PR jobs registry write credentials or deploy secrets. Publish only in the trusted release job after gates pass, with commit-SHA references and immutable digests. Record per-composition results. Treat publishing and rollout as separate operations. Require approved staging evidence bound to the same digests and composition, plus the 038 recovery gate, before production promotion. This implementation task does not create a tag or push any registry image.
- [X] T016 [US1] Make `WEB/playwright.config.ts` and `WEB/e2e/fixtures.ts` capable of targeting an explicitly supplied staging HTTPS URL with external-server mode. Keep local fixture provisioning for local runs. For a real staging run require approved synthetic accounts/fixtures and authenticated access that exercises the deployed application. Fail closed if credentials or necessary journeys are missing, and reject an empty or skipped suite as passing evidence. Never expose a development mailbox, bypass real authorization, or let Playwright silently start a local app during a staging run.
- [X] T017 [US1] Add `DEPLOY/RUNBOOK.md` with operator responsibilities, release-window approval, hostname/TLS and network settings, secret-store injection, migration and startup order, inventory and rollout checkpoints, and code rollback vs forward repair/restore decision. Use role-based ownership until the real environment owner and approved window are supplied.

### Evidence and release gates

- [X] T018 [US1] Run local synthetic Compose smoke from `DEPLOY/tests/smoke.sh`, with bounded scans, twice-run migration, private storage, and checks against at least two independently configured supported compositions. Record version inventory and scope in `DEPLOY/validation.md`. Record missing external infrastructure or tooling rather than replacing the checks with simulated passes.
- [X] T019 [US1] Update the binding/deviation and mock-versus-server evidence in `PROJECT/docs/roadmap/architecture.md` and `DEPLOY/validation.md`. Identify the actual design-system version and source, TR mappings, deviations, prototype and runtime coverage, and fixture/reset scope. Record Editor Play and separately opened supported exports independently for UX-23, where available.
- [X] T020 [US1] In `WEB/e2e/staging.ts`, `WEB/playwright.config.ts` and `WEB/e2e/staging-reporter.ts`, resolve J01 from its named test in `WEB/e2e/matching.spec.ts`, J02 from `WEB/e2e/j02-company-raise.spec.ts`, and J03 from `WEB/e2e/j03-revision.spec.ts`. Validate the required journey identities rather than accepting any test in the same file. Run a focused discovery/guard check to prove missing J04/J05 (027–032), misconfiguration, filtering or unexpected skips still fail closed. Confirm the 042 staging-auth changes are reflected in `DEPLOY/RUNBOOK.md` when verified.
- [X] T021 [US1] Re-run the manifest contract and promotion evidence rejection checks from `DEPLOY/tests/test_release_manifest.py`, and build, scan and smoke the integrated images with `DEPLOY/tests/smoke.sh` and `.github/workflows/temuriset-release.yml` as the procedure. Record the actual image IDs, compositions, live capability/adapter inventory and observed Alembic head in `DEPLOY/validation.md`. Retain the M10 measurements as historical.
- [ ] T022 [US1] For actual staging acceptance, record approved staging URL, release digest, composition, runtime, fixture provenance, and the 003 browser suite plus J01–J05 in `DEPLOY/validation.md`. **Blocked** until approved staging and authentication from 042 are available. Record actual rollout per composition only after it is observed. Leave production promotion and SC-001 open.
- [ ] T023 [US1] Record a trusted published release's verified commit-bound image digests and manifest and an independently observed rollout for at least two supported compositions in `DEPLOY/validation.md`. Evidence remains gated on a protected release and separately approved rollout. Keep release availability and AC70 rollout evidence distinct.
- [ ] T024 [US1] Record Editor Play and independently opened supported exports with the tested version, J01–J05 differences, fixture/reset scope and limitations in `DEPLOY/validation.md`. Keep this evidence open where the actual surfaces are unavailable.

## Phase 4: Polish

- [X] T025 Regenerate `PROJECT/contracts/openapi.json` and `WEB/src/api/schema.generated.ts` with `make openapi` and `make generate-api`. Run lint, API/web checks, the available browser suite, and `PROJECT/docs/roadmap/check_traceability.py`; record actual results in `DEPLOY/validation.md`.
- [X] T026 Update `API/README.md`, `WEB/README.md`, and `PROJECT/specs/037-deploy-release/spec.md` with actual configuration and status. Keep staging acceptance open until T022 passes. T025 and T026 describe historical validation and documentation. Do not claim a release, rollout, image scan, or production readiness based on code alone.

- [X] T027 Verify regenerated contracts, API/web checks and the local 003 browser suite on the integrated worktree via `PROJECT/Makefile`, and run `PROJECT/docs/roadmap/check_traceability.py`. Update the deployment binding and integrated status in `PROJECT/docs/roadmap/architecture.md`, `DEPLOY/validation.md` and `PROJECT/specs/037-deploy-release/spec.md` from actual evidence.

## Dependencies & Execution Order

- T001–T003 precede test design and implementation. T004–T006 can be written in parallel and must establish failing checks for new behavior.
- T007–T010 establish safe runtime adapters and inventory. T011/T012 can proceed independently after T002/T003. T013 depends on T007–T012.
- T014 can run independently after configuration and manifest fields are settled. T015 follows T013/T014. T016/T017 define staging invocation and responsibilities before evidence collection.
- T020/T021 revalidate the inherited work on the integrated source. T022 waits on T020 and the actual staging prerequisites. T023 and T024 each require their own external evidence. T027 follows local checks and remains actionable while external tasks are gated.
- The local MVP is an integrated run of the existing release tooling and isolated stack. Production promotion still waits for T022 and 038 recovery and actual previous-release compatibility.

## Requirements Coverage

| Requirement | Tasks | Evidence |
|---|---|---|
| FR-001 and acceptance 1 | T006, T010–T015, T018, T021, T023, T025, T027 | Validated release workflow and immutable manifest, with publication recorded separately |
| FR-002, SC-001 and acceptance 3 | T015–T016, T018, T020–T022, T027 | Integrated local evidence and a separate staging gate |
| FR-003 and FR24 | T002–T003, T017, T026–T027 | Runbook and inventory with actual deployment dependencies |
| AC70 and acceptance 2 | T014–T015, T017–T018, T021, T023 | Composition-specific checks and actual rollout records |
| UX-23 and UX-24, acceptance 4 | T016, T019–T020, T022, T024, T027 | Runtime evidence, prototype/editor/export evidence and design binding |
| Adapter flip and deployment edge cases | T003–T005, T007–T013 | Actual backend in manifest; TLS, secret-store inputs and same-origin proxy |

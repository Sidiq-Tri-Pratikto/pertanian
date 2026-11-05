# TemuRiset deployment validation

## Local evidence on the M10 base

The 037 implementation was checked on 6 November 2026 WIB from a local worktree based on `eeab59e`. These checks use synthetic data and local builds. The Compose project uses unique names, disposable volumes, private bucket credentials and a loopback TLS certificate. The smoke script removes only its own synthetic project and volumes when it exits. The browser suite uses a separate disposable PostgreSQL database. Local image identifiers and reports are evidence for these checks. The release workflow creates the authoritative commit-bound OCI digest inventory from its own validated archives.

| Check | Result and scope |
|---|---|
| API lint and formatting | Ruff passed. |
| API unit and integration suite | 542 passed with 95.63% coverage. Disabled mail was checked for sign-in codes, invitations and completed erasure. |
| Web lint, types and unit suite | ESLint and TypeScript passed. Vitest passed 203 tests with 89.06% line coverage. |
| Contract and traceability | OpenAPI and TypeScript regenerated. Traceability mapped 143 requirements across 45 specs. |
| Release manifest and workflow | Three manifest contract tests passed. Release workflow YAML and Bash parsed locally. |
| Local 003 browser | 304 passed and 248 intentional viewport skips at 320, 360, 768 and 1280 px, against a production Next build and a local development API. An initial run hit the default sign-up rate limit. The recorded run used a fresh disposable database and the existing E2E limit of 1,000 requests per address per hour. |
| Staging invocation guard | Rejected an HTTP origin, a filtered invocation, and an HTTPS invocation with missing J01–J05 files before starting tests. |
| Image builds and security | Both final ARM64 images built and passed pinned Trivy 0.69.3 with zero HIGH or CRITICAL findings. Next standalone Sharp loaded libvips 8.18.7 from the final musl build. Earlier Debian-based candidates were retired after scanner findings. |

## Synthetic HTTPS topology

The final ARM64 image identifiers were `sha256:ae00ebeb883fd7e665ccb26eb7ce94dcb99c2ea0a2037a16ab31186ac4d54899` for API and worker, and `sha256:7dee63c6fb31a22cff784cd0682b0c48235f4fb9accfe05e25c41befa2caccc8` for web. The disposable stack passed all three composition runs with these images. Both application images use Alpine `3.24.3`.

| Composition | Runtime version | Local smoke scope |
|---|---|---|
| `generic-base` | 1 | Public health and app through HTTPS, private S3, synthetic development authentication, PDF signature check, ClamAV scan, text extraction, denied unshared read, permitted full and range read, no-store, and grant revocation. Real S3 adapter checks include oversized upload cleanup, chunk bounds, temporary file cleanup, idempotent deletion and missing-object behavior. |
| `generic-with-review` | 1 | Independently selected configuration, health and manifest, disabled sign-in mail and unmounted development mailbox. |
| `project-support-only` | 1 | Independently selected configuration, health and manifest, disabled sign-in mail, unmounted development mailbox, and rejected unsigned S3 access from the private network. |

Across all three compositions the capability schema is `1`, source release is `0.1.0`, and the adapters report `s3` and `clamav`. Runtime metadata records composition-specific capability and policy lists, running PostgreSQL, S3, ClamAV and edge image references, and the observed Alembic head `0009`. The migration role ran twice for each composition. The final smoke also replaced the web container and rechecked HTTPS through the existing edge. The local certificate is accepted explicitly by the synthetic client. The actual staging origin requires its own trusted certificate and QA sign-off.

## Design-system and prototype evidence

The application binds TemuRiset Design System `1.0.0-draft`. The source CSS is copied byte-for-byte into the web app. `src/components/tr/` ports the TR names, semantics and class mappings. The [architecture record](../../applications/generic/temuriset/docs/roadmap/architecture.md) describes web deviations D1–D7. The [canvas binding](../../docs/generic/temuriset/app-prototype/binding.json) describes a separate component copy and its fingerprints and deviations. This draft remains subject to design owner approval.

| Surface | Evidence |
|---|---|
| Prototype and reset | The existing [design handoff](../../docs/generic/temuriset/app-prototype/DESIGN_HANDOFF.md) records an independently opened local source harness at canvas version 15 and resettable fictional fixtures. The harness simulates identity, grants, bytes, workflows and timing in browser state. |
| Editor Play | The handoff identifies a published private canvas. 037 has no independently verified Editor Play run. |
| Supported share and export formats | The source harness was opened independently according to the handoff. Hosted Share/Export formats remain blocked there. No separate hosted export run is recorded here. |
| Application runtime | Local API/browser tests use persisted synthetic accounts and records. Compose separately exercises real authorization, private storage and worker jobs. Those checks establish their individual runtime behaviors. |

## Actual staging and release gates

Actual staging acceptance T020 and SC-001 remain open. The release record still needs the approved HTTPS origin, operator and window, exact deployed image digests, composition and live version inventory, approved fixture provenance, a successful 003 run, and J01–J05. The journeys and real staging authentication from 042 remain prerequisites. Local mail and canvas simulations cannot establish actual staging acceptance.

There is no trusted published previous-release tag for the production compatibility gate. The isolated 038 restore and baseline checks are recorded separately in the [recovery drill](backup/drill.md). Production promotion requires passed staging, restore and compatibility evidence tied to the published image digests and composition. This work has no tag, registry publication or environment rollout record.

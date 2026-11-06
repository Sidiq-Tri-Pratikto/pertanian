# Feature Specification: Deployment and release

**Feature Branch**: `037-deploy-release`
**Created**: 2026-11-05
**Status**: The historical Alembic `0015` build passed local smoke on all three compositions and both ARM64 image scans. The `0019` branch passes the local PR-base compatibility check. Actual staging, protected publication and rollout acceptance remain open.
**Milestone**: M11 Portability and operations
**Depends on**: 003, 005
**Size**: L
**Covers**: FR24, AC70, UX-23, UX-24
**Flips**: manifest adapter `object-storage` records `s3` when configured

## User Scenarios & Testing

### User Story 1 - A reproducible release on a real environment (Priority: P1)

Container images for API, worker and web; a migration job that runs before the API starts; an HTTPS deployment with S3-compatible storage, ClamAV and SMTP-less mailbox off; and a version inventory per environment.

**Acceptance Scenarios**:

1. **Given** a tagged release, **When** CI builds it, **Then** immutable images are pushed with the commit SHA, and a release manifest records code, configuration, capability, adapter and schema versions.
2. **Given** a shared fix released to two compositions, **When** deployed, **Then** each composition's suite and version inventory are required, and "released" is never treated as "rolled out" (AC70).
3. **Given** the deployed web app, **When** the 003 suite and J01–J05 run against its URL, **Then** results are recorded separately from local runs. Editor Play and independently opened supported prototype exports have separate evidence and limitations (UX-23).
4. **Given** the deployment, **When** the binding record is read, **Then** the design-system version, deviations and mock-versus-server ledger are current (UX-24).

### Edge Cases

- `API_URL` rewrites are fixed at build: the deployed web image is built per environment or uses a runtime proxy route; this spec picks one and records it.
- Secrets come from the environment's secret store; composition config carries references only.

## Requirements

### Functional Requirements

- **FR-001**: The release workflow MUST build, test, scan and tag images and write the release manifest.
- **FR-002**: Staging MUST run the browser suite and the five journeys before production promotion.
- **FR-003**: The runbook MUST name owner, release window, rollback or forward-repair steps.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A staging deployment passes the 003 suite and J01–J05 against its URL.

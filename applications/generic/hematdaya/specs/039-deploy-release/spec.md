# Feature Specification: Deployment and release

**Feature Branch**: `039-deploy-release`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M9 Saved service
**Depends on**: 036
**Size**: M
**Covers**: FR-22, AT-54
**Flips**: none

## User Scenarios & Testing

### User Story 1 - One command to a pilot server (Priority: P1)

**Why this priority**: Phones need a reachable HTTPS API; release builds block cleartext.

**Independent Test**: Deploy to a clean host.

**Acceptance Scenarios**:

1. **Given** a clean host with Docker, **When** the deploy runs, **Then** API and Postgres start behind HTTPS, migrations run first, and health passes.
2. **Given** a failed migration, **When** deploying, **Then** the old version keeps serving.

### User Story 2 - Know what is running (Priority: P1)

**Why this priority**: FR-22: release, composition, migrations per deployment.

**Independent Test**: Read the record.

**Acceptance Scenarios**:

1. **Given** a deployment, **When** inspected, **Then** source release, composition, policies and migration head are recorded and match the manifest.
2. **Given** a supported isolated client deployment, **When** made, **Then** it uses the same source with separate data, secrets and access, and never a source fork.

### User Story 3 - Failures reach someone (Priority: P1)

**Why this priority**: The EH-08 deviation must close before the first production release.

**Independent Test**: Trigger a failure and find it by reference ID.

**Acceptance Scenarios**:

1. **Given** a reference ID, **When** an engineer searches, **Then** it resolves to one sanitized record.

### Edge Cases

- A site is not a tenant: no tenant claim follows from this work.
- Rollback steps are written and rehearsed.

## Requirements

### Functional Requirements

- **FR-001**: Deployment MUST be repeatable from the repository, with no secrets in it.
- **FR-002**: Each release MUST be tagged and reproducible.
- **FR-003**: `docs/error-handling/deviation.md` MUST lose its EH-08 row.

### Key Entities

- **DeploymentRecord**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A second person can deploy from the runbook alone.
- **SC-002**: A phone release build reaches the API over HTTPS.

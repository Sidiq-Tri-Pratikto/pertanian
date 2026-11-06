# Feature Specification: Deployment and release

**Feature Branch**: `039-deploy-release`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M9 Saved service
**Depends on**: 011, 036
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

1. **Given** a deployment, **When** inspected, **Then** the release, composition and policies match the manifest, and the recorded migration head matches the database.
2. **Given** a supported isolated client deployment, **When** made, **Then** it uses the same source with separate data, secrets and access, and never a source fork.
3. **Given** both supported compositions, **When** deployed from one source release, **Then** each produces the exact household and industrial fixture results, and the release inventory identifies the composition, migration and rollback for each deployment.

### User Story 3 - Failures reach someone (Priority: P1)

**Why this priority**: The EH-08 deviation must close before the first production release.

**Independent Test**: Trigger a failure and find it by reference ID.

**Acceptance Scenarios**:

1. **Given** a reference ID, **When** an engineer searches, **Then** it resolves to one sanitized record.

### Edge Cases

- A site is not a tenant: no tenant claim follows from this work.
- Rollback steps are written and rehearsed.
- The HTTPS environment can be rehearsed with synthetic data. Opening a saved-data pilot requires 038 and the restore rehearsal in 040.

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
- **SC-002**: An actual phone reaches the rehearsal API over HTTPS. 042 supplies the installed app's release-build evidence.
- **SC-003**: The AT-54 evidence records both composition oracles, affected contract checks and separation of storage, secrets and access.

# Feature Specification: Capability guard and configuration validation

**Feature Branch**: `004-capability-guard`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M0 Foundations
**Depends on**: 001
**Size**: S
**Covers**: FR23, AC69
**Flips**: none

## User Scenarios & Testing

### User Story 1 - A disabled capability is refused everywhere (Priority: P1)

When a composition excludes `company_funding` or `organization_review`, any route that needs it refuses with one documented failure, whatever client calls it.

**Why this priority**: FR23 requires visibility and mutation availability to agree on server and client, and 014 and 033 need the guard.

**Independent Test**: A test route guarded by a disabled capability returns `CAPABILITY_UNAVAILABLE`.

**Acceptance Scenarios**:

1. **Given** `project-support-only`, **When** a route requiring `company_funding` is called, **Then** it returns HTTP 403 with code `CAPABILITY_UNAVAILABLE`, an Indonesian two-clause message, and `retryable: false`, and changes nothing.
2. **Given** `generic-base`, **When** the same route is called, **Then** the guard passes.

### User Story 2 - Unsafe configuration never serves traffic (Priority: P1)

**Acceptance Scenarios**:

1. **Given** `COMPOSITION_OVERRIDES` that enables `reranking` without `dense_retrieval`, **When** the service starts, **Then** startup fails naming the dependency.
2. **Given** a composition setting whose value looks like a secret (a key, token or password pattern), **When** the service starts, **Then** startup fails and the value never appears in logs (AC69).
3. **Given** production with `development-accept` as the file scanner, **When** the service starts, **Then** startup fails (enforced from 010; the check lives here).

### Edge Cases

- The manifest still lists only selected capabilities; a disabled one is absent, not `planned`.
- The guard runs before validation of the request body, so a disabled capability never reports field errors.

## Requirements

### Functional Requirements

- **FR-001**: One FastAPI dependency, `require_capability(id)`, MUST guard every route of an optional capability.
- **FR-002**: `CAPABILITY_UNAVAILABLE` MUST be registered in `codes.py`, `public.py` and the catalog.
- **FR-003**: Configuration validation MUST reject unknown capabilities, missing dependencies, secrets in composition config and unsafe adapters for the environment, before the app is created.
- **FR-004**: The web client MUST read the manifest once per server render and hide entry points for absent capabilities, while the API still refuses them.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Each refusal path has a test asserting code, message, recovery, request ID, record and no state change.

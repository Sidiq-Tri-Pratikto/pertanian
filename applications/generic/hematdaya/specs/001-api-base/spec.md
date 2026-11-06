# Feature Specification: API base

**Feature Branch**: `001-api-base`
**Created**: 2026-10-30
**Status**: Built, awaiting review
**Milestone**: M0 Foundations
**Depends on**: none (bootstrap commit)
**Size**: M
**Covers**: FR-20, FR-21, AT-49
**Flips**: none; every manifest entry starts as `planned`

## User Scenarios & Testing

### User Story 1 - A client learns what this deployment offers (Priority: P1)

The mobile app asks the service what is available and gets an honest answer, so it can explain an unavailable feature instead of guessing.

**Why this priority**: Every later PR flips an entry here. Without it, a client has no contract with the deployment.

**Independent Test**: `curl /api/v1/capabilities` on a running service returns the manifest.

**Acceptance Scenarios**:

1. **Given** the base release, **When** a client requests `/api/v1/capabilities`, **Then** it receives schema version, source release, composition, capabilities, adapters and policies, and every capability and adapter reports `planned`.
2. **Given** `COMPOSITION=core-only`, **When** a client requests the manifest, **Then** only the `core` capability is listed.
3. **Given** `COMPOSITION=custom-fork`, **When** the service starts, **Then** startup fails with the unsupported composition named.

### User Story 2 - Operators can tell the process from its dependencies (Priority: P1)

**Why this priority**: PRD §16 defines separate liveness and readiness, and neither says anything about a meter or a load.

**Independent Test**: Stop Postgres; liveness stays ok and readiness fails with the envelope.

**Acceptance Scenarios**:

1. **Given** a running process, **When** `/health/live` is called with the database down, **Then** it returns 200.
2. **Given** the database is down, **When** `/health/ready` is called, **Then** it returns the retryable `DATABASE_UNAVAILABLE` envelope with `Retry-After`.

### User Story 3 - The product cannot actuate anything (Priority: P1)

**Why this priority**: FR-20 is a non-negotiable product boundary and must hold from the first route.

**Independent Test**: Compare the application routes with the expected read-only method/path pairs.

**Acceptance Scenarios**:

1. **Given** the base application, **When** its route table is inspected, **Then** its product routes are the three documented GET endpoints and no path or operation offers control, relay, command or on/off behaviour.

### User Story 4 - Failures speak Indonesian (Priority: P2)

**Why this priority**: The product interface is Indonesian, and the client shows the service's message.

**Independent Test**: Request a missing route and read the envelope.

**Acceptance Scenarios**:

1. **Given** any public failure, **When** it is returned, **Then** `message` is a two-clause Indonesian sentence and `code` is the stable English code.
2. **Given** a validation failure, **When** it is returned, **Then** each `details[].msg` is Indonesian, and submitted values are never echoed.

### Edge Cases

- A capability status can only move forward in a PR that ships the feature; nothing may report `available` early.
- An unknown validation type gets a safe default field message.
- Browser origins not listed in `CORS_ALLOWED_ORIGINS` get no CORS header; native clients need none.

## Requirements

### Functional Requirements

- **FR-001**: The service MUST expose `GET /api/v1/capabilities` with the PRD 15.4 fields and no secrets.
- **FR-002**: The service MUST validate its composition at startup and refuse unknown compositions or a missing core.
- **FR-003**: The service MUST expose `/health/live` and `/health/ready`.
- **FR-004**: All public messages MUST be Indonesian; codes stay English and stable.
- **FR-005**: The generated contract MUST be committed and checked for drift.
- **FR-006**: The route table MUST contain no actuation path, and a test MUST prove it.

### Key Entities

- **Capability manifest**: schema version, source release, composition, capabilities with status, adapters with status, policies with version. It explains; it never grants access.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `make check` passes with at least 80% coverage (33 tests, 96% at build time).
- **SC-002**: `make openapi` produces no diff against `contracts/openapi.json`.
- **SC-003**: `docker build` succeeds and its health check calls `/health/live`.

# Feature Specification: API base

**Feature Branch**: `001-api-base`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M0 Foundations
**Depends on**: none (bootstrap from product-starter-wdd 8f9f07e)
**Size**: M
**Covers**: FR23
**Flips**: none; every capability and adapter starts as `planned`

## User Scenarios & Testing

### User Story 1 - A client learns what this deployment offers (Priority: P1)

The web client asks the service what is available and gets an honest answer, so it can explain an unavailable feature instead of guessing.

**Why this priority**: Every later PR flips an entry here, and FR23 needs a validated composition before any traffic.

**Independent Test**: `curl /api/v1/capabilities` on a running service returns the manifest.

**Acceptance Scenarios**:

1. **Given** the base release, **When** a client requests `/api/v1/capabilities`, **Then** it receives schema version, source release, composition, default locale `id`, supported currencies `IDR` and `USD`, capabilities, adapters and six versioned policies, and every capability and adapter reports `planned`.
2. **Given** `COMPOSITION=project-support-only`, **When** the manifest is read, **Then** only `core` is listed and `company_funding` is absent.
3. **Given** `COMPOSITION=generic-with-review`, **When** the manifest is read, **Then** `organization_review` is listed.
4. **Given** `COMPOSITION=client-fork`, **When** the service starts, **Then** startup fails and names the composition.

### User Story 2 - Operators can tell the process from its dependencies (Priority: P1)

**Why this priority**: Liveness must not depend on Postgres, and readiness must.

**Independent Test**: Stop Postgres; liveness stays ok and readiness fails with the envelope.

**Acceptance Scenarios**:

1. **Given** the database is down, **When** `/health/live` is called, **Then** it returns 200.
2. **Given** the database is down, **When** `/health/ready` is called, **Then** it returns the retryable `DATABASE_UNAVAILABLE` envelope with `Retry-After`.

### User Story 3 - The product never moves money (Priority: P1)

**Why this priority**: PRD section 2 excludes payments, custody, valuation, share issuance and crowdfunding. The boundary must hold from the first route.

**Independent Test**: A test walks the OpenAPI route table.

**Acceptance Scenarios**:

1. **Given** the route table, **When** it is inspected, **Then** no path or operation mentions payment, payout, escrow, wallet, checkout, money transfer, valuation, share issuance, securities, crowdfunding or cap table.

### User Story 4 - Failures speak Indonesian (Priority: P2)

**Acceptance Scenarios**:

1. **Given** any public failure, **When** it is returned, **Then** `message` is a two-clause Indonesian sentence and `code` is the stable English code.
2. **Given** a validation failure, **When** it is returned, **Then** each `details[].msg` is Indonesian and submitted values are never echoed.

### Edge Cases

- A capability status only moves forward in the PR that ships it.
- Browser origins need no CORS entry: the web client calls the API through its own origin.

## Requirements

### Functional Requirements

- **FR-001**: The service MUST expose `GET /api/v1/capabilities` with no secrets.
- **FR-002**: The service MUST validate its composition at startup and refuse unknown compositions or a missing core.
- **FR-003**: The service MUST expose `/health/live` and `/health/ready`.
- **FR-004**: All public messages MUST be Indonesian; codes stay English and stable.
- **FR-005**: The generated contract MUST be committed and drift-checked in CI.
- **FR-006**: The route table MUST contain no money-movement path, and a test MUST prove it.

### Key Entities

- **Capability manifest**: schema version, source release, composition, locale, currencies, capabilities, adapters and policies. It explains; it never grants access.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `make check` passes with at least 80% coverage (36 tests, 96% at build time, including the readiness integration test against Postgres).
- **SC-002**: `make openapi` produces no diff against `contracts/openapi.json`.
- **SC-003**: `docker build` succeeds and its health check calls `/health/live`.

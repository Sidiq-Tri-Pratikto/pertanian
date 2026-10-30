# Feature Specification: Demo sessions

**Feature Branch**: `008-demo-sessions`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M1 Energy core
**Depends on**: 007
**Size**: M
**Covers**: FR-01, FR-17, AT-43
**Flips**: manifest adapter `demo` → `simulated`

## User Scenarios & Testing

### User Story 1 - Start a demo with no account (Priority: P1)

A client requests a scenario and gets an isolated seeded site plus an opaque token.

**Why this priority**: The hardware-free demo is the product's first impression and needs no credentials (FR-01).

**Independent Test**: `POST /demo/sessions`, then read the site with the token.

**Acceptance Scenarios**:

1. **Given** no credentials, **When** a client creates a session for `h-base`, **Then** it receives a token and a site whose 2,688 rows are seeded.
2. **Given** two sessions, **When** each reads, **Then** neither sees the other's site or changes.
3. **Given** scenario `empty`, **When** a session is created, **Then** the site has no readings, for the "Mulai" path before accounts exist.

### User Story 2 - Reset affects only the demo (Priority: P1)

**Why this priority**: AT-43 requires each action to stay within its declared scope.

**Independent Test**: Change a demo site, reset, compare.

**Acceptance Scenarios**:

1. **Given** a session with changes, **When** it resets, **Then** its site returns to the scenario's start and the token stays valid.
2. **Given** another session, **When** the first resets, **Then** the other is unchanged.

### User Story 3 - The public endpoint cannot be abused cheaply (Priority: P1)

**Why this priority**: Each anonymous call writes thousands of rows.

**Independent Test**: Exceed the cap in a test.

**Acceptance Scenarios**:

1. **Given** the active session cap is reached, **When** a new session is requested, **Then** expired sessions are purged first, and if none are free the response is the retryable `RATE_LIMITED` envelope.
2. **Given** an expired token, **When** it is used, **Then** the response is a typed `SESSION_EXPIRED` error the client can act on.

### Edge Cases

- A token is shown once and stored only as a hash.
- A malformed bearer token returns `UNAUTHORIZED`, with no detail on why.
- Demo data is labelled through `sites.kind = 'demo'` and origin `simulated`.

## Requirements

### Functional Requirements

- **FR-001**: The API MUST list scenarios with Indonesian names and create a session for any of them.
- **FR-002**: Sessions MUST expire, and creation MUST purge expired sessions.
- **FR-003**: Tokens MUST be high-entropy, opaque and stored hashed.
- **FR-004**: Reset MUST reseed only that session's site.
- **FR-005**: Seeding MUST be a set-based insert, not one statement per row.
- **FR-006**: The principal resolver from 004 MUST accept demo tokens.

### Key Entities

- **DemoSession**: principal, site, scenario, token hash, expiry.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Creating an `h-base` session takes under 2 seconds on the dev machine, measured and recorded.
- **SC-002**: AT-41 covers demo routes with two real sessions.

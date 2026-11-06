# Feature Specification: Demo sessions

**Feature Branch**: `008-demo-sessions`
**Created**: 2026-10-30
**Status**: Implemented on `f/m1-energy-core`; Postgres integration tests pass. SC-001: an `h-base` session took 0.69 s on the dev machine (2026-11-06)
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
4. **Given** a create committed but its response was lost, **When** the client repeats the same operation ID, replay proof and payload within the replay window, **Then** it receives the original credential and site without seeding twice.
5. **Given** a known operation, **When** a request lacks the matching proof, changes the payload or arrives outside its replay window, **Then** it does not obtain the existing credential or create a second session for that operation.

### User Story 2 - Reset affects only the demo (Priority: P1)

**Why this priority**: AT-43 requires each action to stay within its declared scope.

**Independent Test**: Change a demo site, reset, compare.

**Acceptance Scenarios**:

1. **Given** a session with changes, **When** it resets, **Then** its site returns to the scenario's start and the token stays valid.
2. **Given** another session, **When** the first resets, **Then** the other is unchanged.
3. **Given** reset fails during seeding, **When** the transaction rolls back, **Then** the prior site, token and data remain usable.

### User Story 3 - The public endpoint cannot be abused cheaply (Priority: P1)

**Why this priority**: Each anonymous call writes thousands of rows.

**Independent Test**: Exceed the cap in a test.

**Acceptance Scenarios**:

1. **Given** the active session cap or anonymous creation budget is reached, **When** a new operation is requested, **Then** expired sessions are excluded after cleanup and requests exceeding the remaining allowance return `RATE_LIMITED` with bounded recovery.
2. **Given** an expired token with a stored digest, **When** it is used, **Then** the response is `SESSION_EXPIRED`. After the digest is purged it receives generic `UNAUTHORIZED`.
3. **Given** one slot remains and distinct new requests arrive together, **When** admission runs, **Then** at most one request seeds a session.

### Edge Cases

- A token is returned on creation and bounded, proof-verified replay. Store only its digest, never the credential or replay proof in plaintext.
- A malformed bearer token returns `UNAUTHORIZED`, with no detail on why.
- The site is always labelled as demo. Seeded readings use origin `simulated`. Use a CSV-derived origin only when the scenario exercises CSV ingestion.

## Requirements

### Functional Requirements

- **FR-001**: The API MUST list scenarios with Indonesian names and create a session for any of them.
- **FR-002**: Sessions MUST expire, and creation MUST purge expired sessions.
- **FR-003**: Tokens MUST be high-entropy, opaque and stored hashed.
- **FR-004**: Reset MUST reseed only that session's site.
- **FR-005**: Seeding MUST be a set-based insert, not one statement per row.
- **FR-006**: The principal resolver from 004 MUST accept demo tokens.
- **FR-007**: A create MUST require a high-entropy operation ID and separate secret replay proof. Dedupe and seed atomically, bind replays to the same payload and bound the credential replay window.
- **FR-008**: The active cap and anonymous creation budget MUST be shared and atomic. Purge MUST remove the expired site's demo-owned records and principal.

### Key Entities

- **DemoSession**: principal, site, scenario, token hash, expiry.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Creating an `h-base` session takes under 2 seconds on the dev machine, measured and recorded.
- **SC-002**: AT-41 covers demo routes with two real sessions.

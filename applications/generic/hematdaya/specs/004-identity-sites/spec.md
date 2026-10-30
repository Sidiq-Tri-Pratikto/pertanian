# Feature Specification: Identity and sites

**Feature Branch**: `004-identity-sites`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M1 Energy core
**Depends on**: 001
**Size**: M
**Covers**: FR-02, AT-41
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Every resource belongs to someone (Priority: P1)

Every site has an owner principal from the first migration, and a request can only reach sites its principal owns.

**Why this priority**: Ownership added later means rewriting every query and every test. PRD §17 requires owner checks on every read and mutation.

**Independent Test**: Two principals in a test; each can read only its own site.

**Acceptance Scenarios**:

1. **Given** principal A owns a site, **When** A requests it, **Then** the site is returned.
2. **Given** principal B, **When** B requests A's site, **Then** the response is `NOT_FOUND`, so the site's existence does not leak.
3. **Given** no credentials on a protected route, **When** it is called, **Then** the response is `UNAUTHORIZED` with `WWW-Authenticate`.

### User Story 2 - A site has a visible timezone and neutral context (Priority: P1)

**Why this priority**: Every period boundary depends on the site's timezone; context must stay neutral (PRD §3).

**Independent Test**: Create a site through the service; defaults are Asia/Jakarta, IDR, `unspecified`.

**Acceptance Scenarios**:

1. **Given** a new site, **When** it is created with no context, **Then** context is `unspecified`, timezone `Asia/Jakarta`, currency `IDR`.
2. **Given** an invalid timezone, **When** it is saved, **Then** the request fails with a field message and nothing changes.

### User Story 3 - One clock per site (Priority: P1)

Demo sites run on a virtual clock and standard sites on the wall clock, behind one function.

**Why this priority**: Fixtures, staleness and snooze must be reproducible.

**Independent Test**: `site_clock` returns `virtual_now` for a demo site and the wall clock otherwise.

**Acceptance Scenarios**:

1. **Given** a demo site with `virtual_now` 2026-10-26 00.00, **When** product code asks for now, **Then** it gets that instant.
2. **Given** a standard site, **When** `virtual_now` is written, **Then** the database refuses it.

### Edge Cases

- A nested resource from another owner in an otherwise valid request is refused.
- A site is a domain location, never a tenant (PRD §15.3).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST store principals with a kind of `demo` or `user`.
- **FR-002**: Every site MUST reference an owner principal.
- **FR-003**: Routes MUST resolve the acting principal through one dependency, and it MUST fail closed when no resolver accepts the request.
- **FR-004**: Foreign resources MUST return `NOT_FOUND`, never `FORBIDDEN`.
- **FR-005**: Timezone MUST be a valid IANA name.
- **FR-006**: `site_clock` MUST be the only source of product time.

### Key Entities

- **Principal**: `id`, `kind`.
- **Site**: owner, kind, name, context, timezone, currency, optional virtual now.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An owner-isolation test exists and later data PRs extend it.
- **SC-002**: The CHECK constraint on `virtual_now` is proven by an integration test.

# Feature Specification: Assets, bindings and audit

**Feature Branch**: `005-assets-bindings-audit`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M1 Energy core
**Depends on**: 004
**Size**: M
**Covers**: FR-03, FR-19, AT-11
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Model what is measured (Priority: P1)

A site holds arbitrary assets, each with a scope kind, and sources bind to assets with effective times.

**Why this priority**: PRD §5 makes this the shared domain model. A name is not an ID, and a category is not a capability.

**Independent Test**: Create an asset and bind a source through the service; rename keeps its ID.

**Acceptance Scenarios**:

1. **Given** an asset, **When** it is renamed, **Then** its ID and bindings are unchanged.
2. **Given** two assets with the same name, **When** both exist, **Then** both are valid and distinguishable by ID.
3. **Given** an asset of category "Pendingin", **When** it is created, **Then** its expected use stays `unknown` unless the user chose otherwise.

### User Story 2 - Change sources without losing history (Priority: P1)

**Why this priority**: FR-03 requires effective-dated replacement and retained history.

**Independent Test**: End a binding; readings stay and the asset's history stops at that time.

**Acceptance Scenarios**:

1. **Given** an active binding, **When** it is removed, **Then** it gets an end time and is not deleted.
2. **Given** an authoritative binding, **When** a second authoritative binding overlaps it, **Then** the database refuses it.
3. **Given** two non-authoritative bindings for one asset, **When** both exist, **Then** they are stored as an unresolved conflict.

### User Story 3 - Every change leaves a record (Priority: P2)

**Why this priority**: FR-19 requires who, when and affected intervals, without secrets.

**Independent Test**: Edit an asset and read the audit row.

**Acceptance Scenarios**:

1. **Given** a binding, tariff, scope or metric change, **When** it is saved, **Then** one audit event records actor, action, subject and affected range in the same transaction.
2. **Given** a failed save, **When** it rolls back, **Then** no audit event remains.

### Edge Cases

- A declared parent must be in the same site; a cycle or self-reference is refused.
- Unknown physical overlap is its own state, never treated as disjoint.
- Archiving is reversible and keeps readings.
- A continuous expected asset is never treated as waste by any later rule (AT-11).

## Requirements

### Functional Requirements

- **FR-001**: Assets MUST carry a stable ID, name up to 60 characters, optional category and location, scope kind, and expected use.
- **FR-002**: Scope kind MUST be one of `device`, `group`, `circuit`, `site_total`.
- **FR-003**: Expected use MUST default to `unknown` and MUST never be derived from category.
- **FR-004**: Bindings MUST be effective-dated, and removal MUST set an end time.
- **FR-005**: At most one authoritative source per asset per instant MUST be enforced by the database.
- **FR-006**: Relations MUST be within one site and acyclic.
- **FR-007**: Audit events MUST be append-only, contain no secrets, and commit with their change.

### Key Entities

- **Asset**, **Source**, **Binding**, **AssetRelation**, **AuditEvent**. See `docs/roadmap/architecture.md`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Overlapping authoritative bindings fail at the database, proven by an integration test.
- **SC-002**: Every mutation route in this PR writes exactly one audit event.

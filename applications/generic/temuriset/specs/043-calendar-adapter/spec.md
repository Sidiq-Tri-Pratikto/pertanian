# Feature Specification: External calendar adapter (gated)

**Feature Branch**: `043-calendar-adapter`
**Created**: 2026-11-05
**Status**: Seeded, not started; gated
**Milestone**: M12 Gated adapters
**Depends on**: 028
**Size**: L
**Covers**: FR17, AC68
**Flips**: manifest adapter `calendar` → `available`; web registry `kalender` → `available`

**Entry condition**: a contracted calendar provider and consent wording for reading free and busy times.

## User Scenarios & Testing

### User Story 1 - Free and busy from a connected calendar, honestly labelled (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a connected calendar, **When** slots are proposed, **Then** busy times are marked from the provider, and internal bookings still decide conflicts on acceptance.
2. **Given** the adapter is off or fails, **When** scheduling, **Then** internal slots and ICS keep working and external availability reads "belum diketahui" (AC68).

## Requirements

### Functional Requirements

- **FR-001**: OAuth tokens MUST be stored encrypted and revocable; only free and busy are read.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Adapter contract tests and an adapter-off journey pass.

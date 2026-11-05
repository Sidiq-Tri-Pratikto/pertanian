# Feature Specification: Public profiles and relationship transparency

**Feature Branch**: `031-public-profiles-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M9 Relationships
**Depends on**: 030
**Size**: M
**Covers**: FR19, AC55, AC56, AC57
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Only what both allowed appears (Priority: P1)

A party's public profile shows its deliberately published biography, published inventions and the effective public fields of each confirmed relationship.

**Acceptance Scenarios**:

1. **Given** version 2 confirmed with amount permitted by only one party, **When** anyone reads the profile, **Then** amount is absent; **When** a party later restricts date, **Then** date disappears on the next read, and expansion needs a new confirmation round (AC55).
2. **Given** one equity relationship supporting two inventions, **When** read, **Then** it appears once with two invention links and no doubled share (AC56).
3. **Given** a contested claim under review, **When** read publicly, **Then** it is hidden, and the parties still see their private history (AC57).

### Edge Cases

- Creator, manager, claimed rights holder, project partner, licensee and investor are labelled separately.
- Funding amounts default private.
- A profile without anything published says so.

## Requirements

### Functional Requirements

- **FR-001**: The public read MUST be computed from current publication and consent state on every request, with no cache in R1.
- **FR-002**: The public profile route MUST be readable without sign-in and reveal no private field.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC55–AC57 pass; a test asserts private strings never appear in public responses.

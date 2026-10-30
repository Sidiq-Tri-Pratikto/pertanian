# Feature Specification: Usability study kit

**Feature Branch**: `044-usability-kit`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M10 Platforms and usability
**Depends on**: 043
**Size**: S
**Covers**: UX-16, AT-52
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Run the study without improvising (Priority: P1)

**Why this priority**: Household and industry results must be reported separately (PRD §3, §20.1).

**Independent Test**: A moderator reads the kit and runs a pilot session.

**Acceptance Scenarios**:

1. **Given** the kit, **When** used, **Then** it holds neutral Indonesian tasks, recruitment criteria, consent text, a result sheet and reporting rules.
2. **Given** results, **When** reported, **Then** each segment reports alone, with no combined average hiding a failure.

### Edge Cases

- A participant study that has not happened stays "pending".
- Targets of 4 of 5 and 30 seconds are formative, not population estimates.
- No identifying personal data enters the repository.

## Requirements

### Functional Requirements

- **FR-001**: The kit MUST use the tasks in PRD §20.1 and the handoff §14 scripts.
- **FR-002**: Recording requires consent.

### Key Entities

None.

## Success Criteria

### Measurable Outcomes

- **SC-001**: One pilot session finds the kit runnable.

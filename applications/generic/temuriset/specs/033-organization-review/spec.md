# Feature Specification: Optional organization review

**Feature Branch**: `033-organization-review`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M10 Governance
**Depends on**: 011, 023
**Size**: L
**Covers**: FR20, AC58, AC59, AC60, S17, UX-18
**Flips**: manifest capability `organization_review` → `available`; web registry `tinjauan-organisasi` → `available`

## User Scenarios & Testing

### User Story 1 - Review the exact version, only when the composition enables it (Priority: P1)

In `generic-with-review`, an organization can require review before publication and before submission. A reviewer with `review_publication` sees a queue (S17) with the exact version, a versioned checklist and scope, and approves or returns with a reason.

**Acceptance Scenarios**:

1. **Given** `generic-base` and an independent inventor, **When** publishing and pitching, **Then** no review gate appears and the core flow works (AC58).
2. **Given** review enabled, **When** an organization submits a pitch, **Then** it is `PENDING_WORKSPACE_REVIEW` until a reviewer approves that exact version.
3. **Given** a reviewer approved version 3, **When** version 4 with a material change is submitted, **Then** the earlier approval does not authorize it (AC59).
4. **Given** pending review items, **When** the composition is changed to disable review, **Then** the change is refused until each item is resolved or transferred (AC60).
5. **Given** a return, **When** it is saved, **Then** the pitch or publication goes back to its previous state with the reason.

### Edge Cases

- Reviewers cannot decide a partner's pitch or certify fields outside their checklist.
- Review is never a third persona; it is a capability on a membership.
- UX-18: the base, review-enabled and funding-disabled compositions each run their journeys in CI.

## Requirements

### Functional Requirements

- **FR-001**: The publication gate from 009 and the submission gate from 023 MUST be implemented here behind `require_capability("organization_review")`.
- **FR-002**: Checklists MUST be versioned; an approval MUST bind to the reviewed version.
- **FR-003**: A composition-change command MUST refuse to disable review with pending items.

### Key Entities

- **ReviewChecklist**, **ReviewItem**, **ReviewDecision**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC58–AC60 pass; CI runs the journey suite against all three compositions.

# Feature Specification: Reports, moderation and privacy requests

**Feature Branch**: `034-moderation-privacy-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M10 Governance
**Depends on**: 010
**Size**: M
**Covers**: FR22, AC64, AC66
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Report privately; operators act within scope (Priority: P1)

Users report impersonation, unsupported claims, unwanted contact or abuse with a private reason and the object. Operators with a scoped capability see a queue, act, and every action is audited.

**Acceptance Scenarios**:

1. **Given** a report of impersonation, **When** filed, **Then** a private case exists and the reporter sees its status only (AC64).
2. **Given** an operator suspends a listing, **When** applied, **Then** new actions stop and public discovery hides it, while ongoing cases stay handled.
3. **Given** an operator without a case-specific grant, **When** it requests a confidential file, **Then** it is refused.

### User Story 2 - Privacy requests tell the truth (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a deletion request where an audit hold applies, **When** answered, **Then** the response lists removed categories, retained categories and the reason, and promises nothing about copies recipients already downloaded (AC66).
2. **Given** an export request, **When** fulfilled, **Then** it contains the requester's data under current permissions.

### Edge Cases

- Reports never lower public reputation; there are no ratings.
- Analytics never store message or file contents.

## Requirements

### Functional Requirements

- **FR-001**: Operators MUST be a scoped capability, not a persona, and every operator action MUST be audited.
- **FR-002**: Retention categories MUST be data in a policy table, so the answer to a deletion request is generated, not hand-written.

### Key Entities

- **Report**, **OperatorAction**, **PrivacyRequest**, **RetentionPolicy**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC64 and AC66 pass; operator file access without a grant is refused and audited.

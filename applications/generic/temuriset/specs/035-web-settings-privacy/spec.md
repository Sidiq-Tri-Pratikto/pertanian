# Feature Specification: Profile, privacy and reports screens

**Feature Branch**: `035-web-settings-privacy`
**Created**: 2026-11-05
**Status**: In progress
**Milestone**: M10 Governance
**Depends on**: 008, 026, 034
**Size**: S
**Covers**: S18, FR22
**Flips**: web registry `privasi-laporan` → `available`

## User Scenarios & Testing

### User Story 1 - Report, export and delete with honest explanations (Priority: P1)

S18 gains "Laporkan masalah", "Minta ekspor data" and "Minta penghapusan data", each with status and plain explanations of what is kept and why.

**Acceptance Scenarios**:

1. **Given** a report, **When** sent, **Then** a case number and status appear; the reason field is required with an error summary when empty.
2. **Given** a deletion request answered with a retention hold, **When** shown, **Then** removed and retained categories and reasons are listed.
3. **Given** the workspace pitch room, **When** "Laporkan" is pressed, **Then** the report form opens with the object prefilled.

## Requirements

### Functional Requirements

- **FR-001**: Copy MUST state that downloaded copies cannot be recalled and that reports do not affect public reputation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: View tests, axe and a Playwright report flow pass.

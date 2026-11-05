# Feature Specification: Preflight and editable brief

**Feature Branch**: `022-preflight-brief-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M6 Pitch submission
**Depends on**: 010, 019
**Size**: M
**Covers**: FR12, AC34, AC35, AC36, AC68
**Flips**: none

## User Scenarios & Testing

### User Story 1 - See exactly what would be sent (Priority: P1)

Preflight returns recipient, opportunity version, source and invention versions, purpose, requirement rows, the files eligible to share, money scope, and a deterministic template brief, under a token that pins all versions and the permission generation.

**Why this priority**: FR12; submission (023) accepts only a fresh preflight.

**Independent Test**: Preflight F01 → A1 and read the brief.

**Acceptance Scenarios**:

1. **Given** F01 → A1, **When** preflight runs, **Then** it returns `READY_TO_SUBMIT`, the function file version 1 as selectable, and a brief with problem, current solution, Saat ini and Direncanakan facts, requested support, money with subject and basis, relevance, unresolved work and team.
2. **Given** the opportunity changes after preflight, **When** the token is checked, **Then** it is stale and a fresh preflight is required, while the client's edited brief is kept (AC34).
3. **Given** the summarizer is off or failing, **When** the brief is requested, **Then** the template brief is returned and editable; an AI output with a claim not traceable to a supplied fact is refused (AC35, AC68).
4. **Given** a brief depends on a fact from a document whose grant or ownership access is revoked, **When** the brief is exported, **Then** the dependent part is redacted with a label or the export is refused; no cached text leaks (AC36).

### User Story 2 - Export the brief (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a brief, **When** exported as Markdown or text, **Then** it follows current permissions and states its source versions.

### Edge Cases

- A preflight token expires after 30 minutes or on any version or permission change.
- `BLOCKED_FOR_THIS_TARGET` and `NEEDS_INFORMATION` preflights are returned, but cannot be submitted.
- The brief carries dependency references so redaction is exact.

## Requirements

### Functional Requirements

- **FR-001**: A preflight record MUST pin source version, invention versions, opportunity version, configuration revision and permission generation.
- **FR-002**: The template brief MUST be built only from supplied facts, with references per sentence.
- **FR-003**: The summarizer MUST be a port with `off` (default) and adapters from 044; output is validated against references.
- **FR-004**: Export MUST recheck permissions at export time.

### Key Entities

- **Preflight**, **Brief**, **BriefDependency**, **SummarizerPort**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC34–AC36 and AC68 (summarizer off) pass.

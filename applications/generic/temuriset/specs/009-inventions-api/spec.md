# Feature Specification: Inventions and publication versions

**Feature Branch**: `009-inventions-api`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M2 Portfolio and evidence
**Depends on**: 007
**Size**: L
**Covers**: FR03, FR04, AC07, AC08, AC09, AC10, AC11
**Flips**: none (`core` flips only at 024 when the first journey completes)

## User Scenarios & Testing

### User Story 1 - Save a draft, publish an immutable version (Priority: P1)

A managing party creates inventions, saves incomplete drafts, and publishes a version. Editing a published invention creates a draft successor while the published version stays visible.

**Why this priority**: FR03; every need, match and pitch references an invention version.

**Independent Test**: Create, save, publish, edit and republish through the API.

**Acceptance Scenarios**:

1. **Given** a party with `edit_portfolio`, **When** it saves a draft with only a title, **Then** the draft is stored with `version` and no publication rule is applied.
2. **Given** a draft, **When** it is published with a title under 5 or over 120 characters, a summary over 350, or no problem, solution, intended users, stage or current capability, **Then** the response is `VALIDATION_FAILED` with Indonesian field messages and the draft is unchanged.
3. **Given** two published inventions from one party, **When** each is read, **Then** versions, facts and claims stay separate (AC07).
4. **Given** a published version referenced by a submission, **When** the owner edits and republishes, **Then** a new version number is created and the old version's content is unchanged (AC08).
5. **Given** an archived invention, **When** discovery or a new submission is attempted, **Then** it is absent or refused, while its existing history stays readable to authorized parties (AC09).

### User Story 2 - Facts say what exists and who said so (Priority: P1)

**Acceptance Scenarios**:

1. **Given** facts "Kapasitas saring 10 L/jam" CURRENT and "20 L/jam" PLANNED, **When** read, **Then** each keeps its timing and provenance (`SELF_DECLARED`, `PROVIDED`, `SOURCE_REPORTED`, `REVIEWED`, `UNKNOWN`).
2. **Given** a fact linked to a document version, **When** the document is superseded, **Then** the fact still names the version it came from.

### User Story 3 - Rights and authority are claims, not certificates (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a creator "Rani" and an asserted rights holder that differs, **When** read, **Then** both appear as separate claims with scope, source, date and status, and nothing infers ownership (AC10).
2. **Given** no patent and no company, **When** the invention is published, **Then** publication succeeds (AC11).
3. **Given** a claim "not yet established", **When** read, **Then** it is shown as such and never as absent.

### Edge Cases

- Two tabs saving one draft: the second gets `STALE_VERSION` with the current draft.
- Public projection includes only published fields; private notes never enter it.
- Reassigning the managing party is out of scope; a name edit never changes ownership.

## Requirements

### Functional Requirements

- **FR-001**: Inventions MUST have one managing party, a published pointer and at most one draft.
- **FR-002**: Versions MUST be immutable once published; publication MUST validate the PRD fields.
- **FR-003**: Facts MUST carry label, value, unit, timing, provenance, optional key and optional document version.
- **FR-004**: Claims MUST keep creator, contributor, manager, rights holder and authority separate, with scope, source, date and status.
- **FR-005**: Publishing and archiving MUST emit audit and outbox events (`invention.published`, `invention.archived`) for the search projection in 018.
- **FR-006**: The organization-review hook MUST exist as a no-op interface that 033 implements.

### Key Entities

- **Invention**, **InventionVersion**, **InventionFact**, **InventionClaim**, **PublicInventionProjection**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC07–AC11 pass as integration tests with the isolation harness extended to every new route.

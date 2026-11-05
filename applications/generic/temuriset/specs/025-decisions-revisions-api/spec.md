# Feature Specification: Decisions and itemized revisions

**Feature Branch**: `025-decisions-revisions-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M7 Review and revisions
**Depends on**: 023
**Size**: L
**Covers**: FR14, FR15, AC40, AC41, AC42, AC43, AC44, AC45
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Three decisions, each meaning only itself (Priority: P1)

An authorized recipient begins review, approves for discussion, requests revision, or rejects with a private reason, on the exact submission and pitch version.

**Acceptance Scenarios**:

1. **Given** a submitted pitch, **When** Mitra A approves, **Then** status is `APPROVED_FOR_DISCUSSION`, and no funding, partnership or commitment record exists (AC40).
2. **Given** two decisions on the same version at once, **When** both commit, **Then** one succeeds and the other gets `STALE_VERSION` (AC41).
3. **Given** a withdrawn submission, **When** a decision is attempted, **Then** `INVALID_TRANSITION` and nothing reopens; no public reputation changes (AC42).
4. **Given** a rejection without reason, **When** sent, **Then** `VALIDATION_FAILED` asks for a short reason visible only to the sender.
5. **Given** an approved pitch, **When** revision is requested, **Then** `INVALID_TRANSITION`; clarification uses tasks (027).

### User Story 2 - Revision rounds that respect honest answers (Priority: P1)

**Acceptance Scenarios**:

1. **Given** round 1 with a required pilot-budget question and an optional planned-feature question, **When** Rani answers the required one "Belum dapat dipenuhi", **Then** resubmission is allowed and nothing is auto-approved (AC43).
2. **Given** an answer adds a planned feature, **When** facts are read, **Then** it stays PLANNED unless evidence changes the invention (AC44).
3. **Given** resubmission with a new file version, **When** it commits, **Then** submission 2 freezes the selected versions, submission 1 and round 1 answers stay, and the review gate reapplies when enabled (AC45).
4. **Given** a required item unanswered, **When** resubmitting, **Then** `REQUIRED_ANSWERS_MISSING` lists the items.
5. **Given** the recipient reviews an answer, **When** it marks "Diterima" or "Perlu detail", **Then** the mark is stored per item.

### Edge Cases

- A failed attachment upload never clears other answers.
- Answers save as drafts with their own version; resubmission is a separate consequential action.
- Silence never approves; withdrawal stops later decisions.

## Requirements

### Functional Requirements

- **FR-001**: Decisions MUST reference submission number and expected pitch version, and be idempotent.
- **FR-002**: Items MUST carry category, question, reason, required flag, due date and expected evidence.
- **FR-003**: Answers MUST be `CAN`, `DISCUSS` or `CANNOT` with text and selected file versions.
- **FR-004**: State changes MUST follow PRD section 7 exactly; any other transition is `INVALID_TRANSITION`.

### Key Entities

- **Decision**, **RevisionRound**, **RevisionItem**, **RevisionAnswer**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC40–AC45 pass; a transition table test covers every state and action pair.

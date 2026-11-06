# Feature Specification: Deliberate pitch submission

**Feature Branch**: `023-pitch-submission-api`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M6 Pitch submission
**Depends on**: 022
**Size**: L
**Covers**: FR13, AC26, AC37, AC38, AC39
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Send once, on purpose (Priority: P1)

A submit freezes the request and invention versions, brief, selected document versions with new grants, declared facts and permission metadata, after rechecking the preflight.

**Why this priority**: FR13; every collaboration step hangs off a submission.

**Independent Test**: F01 → A1 with replays and conflicts.

**Acceptance Scenarios**:

1. **Given** a fresh preflight and chosen file version 1, **When** `POST /pitches` is sent with an idempotency key, **Then** one pitch and submission 1 exist, Mitra A has a grant to version 1 only, and Mitra A is notified.
2. **Given** a lost response, **When** the same request is retried with the same key, **Then** the original pitch is returned once (AC37).
3. **Given** the same key with a different target or brief, **When** sent, **Then** `IDEMPOTENCY_CONFLICT` and no second pitch (AC38).
4. **Given** FRaise01 already pitched to B1, **When** a pitch is prepared through the second linked invention, **Then** `DUPLICATE_PITCH` returns the existing pitch id (AC39).
5. **Given** the opportunity closed after preflight, **When** submitting, **Then** `TARGET_CLOSED` explains that new pitches stop and existing discussions remain (AC26).
6. **Given** a stale preflight, **When** submitting, **Then** `PREFLIGHT_STALE` asks for a fresh check and keeps the client's brief.
7. **Given** a requirement for file presence, **When** no file is chosen, **Then** `NOT_READY` names it.

### Edge Cases

- The subject is exactly one support request or one funding request, never both.
- The default limit is five new pitches per actor per day (policy `pitch-rate-limit` v1), disclosed in the error.
- Later edits to the invention or request never change the submission (AC08 for pitches).
- The organization-review gate from 033 may hold the pitch in `PENDING_WORKSPACE_REVIEW`.

## Requirements

### Functional Requirements

- **FR-001**: The active-pitch uniqueness MUST be a partial unique index, not only a service check.
- **FR-002**: Submission, grants, audit and outbox MUST commit in one transaction.
- **FR-003**: The submit MUST recheck intake status, versions, readiness and permissions.
- **FR-004**: The snapshot MUST store references plus the facts shown, never document bytes.

### Key Entities

- **Pitch**, **PitchSubmission**, **PitchSubmissionFile**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC26 and AC37–AC39 pass; 20 parallel identical submits create one pitch.

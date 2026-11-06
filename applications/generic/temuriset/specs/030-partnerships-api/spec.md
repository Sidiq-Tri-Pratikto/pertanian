# Feature Specification: Relationship records confirmed on the same version

**Feature Branch**: `030-partnerships-api`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M9 Relationships
**Depends on**: 014, 028
**Size**: L
**Covers**: FR18, AC21, AC52, AC53, AC54
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Propose, correct, confirm the same version (Priority: P1)

After a completed meeting, either party proposes a PROJECT, LICENSE or EQUITY summary with values, a public-field ceiling and its own consent subset. The other party confirms the same version or requests a correction, which creates a new version with no confirmations.

**Acceptance Scenarios**:

1. **Given** Rani proposes version 1, **When** only Rani has confirmed, **Then** status is `PENDING_COUNTERPARTY` and no mutual badge or public field exists (AC52).
2. **Given** Mitra A requests a scope correction, **When** version 2 is created, **Then** version 1 is `CHANGES_REQUESTED`, version 2 has no confirmations, and a version-1 confirmation cannot confirm version 2 (AC53).
3. **Given** both confirm version 2 with Rani permitting name, type, scope, date and amount and Mitra A permitting name, type, scope and date, **When** read, **Then** status is `CONFIRMED` and effective public fields exclude amount.
4. **Given** a PROJECT record with an amount, **When** read, **Then** no share, percentage or ownership exists (AC54).
5. **Given** a proposed company, **When** EQUITY is proposed, **Then** `ENTITY_REQUIRED` refuses it; discussion stays open (AC21).

### User Story 2 - Narrow at once; expand only by agreement (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a confirmed record, **When** a party restricts "date", **Then** an append-only restriction applies on the next read and history is unchanged.
2. **Given** a party wants to add amount, **When** it proposes, **Then** a new version starts and the old confirmed version stays effective until both confirm.
3. **Given** a party contests the public claim, **When** review is requested, **Then** the public projection hides it while private history stays.

### Edge Cases

- No relationship can be proposed before a completed meeting.
- EQUITY percentage needs an explicit permission and an effective date.
- One equity relationship can reference two inventions without doubling anything.

## Requirements

### Functional Requirements

- **FR-001**: Confirmations MUST bind to a version checksum.
- **FR-002**: Effective public fields MUST be computed on read: subset intersection within the ceiling minus restrictions.
- **FR-003**: Every confirmation MUST check `confirm_relationship` capability and acting context, with idempotency.

### Key Entities

- **Partnership**, **PartnershipVersion**, **Confirmation**, **Restriction**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC21 and AC52–AC54 pass; a property test shows effective fields never exceed either subset.

## Validation

The integrated API tests passed the same-version, race and route-isolation checks. Alembic reached `0017` from M8's `0015`, then passed downgrade, re-upgrade and schema drift checks.

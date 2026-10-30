# Feature Specification: Asset edit and archive

**Feature Branch**: `016-asset-edit`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M2 Read journey on phone
**Depends on**: 014
**Size**: S
**Covers**: FR-03, AT-43, S06
**Flips**: registry `detail-perangkat` → `available` (with 015)

## User Scenarios & Testing

### User Story 1 - Rename safely (Priority: P1)

**Why this priority**: Names are how people read the product; IDs must not change.

**Independent Test**: Rename and confirm the ID and history are unchanged.

**Acceptance Scenarios**:

1. **Given** the edit sheet, **When** a valid name is saved, **Then** the list and detail update after acknowledgment only.
2. **Given** a rejected save, **When** it fails, **Then** the draft stays, the old name stays confirmed, and retry is offered.
3. **Given** an empty name, **When** Simpan is pressed, **Then** the field shows the correction and focus moves to the error summary.

### User Story 2 - Archive reversibly (Priority: P1)

**Why this priority**: AT-43: archive, unlink and delete each stay within their declared scope.

**Independent Test**: Archive, restore, compare totals.

**Acceptance Scenarios**:

1. **Given** an asset, **When** archived after confirmation, **Then** it leaves the selection, readings stay, and it appears under Diarsipkan.
2. **Given** an archived asset, **When** restored, **Then** its history and totals return.

### Edge Cases

- The confirmation states the specific scope.
- Unlinking a source never deletes readings.
- Back from the sheet keeps the draft until Buang draf.

## Requirements

### Functional Requirements

- **FR-001**: Edits MUST use `PATCH /assets/{id}` with name, category and location.
- **FR-002**: Confirmed values MUST NOT change before acknowledgment.
- **FR-003**: Archive MUST be reversible and MUST NOT delete data.

### Key Entities

Asset from 005.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Failed save leaves server and screen unchanged.
- **SC-002**: Archive plus restore returns identical totals.

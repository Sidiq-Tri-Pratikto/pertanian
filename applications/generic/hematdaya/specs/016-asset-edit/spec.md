# Feature Specification: Asset edit and archive

**Feature Branch**: `016-asset-edit`
**Created**: 2026-10-30
**Status**: Implemented and verified in automated tests and Chrome against the live API. Native interaction and spoken screen-reader checks are pending.
**Milestone**: M2 Read journey on phone
**Depends on**: 014, 015
**Merged implementation input**: [027 form components](../027-import-s10/spec.md)
**Size**: S
**Covers**: FR-03, AT-43, S06
**Flips**: registry `detail-perangkat` → `available` (with 015)

## User Scenarios & Testing

### User Story 1 - Rename safely (Priority: P1)

**Why this priority**: Names are how people read the product; IDs must not change.

**Independent Test**: Rename and confirm the ID and history are unchanged.

**Acceptance Scenarios**:

1. **Given** the edit sheet, **When** a valid change is submitted, **Then** the list and detail keep their confirmed values until a matching acknowledgment or a fresh service read establishes the current values.
2. **Given** a rejected save, **When** the server confirms it was rejected, **Then** the draft stays, the old name stays confirmed, and the next action follows the error recovery guidance.
3. **Given** an empty name, **When** Simpan is pressed, **Then** the field shows the correction and focus moves to the error summary.
4. **Given** the outcome is unknown, **When** a fresh service read matches the submitted fields, **Then** the app confirms the observed values and sends no duplicate edit.
5. **Given** a fresh read differs from an unconfirmed submission, **When** the result is shown, **Then** the app keeps the draft, shows the observed values and requires review and a new explicit save. The original request may still complete. The service applies 005's last-write-wins behavior to each write.

### User Story 2 - Archive reversibly (Priority: P1)

**Why this priority**: AT-43: archive, unlink and delete each stay within their declared scope.

**Independent Test**: Archive, restore, compare totals.

**Acceptance Scenarios**:

1. **Given** an asset, **When** archived after confirmation, **Then** it leaves the selection, readings stay, and it appears under Diarsipkan.
2. **Given** an archived asset, **When** restored, **Then** its history and totals return.
3. **Given** the active summary is empty or unavailable, **When** an owned archived asset can be read, **Then** the user can open it from Diarsipkan and restore it.

### Edge Cases

- The confirmation states the specific scope.
- Unlinking a source never deletes readings.
- Back from the sheet keeps the draft until Buang draf.
- When the app already knows it is offline, save keeps the draft and explains that nothing was sent. Reconnecting does not submit it. Losing the connection after dispatch leaves the outcome unknown.

## Requirements

### Functional Requirements

- **FR-001**: Edits MUST use `PATCH /assets/{id}` and send only changed values for name, category or location.
- **FR-002**: The app MUST keep confirmed values separate from the draft and update them only from a valid matching acknowledgment or a fresh service read. A reconciliation read confirms state at read time. It cannot attribute a change to the original PATCH or establish that the request has finished.
- **FR-003**: Archive MUST be reversible and MUST NOT delete data.
- **FR-004**: Archive and restore MUST set `archived` to `true` and `false`, respectively, using the existing PATCH route from 005 and the same acknowledgment and unknown-outcome rules as edits.

### Key Entities

Asset from 005.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A known rejection leaves the server and confirmed values unchanged. A timeout after commit can reconcile to the observed state with one PATCH. A divergent or failed read causes no automatic write.
- **SC-002**: Archive and restore preserve measurement identities, values and binding history. Restoring returns identical totals for the same valid selection and period.

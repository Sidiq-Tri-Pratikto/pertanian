# Feature Specification: Scope screen

**Feature Branch**: `029-scope-s11`
**Created**: 2026-10-30
**Status**: Implemented and verified locally. Hosted Android gate pending.
**Milestone**: M6 Scope
**Depends on**: 013, 014, 028
**Size**: M
**Covers**: UX-19, AT-57, S11, P09
**Flips**: registry `cakupan-sumber` → `available`

## User Scenarios & Testing

### User Story 1 - Resolve an overlap (Priority: P1)

**Why this priority**: AT-57: selected equipment scope stays distinct from time completeness.

**Independent Test**: Scope scenario end to end.

**Acceptance Scenarios**:

1. **Given** the scope scenario, **When** S11 opens, **Then** sources, physical inclusion, current selection and why the total is blocked are visible.
2. **Given** a parent and children, **When** a view is chosen, **Then** options read "Meter utama · 10 kWh" or the child view, never a sum.
3. **Given** two sources, **When** one is chosen in the draft, **Then** the server previews child values without saving the choice.
4. **Given** a valid preview, **When** Konfirmasi cakupan is pressed, **Then** the selection and proposed authority save together. The confirmed energy summary updates from a fresh matching summary read after acknowledgment.
5. **Given** a scope issue or an old scope link, **When** S11 opens, **Then** it keeps the active tab and period. On return, focus goes back to the invoking control if it is still present.

### User Story 2 - Failure changes nothing (Priority: P1)

**Why this priority**: S11 contract.

**Independent Test**: Reject a reviewed save, then simulate losing the acknowledgment after dispatch and check recovery across a reload.

**Acceptance Scenarios**:

1. **Given** a rejected save, **When** it fails, **Then** the proposal stays for retry and the previous confirmed summary is still used.
2. **Given** a proposed source authority, **When** Batal is pressed, **Then** the confirmed authority, selection, and summary are unchanged.
3. **Given** a stale preview, **When** confirmation is rejected, **Then** the draft stays and the app asks the user to refresh the preview. A changed revision or rolled local period can make it stale. Newly arrived measurements or a moving cutoff within the same local period alone do not.
4. **Given** a lost acknowledgment, **When** the app checks the owned confirmed state or reopens after reload, **Then** it preserves uncertainty until it has newer confirmed evidence. An unchanged revision pair cannot rule out a pending commit. A new save requires a fresh preview and a separate explicit confirmation under the server revision checks. Reconnect and reload send no PUT.
5. **Given** the server acknowledges a save but local storage or refresh fails, **When** S11 reports the result, **Then** it distinguishes the server acknowledgment from the local failure. Prior figures carry their original scope, period and timestamp if displayed.

### Edge Cases

- A conflicted child is never shown as 0.
- Scope and completeness keep separate labels.
- The primary action is disabled with a stated reason until valid. A valid scope can have unavailable energy.
- A chosen source shows its effective instant before confirmation. A source choice or disjoint confirmation leaves the draft when an involved asset is excluded or archived.
- When no durable attempt record can be written, the app blocks the save before dispatch. A cache from another, expired or unconfirmed owner is never shown.

## Requirements

### Functional Requirements

- **FR-001**: S11 MUST show included and excluded assets with reasons before confirmation.
- **FR-002**: Beranda and Perangkat MUST link here from any scope issue.
- **FR-003**: S11 MUST preview and confirm the same full proposal through 028. Confirmation carries the original period request, the preview’s selection and binding revisions, and its resolved local dates and timezone. Any edit invalidates the existing preview.
- **FR-004**: S11 MUST separate draft and confirmed state. It MUST track an uncertain save under the active owner across reloads, with no automatic write or claim of attribution from a confirmed-state read.
- **FR-005**: The app MUST keep confirmed summaries bound to owner, scope identity and resolved window. Once a newer confirmed scope is observed, older figures may appear only with their original context and a previous-scope label. A source refresh continues to read only the current summary.

### Key Entities

028 selection, full draft proposal, reviewed preview, and confirmed summary identity. A local attempt record stores revision evidence for recovery and contains no executable proposal.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The screen never displays a combined value for an invalid selection.

# Feature Specification: Import screens

**Feature Branch**: `027-import-s10`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M5 CSV
**Depends on**: 012, 013, 026
**Size**: L
**Covers**: UX-20, AT-03, AT-44, AT-58, S10, P02
**Flips**: registry `impor-data` → `available`

## User Scenarios & Testing

### User Story 1 - First data from a file (Priority: P1)

**Why this priority**: P02 and AT-03: a neutral user with no demo reaches real totals.

**Independent Test**: Empty workspace → import → Beranda.

**Acceptance Scenarios**:

1. **Given** S02, **When** the user imports a valid file, **Then** the steps are Periksa berkas → Lihat pratinjau → confirm → Lihat periode data, and Beranda lands on the imported range.
2. **Given** a paste instead of a file, **When** checked, **Then** the same flow runs.
3. **Given** an example, **When** chosen, **Then** it fills the input and can be copied.

### User Story 2 - Recover from anything (Priority: P1)

**Why this priority**: AT-58.

**Independent Test**: Each failure path.

**Acceptance Scenarios**:

1. **Given** errors, **When** shown, **Then** a focused summary links to row messages with stated numbering.
2. **Given** 2 of 10 invalid, **When** confirming without acknowledgment, **Then** the error links to the checkbox.
3. **Given** an unknown commit result after a lost connection, **When** the user selects Periksa status, **Then** the app checks the existing import first. It shows a committed result when found and keeps the original operation key if another attempt is needed.
4. **Given** back from preview or mapping, **When** pressed, **Then** content and mapping are retained.
5. **Given** a browser restart, **When** the flow reopens, **Then** the app says a file needs reselecting.

### User Story 3 - Hostile text stays text (Priority: P2)

**Why this priority**: AT-44.

**Independent Test**: Import names such as `=HYPERLINK(...)` and `<script>`.

**Acceptance Scenarios**:

1. **Given** such names, **When** displayed anywhere, **Then** they render as plain text.

### Edge Cases

- Replace-file is explicit.
- Import cancel returns to S02 without losing other data.
- Long keyboards never hide the primary action or the active field.

## Requirements

### Functional Requirements

- **FR-001**: The requirements panel MUST show before parsing.
- **FR-002**: Primary actions MUST change by step.
- **FR-003**: `HDImportPreview` MUST carry file line numbers from the service, fixing the web component's assumption.
- **FR-004**: Commit MUST prevent double submission and retain the import ID and operation key through uncertain results and retries. A status check MUST precede retrying an unknown result.

### Key Entities

Import from 025 and 026.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every import example from the prototype passes by keyboard on web and by touch on Android.
- **SC-002**: UX-20 check is recorded with row and file-line evidence.

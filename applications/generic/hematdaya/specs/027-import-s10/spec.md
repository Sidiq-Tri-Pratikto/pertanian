# Feature Specification: Import screens

**Feature Branch**: `m5/import-screens`
**Created**: 2026-10-30
**Status**: Implemented and verified in Chrome against the live API. Android and iOS bundles export. Native file picking, keyboard avoidance and screen readers were not run.
**Milestone**: M5 CSV
**Depends on**: 012, 026
**Size**: L
**Covers**: UX-20, AT-03, AT-44, AT-58, S10, P02
**Flips**: registry `impor-data` → `available`

014 is merged too. This spec repoints its Perangkat entry points and reuses its `ReadFailure`, but needs nothing 014 left unfinished. AT-44's export half belongs to 038; this spec covers names rendered as text.

## User Scenarios & Testing

### User Story 1 - First data from a file (Priority: P1)

**Why this priority**: P02 and AT-03: a neutral user with no demo reaches real totals. Under the open clock question (Assumptions), that holds for files dated before the workspace's clock, and the screen says so for any other file.

**Independent Test**: Empty workspace → import an example dated 20 Oktober 2026 → Beranda shows that day's imported values.

**Acceptance Scenarios**:

1. **Given** S02, **When** the user imports a valid file, **Then** the steps are Periksa berkas → Lihat pratinjau → Konfirmasi impor → Lihat periode data, and Beranda lands on the imported range. A range longer than 366 days lands on its last 366 days and says so.
2. **Given** a paste instead of a file, **When** checked, **Then** the same flow runs.
3. **Given** an example, **When** chosen, **Then** it fills the input and can be copied.
4. **Given** a file whose rows all end after the workspace's clock, **When** committed, **Then** the result says the rows are stored and not shown yet, and offers Kembali ke Beranda instead of Lihat periode data. With some rows after the clock, it says how many are not counted.
5. **Given** a file whose every row is already stored, **When** committed, **Then** the result says no row is new and how many duplicates were counted once.

### User Story 2 - Recover from anything (Priority: P1)

**Why this priority**: AT-58.

**Independent Test**: Each failure path.

**Acceptance Scenarios**:

1. **Given** errors, **When** shown, **Then** a summary links to row messages with stated numbering, using the service's data row and file line, and takes focus when it appears after the user's action.
2. **Given** 2 of 10 invalid, **When** confirming without acknowledgment, **Then** the error links to the checkbox and nothing is sent.
3. **Given** an unknown commit result after a lost connection or a timeout, **When** the user selects Periksa status, **Then** the app checks the existing import first. It shows a committed result when found and keeps the original operation key if another attempt is needed.
4. **Given** back from preview or mapping, **When** pressed, **Then** content and mapping are retained.
5. **Given** a web page reload or a restored browser session, **When** the flow reopens, **Then** the app says a file needs reselecting and never claims the file was recovered. A quit without session restore also ends the temporary workspace (012), so the app returns to S01.
6. **Given** a commit refused as stale, blocked, unacknowledged, conflicting or gone, **When** shown, **Then** the screen names what happened, shows the service's details and reference, and offers only the safe next step.

### User Story 3 - Hostile text stays text (Priority: P2)

**Why this priority**: AT-44.

**Independent Test**: Import names such as `=HYPERLINK(...)` and `<script>`.

**Acceptance Scenarios**:

1. **Given** such names, **When** displayed anywhere, **Then** they render as plain text.

### Edge Cases

- Replace-file is explicit: choosing other content while content, answers or a preview exist asks first, and cancelling changes nothing.
- Import cancel returns to S02 without losing the draft or other data.
- The primary action and the active field stay visible when the keyboard opens: the primary action sits in a footer outside the scroll view, and the screen avoids the keyboard. Checked on web at 320 px; native keyboards are not run in this spec.
- No workspace, or a session that ends mid-flow: S10 offers a new temporary workspace and keeps typed content, and sends no import request.
- A lost or timed-out preview cannot be found again, because previews carry no key: the app says nothing was saved and offers a new check.
- Scope answers apply only between assets in one file, so a second file's new asset leaves the combined total refused until 029. The screen never implies otherwise.
- More than 100 assets in a file, more than 20% invalid rows, conflicts and open questions block with the service's reasons, shown verbatim.
- More than 50 row errors page through the error list, and loaded rows stay when a page fails.
- Importing into a seeded demo mixes simulated and imported data, and both provenance tags show.
- A name the file writes in another case than the stored asset is answered under the file's spelling.

## Requirements

### Functional Requirements

- **FR-001**: The requirements panel MUST show before parsing.
- **FR-002**: Primary actions MUST change by step: Periksa berkas, Lihat pratinjau, Konfirmasi impor, then Lihat periode data, or Kembali ke Beranda when the result has nothing new to show.
- **FR-003**: `HDImportPreview` MUST carry file line numbers from the service, fixing the web component's assumption.
- **FR-004**: Commit MUST prevent double submission and retain the import ID and operation key through uncertain results and retries, while the app runs and across a web reload. A status check MUST precede retrying an unknown result.
- **FR-005**: Each failure MUST branch on the public `code`, never on text, with a defined behaviour for `IMPORT_INVALID`, `IMPORT_TOO_LARGE`, `IMPORT_BLOCKED`, `IMPORT_STALE`, `IMPORT_ACK_REQUIRED`, `CONFLICT`, `NOT_FOUND`, `VALIDATION_FAILED` and an ended session, showing `details` where they carry specifics and always the reference ID.
- **FR-006**: Preview and commit requests MUST have timeouts long enough for a file at the limits, and a commit timeout MUST count as an unknown result.
- **FR-007**: The result MUST state `rows_after_site_clock` when it is above zero and MUST NOT say the data is visible when it is not.
- **FR-008**: Counts, block reasons, assumptions, questions and acknowledgment MUST come from the service, rendered without recomputation.
- **FR-009**: Imported data MUST carry "Data historis · Impor CSV", and a period mixing simulated and imported data MUST show both.
- **FR-010**: Every import entry point MUST open S10, and Pengaturan MUST stop listing import as planned.

### Key Entities

Import from 025 and 026. The client adds an import draft (source, answers, preview, commit intent) that belongs to one workspace's site.

### Assumptions

- The `empty` scenario keeps 008's fixed clock (2026-10-26 00.00 WIB) until the owner and P1 decide otherwise.
- No API change. File picking adds one native dependency, `expo-document-picker`, justified in `tasks.md` D1.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every import example from the prototype passes by keyboard on web and by touch on Android. The Android half needs a device or emulator run, which this spec's CI job cannot reach, so it stays recorded as not run until one is made.
- **SC-002**: UX-20 check is recorded with row and file-line evidence.
- **SC-003**: AT-03's evidence names its file dates and the workspace clock, and the after-clock path is recorded separately.

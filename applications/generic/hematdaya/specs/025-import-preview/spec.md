# Feature Specification: Import preview

**Feature Branch**: `m5/csv-parser`
**Created**: 2026-10-30
**Status**: Built, awaiting review
**Milestone**: M5 CSV
**Depends on**: 024
**Size**: M
**Covers**: FR-06, AT-30, AT-32, AT-33
**Flips**: none

## User Scenarios & Testing

### User Story 1 - See the result before anything is saved (Priority: P1)

**Why this priority**: PRD §10.2: parse, map, validate and preview before commit.

**Independent Test**: Preview leaves `measurements` unchanged.

**Acceptance Scenarios**:

1. **Given** a parsed file and mapping, **When** previewed, **Then** counts reconcile: accepted unique + invalid + exact duplicate + conflicting + pending = all nonblank data rows. Rows are pending only while a question is open, and a preview with pending rows is blocked.
2. **Given** 2 of 10 rows invalid, **When** previewed, **Then** eight rows can import only after explicit acknowledgment.
3. **Given** 3 of 10 invalid, **When** previewed, **Then** commit is blocked with `Impor diblokir: 3 dari 10 baris tidak valid.`

### User Story 2 - Conflicts and duplicates (Priority: P1)

**Why this priority**: The same interval with different values must never be picked silently.

**Independent Test**: Duplicate and conflict rows.

**Acceptance Scenarios**:

1. **Given** identical repeated rows, **When** previewed, **Then** one is accepted and the rest count as duplicates.
2. **Given** different values for one source and interval, **When** previewed, **Then** they are conflicts and block commit even if the invalid share is low.
3. **Given** `[00:00, 02:00)` and `[01:00, 03:00)` for one source, in the file or against an accepted stored interval, **When** previewed, **Then** the overlapping candidate rows are conflicts even though their interval identities differ. Adjacent half-open intervals are valid.
4. **Given** a reimport of a committed file with the same mapping, **When** previewed, **Then** rows are exact duplicates and the result is a no-op. A file with neither usable rows nor exact duplicates is blocked.

### User Story 3 - Map by identity, not name (Priority: P1)

**Why this priority**: Two assets may share a name (PRD §5.1).

**Independent Test**: Two "Kulkas" assets.

**Acceptance Scenarios**:

1. **Given** two assets with one name, **When** mapped, **Then** the user must pick with location, type and ID context.
2. **Given** a target asset with another source over the file's period, **When** mapped, **Then** preview requires an explicit choice of a new asset and never adds them. Source authority is then chosen in 028.
3. **Given** unknown overlap with existing loads, **When** confirmed as unknown, **Then** the preview is not blocked and stores that answer. 026 records the relation, and totals stay refused until scope is resolved.

### Edge Cases

- A preview survives a restart: it lives in Postgres.
- Skipped invalid rows cannot waive structural, meaning or scope conflicts.
- Stale previews are rejected at commit if stored data changed.
- An uncommitted preview expires after 24 hours of wall-clock time. A site keeps at most 5 uncommitted previews.
- One stream maps to one asset. A source used by two asset names, or two sources on one asset, must be resolved before commit.
- Rows ending after the workspace's product time are listed as an assumption, because reads exclude them until that time arrives.
- A preview on an expiring demo workspace ends with that workspace.

## Requirements

### Functional Requirements

- **FR-001**: Previews MUST be stored with mapping, counts, assumptions and row results.
- **FR-002**: The invalid share MUST use all nonblank data rows as denominator; up to and including 20% may proceed.
- **FR-003**: Limits MUST be enforced server-side, including a cap that stops an oversized upload before it is read in full.
- **FR-004**: Preview MUST NOT change measurements, assets, sources, bindings, relations, audit events or site revisions.
- **FR-005**: Assumptions MUST be listed before confirmation.
- **FR-006**: Preview MUST classify interval overlaps after resolving source identity and MUST limit inline row errors, with remaining errors available by cursor. Exact duplicates and changed values MUST use 006's identity and comparison, so the preview and a later commit agree.
- **FR-007**: A foreign site or import MUST return `NOT_FOUND` before any upload is read, and so MUST an asset ID outside the site. Import is core: it MUST work under the `core-only` composition with no capability guard.
- **FR-008**: Structural and limit failures MUST use `APP-IMPORT-STRUCTURE` and `APP-IMPORT-TOO-LARGE`, with row or limit details, and `APP-IMPORT-BLOCKED` MUST be registered for commit. All follow rule 008, including the catalog. A blocked preview is a stored result, not an error.
- **FR-009**: The routes MUST appear in `contracts/openapi.json` and the generated mobile client.

### Key Entities

- **Import**, **ImportRow**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Counts reconcile in every test.
- **SC-002**: AT-30 and AT-33 thresholds pass exactly.

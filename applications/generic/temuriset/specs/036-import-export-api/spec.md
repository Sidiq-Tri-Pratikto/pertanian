# Feature Specification: JSON import and export

**Feature Branch**: `036-import-export-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M11 Portability and operations
**Depends on**: 010, 016
**Size**: L
**Covers**: FR21, AC06, AC61, AC62, AC63
**Flips**: web registry `impor-ekspor` → `available` (with a minimal upload and preview screen)

## User Scenarios & Testing

### User Story 1 - Preview before apply; never duplicate or overwrite silently (Priority: P1)

A managing party validates a JSON file (schema version, external system and id, provenance), sees a preview, and applies it.

**Acceptance Scenarios**:

1. **Given** the same external system and id imported twice, **When** applied, **Then** the second run updates within the managing context and creates no duplicate, and never upgrades a source-reported relationship to confirmed (AC61).
2. **Given** an import that conflicts with a reviewed rights fact, **When** previewed, **Then** the conflict is flagged and apply skips it unless the owner resolves it (AC62).
3. **Given** an export job whose requester's grant is revoked before download, **When** the result is fetched, **Then** access is denied and the result expires (AC63); the same holds when membership is removed (AC06).

### Edge Cases

- Organizations are never merged by name.
- Private fields need an explicit mapping; absent mapping skips them.
- Large files run as jobs with progress and cancel.

## Requirements

### Functional Requirements

- **FR-001**: Import MUST be validate → preview → apply, each a job with its own status.
- **FR-002**: External references MUST be unique per managing party, system and id.
- **FR-003**: Export results MUST be served through the gateway with current authorization.

### Key Entities

- **ImportRun**, **ExternalReference**, **ExportJob**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC61–AC63 pass; a 1,000-invention import completes as a job with a preview.

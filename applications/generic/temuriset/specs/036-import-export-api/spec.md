# Feature Specification: JSON import and export

**Feature Branch**: `036-import-export-api`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M11 Portability and operations
**Depends on**: 010, 016
**Size**: L
**Covers**: FR21, AC06, AC61, AC62, AC63
**Flips**: web registry `impor-ekspor` → `available` (with a minimal upload and preview screen)

## User Scenarios & Testing

### User Story 1 - Preview before apply; never duplicate or overwrite silently (Priority: P1)

A managing party validates a JSON file with a schema version, external system and ID, and provenance. The party reviews a preview before applying it and can request an export for selected resources.

**Acceptance Scenarios**:

1. **Given** the same external system and id imported twice, **When** applied, **Then** the second run updates within the managing context and creates no duplicate, and source-reported relationship assertions stay separate from confirmed records (AC61).
2. **Given** an import that conflicts with a reviewed rights fact, **When** previewed, **Then** the conflict is flagged and apply skips it until the owner resolves it and reviews a fresh preview (AC62).
3. **Given** an export job whose requester's grant is revoked before download, **When** the result is fetched, **Then** access is denied and the result expires (AC63); the same holds when membership is removed. If authorization is lost while the job is pending, generation is denied too (AC06).

### Edge Cases

- Organizations are never merged by name.
- Private fields need an explicit, authorized mapping. Unmapped fields are skipped.
- Jobs report progress and support cancellation. Cancellation stops the next unit of work and reports records already committed.

## Requirements

### Functional Requirements

- **FR-001**: Import MUST be validate → preview → apply, each a job with its own status.
- **FR-002**: External references MUST be unique per managing party, system and id.
- **FR-003**: Export generation and gateway delivery MUST check live authorization for the requester and every selected resource. A lost dependency expires access to the result.

### Key Entities

- **ImportRun**, **ExternalReference**, **ExportJob**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC06 and AC61–AC63 pass. A 1,000-invention file reaches a completed preview before apply writes any records.

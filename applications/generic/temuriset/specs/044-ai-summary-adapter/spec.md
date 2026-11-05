# Feature Specification: AI brief summary adapter (gated)

**Feature Branch**: `044-ai-summary-adapter`
**Created**: 2026-11-05
**Status**: Seeded, not started; gated
**Milestone**: M12 Gated adapters
**Depends on**: 022
**Size**: M
**Covers**: FR12, AC35, AC68
**Flips**: manifest adapter `ai-summary` → `available`; web registry `ringkasan-otomatis` → `available`

**Entry condition**: an approved model provider with processing terms that permit the supplied facts, and a reviewed evaluation set.

## User Scenarios & Testing

### User Story 1 - Shorter brief, no new claims (Priority: P1)

**Acceptance Scenarios**:

1. **Given** supplied facts, **When** a summary is requested, **Then** every sentence references a supplied fact; output with an unsupported number or claim is refused and the template brief stays (AC35).
2. **Given** the provider is down, **When** requested, **Then** "Ringkasan otomatis tidak tersedia" shows and the template brief remains editable (AC68).
3. **Given** retrieved text containing instructions, **When** summarized, **Then** it is treated as data and never changes behaviour.

## Requirements

### Functional Requirements

- **FR-001**: Model input MUST be assembled only from authorized facts, with one controlled retry then the deterministic fallback.
- **FR-002**: Model identity, version and prompt template version MUST be recorded with each output.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An evaluation set of supported and unsupported outputs passes in CI with a fake provider.

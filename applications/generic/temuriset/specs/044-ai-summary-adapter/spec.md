# Feature Specification: AI brief summary adapter (gated)

**Feature Branch**: `044-ai-summary-adapter`
**Created**: 2026-11-05
**Status**: Planned. Synthetic readiness can use the existing 022 port. Real-provider integration and activation remain gated.
**Milestone**: M12 Gated adapters
**Depends on**: 022
**Size**: M
**Covers**: FR12, AC35, AC68
**Flips**: manifest adapter `ai-summary` → `available`; web registry `ringkasan-otomatis` → `available`

**Entry condition**: an approved model provider with processing terms that permit the supplied facts, and a reviewed evaluation set. Provider approval, processing terms and independent evaluation review are pending. Spec 022 already supplies the summary endpoint and default-off journey.

## User Scenarios & Testing

### User Story 1 - Shorter brief, no new claims (Priority: P1)

**Independent Test**: Use a fake provider to select an authorized subset of supplied facts. Exercise altered claims, expired access and provider timeout. Check that the deterministic brief remains editable.

**Acceptance Scenarios**:

1. **Given** supplied facts, **When** a summary is requested, **Then** each returned sentence is an exact supplied sentence with its original references. An invalid selection is refused and the template brief stays (AC35).
2. **Given** the provider is down, **When** requested, **Then** "Ringkasan otomatis tidak tersedia" shows and the template brief remains editable (AC68).
3. **Given** retrieved text containing instructions, **When** summarized, **Then** it is treated as data and never changes behaviour.

## Requirements

### Functional Requirements

- **FR-001**: Model input MUST contain only facts authorized when each attempt starts. An eligible transient failure permits at most one controlled retry before the deterministic fallback. Live access MUST be checked again before returning selected facts.
- **FR-002**: Model identity, model version and prompt template version MUST accompany each accepted output and come from trusted adapter configuration.
- **FR-003**: The model MUST select a proper subset of server-supplied sentences by request-local identifier. The server MUST reject additional text and unknown or repeated identifiers and preserve the original text, order and references.
- **FR-004**: The approved provider and reviewed evaluation set MUST be evidenced before external use. Manual brief editing MUST remain available while off, unavailable or refused.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An evaluation set of supported and unsupported outputs passes in CI with a fake provider.

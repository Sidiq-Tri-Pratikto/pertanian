# Feature Specification: Live meter adapter

**Feature Branch**: `046-live-adapter`
**Created**: 2026-10-30
**Status**: Seeded, gated
**Milestone**: M11 Gated
**Depends on**: 039
**Size**: L
**Covers**: FR-04, FR-05, AT-42
**Flips**: manifest adapter for the verified model only

**Entry condition**: a chosen meter model, a real device, a reference meter, and an appropriate installation. Fixed wiring needs a qualified installer.

## User Scenarios & Testing

### User Story 1 - One verified model (Priority: P1)

**Why this priority**: G5: "Terhubung" only after authenticated enrollment and a valid first reading.

**Independent Test**: Enroll the real device.

**Acceptance Scenarios**:

1. **Given** the device, **When** enrolled, **Then** identity is verified server-side, the first reading is valid, and only then does the status change.
2. **Given** the reference meter, **When** compared, **Then** results are recorded per installation, and accuracy is not claimed beyond them.
3. **Given** the stream stops, **When** past two intervals, **Then** the source is stale and never "off".

### Edge Cases

- No relay or switching route exists, even when the hardware has one.
- Phase total and components are declared and never added.
- Vendor credentials never reach the app.

## Requirements

### Functional Requirements

- **FR-001**: Ingestion MUST go through `IngestService`.
- **FR-002**: Credentials MUST be measurement-scoped where supported.
- **FR-003**: Transport MUST use TLS with per-source identity.

### Key Entities

- **SourceCredential**, **Enrollment**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A reference comparison is recorded for at least one installation.
- **SC-002**: The FR-20 route test still passes.

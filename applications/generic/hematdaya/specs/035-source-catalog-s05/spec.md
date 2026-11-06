# Feature Specification: Source catalog and simulated setup

**Feature Branch**: `035-source-catalog-s05`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M8 Recovery
**Depends on**: 005, 013, 027
**Size**: M
**Covers**: FR-04, AT-42, S05, P07
**Flips**: registry `sumber-meter` → `available`

## User Scenarios & Testing

### User Story 1 - See what is real (Priority: P1)

**Why this priority**: Candidates must stay labelled planned until verified (PRD §6.3).

**Independent Test**: Open the catalog.

**Acceptance Scenarios**:

1. **Given** the catalog, **When** opened, **Then** CSV appears available only if the adapter and import screen are available. The simulated source is labelled simulated, and Shelly and TP-Link show "Direncanakan".
2. **Given** a planned provider, **When** chosen, **Then** "Integrasi belum tersedia pada prototipe ini" shows, with a return to the catalog or to CSV when available, and the draft stays.

### User Story 2 - Simulated setup end to end (Priority: P2)

**Why this priority**: It rehearses enrollment and binding without a device.

**Independent Test**: Complete setup twice with one operation key.

**Acceptance Scenarios**:

1. **Given** the simulated path, **When** completed, **Then** a first reading is recorded, status stays "Simulasi koneksi", and no unqualified "Terhubung" appears.
2. **Given** the response to confirmation is lost, **When** the same operation and payload are retried, **Then** the service returns the first result without creating a second asset, binding, or reading.
3. **Given** an expired unconfirmed enrollment, **When** confirmation is attempted, **Then** the service rejects it and creates no data.
4. **Given** an existing asset, **When** bound, **Then** the source starts at its effective time and old readings stay.

### Edge Cases

- No credentials are requested.
- No rewiring instructions appear.
- A new asset's overlap with others stays unknown until confirmed.

## Requirements

### Functional Requirements

- **FR-001**: `GET /device-catalog` MUST report status, measurement kind, cadence and channel scope.
- **FR-002**: Enrollment MUST expire while pending, verify the simulated source identity on the server, and require a valid first reading. Confirmation MUST be single-use, atomic, and replay-safe.
- **FR-003**: Steps MUST retain drafts; back moves one step.

### Key Entities

- **CatalogEntry**, **Enrollment**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A UI scan finds no unqualified "Terhubung".
- **SC-002**: Retry creates exactly one asset, binding and reading.

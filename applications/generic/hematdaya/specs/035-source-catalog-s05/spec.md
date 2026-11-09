# Feature Specification: Source catalog

**Feature Branch**: `035-source-catalog-s05`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M8 Recovery
**Depends on**: 005, 013, 027
**Size**: S
**Covers**: FR-04, AT-42, S05, P07
**Flips**: registry `sumber-meter` → `available` for the catalog

## User Scenarios & Testing

### User Story 1 - Find a compatible meter (Priority: P1)

**Independent Test**: From Welcome, empty Beranda or Perangkat, open **Hubungkan alat ukur** / **Connect a meter**.

1. The catalog lists the selected lab model, Shelly Plug PM Gen3, and clearly shows whether setup is available in this environment. Unverified models stay planned or unsupported. Opening a catalog entry cannot create a workspace or claim a connection.
2. When setup is unavailable, explain the status and let the user return or choose historical CSV import when available.
3. Beranda and Perangkat keep the existing historical CSV path discoverable as a secondary action. The catalog and its status copy work in Indonesian and English.

## Requirements

- **FR-001**: `GET /api/v1/device-catalog` MUST report model, availability, measurement kind, cadence and channel scope where known.
- **FR-002**: The catalog MUST be read-only. Enrollment belongs to 046. A catalog entry marked available MUST describe access to the lab setup separately from verified support for release.

## Success Criteria

- **SC-001**: The catalog and unavailable-state recovery are reachable without creating a workspace or starting import.
- **SC-002**: A catalog-only deployment displays no connection or enrollment success.

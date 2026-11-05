# Feature Specification: Labelled demo accounts and fixtures

**Feature Branch**: `021-demo-fixtures`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M5 Discovery and matching
**Depends on**: 010, 019
**Size**: M
**Covers**: AC03
**Flips**: web registry `data-demo` → `available`

## User Scenarios & Testing

### User Story 1 - A visibly labelled demo of the whole product (Priority: P1)

In the demo composition, a visitor can enter labelled demo accounts (Rani, Bima, Dewi, Galih, Sinta, Peserta P, Investor B, and the other recipients) with fixtures F01–F06 and Recipients A–E, and reset them.

**Why this priority**: The PRD allows closed demonstrations with labelled accounts; reviewers need to walk journeys without real data.

**Independent Test**: `make demo-seed` then sign in as Rani from the demo picker.

**Acceptance Scenarios**:

1. **Given** `DEMO_MODE=true`, **When** the start screen loads, **Then** a demo panel lists demo accounts labelled "Akun demo · data fiktif".
2. **Given** a demo account saves an item or views an invention, **When** activity metrics are computed, **Then** demo events are excluded (AC03).
3. **Given** "Atur ulang demo", **When** confirmed, **Then** only demo-namespace rows are deleted and recreated; real accounts are untouched.
4. **Given** production, **When** `DEMO_MODE=true` is set, **Then** startup refuses it unless the deployment is marked as a demo deployment.

### Edge Cases

- Demo accounts never receive email; sign-in is the demo picker only.
- A demo workspace may carry a virtual clock starting 2 November 2026 08:00 UTC, with presets from the prototype; security uses the wall clock.
- Every demo screen shows "Demo · Data fiktif" in the bar.

## Requirements

### Functional Requirements

- **FR-001**: Seeding MUST go through the domain services, not raw SQL, so fixtures obey the same rules.
- **FR-002**: Demo rows MUST be tagged so reset and metric exclusion are exact.
- **FR-003**: F01-GAP, F01-SCAN and the proposed-entity variant MUST be selectable states.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Reset twice in a row yields identical fixture ids and versions; matching goldens hold on seeded data.

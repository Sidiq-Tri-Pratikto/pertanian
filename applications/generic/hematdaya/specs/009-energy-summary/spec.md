# Feature Specification: Energy summary

**Feature Branch**: `009-energy-summary`
**Created**: 2026-10-30
**Status**: Implemented on `f/m1-energy-core`; Postgres integration tests and golden files `contracts/golden/summary-*.json` pass. A four-week summary over 2,688 rows took 0.25 s locally
**Milestone**: M1 Energy core
**Depends on**: 008
**Size**: L
**Covers**: FR-07, FR-09, AT-05, AT-06, AT-21, AT-36
**Flips**: none (`core` flips at 021)

## User Scenarios & Testing

### User Story 1 - Exact energy for a period and scope (Priority: P1)

**Why this priority**: This answers the product's first question: how much energy was recorded in this period?

**Independent Test**: Golden responses for the H and I fixtures.

**Acceptance Scenarios**:

1. **Given** `h-base` and 19–25 Oktober, **When** the summary is read, **Then** energy is `14.700` kWh, coverage is complete, and Kulkas is `8.400` kWh, the largest of four.
2. **Given** `i-base` and the same week, **When** read, **Then** energy is `144.000` kWh and Oven `72.000` kWh.
3. **Given** `i-base` and Sunday 25 Oktober, **When** read, **Then** energy is `0.000` kWh with full coverage: measured zero, not missing.
4. **Given** `h-base` and today on virtual Monday 00.00, **When** read, **Then** energy is `null`, with reason `no_data`, not zero.
5. **Given** `h-current` at 21 Oktober 12.00, **When** today is read, **Then** energy is `0.870` kWh and later rows are excluded.

### User Story 2 - Refuse a sum that would double count (Priority: P1)

**Why this priority**: PRD §5.2 forbids showing 11 for a 10 parent and 1 child, and that refusal must ship with the first total.

**Independent Test**: Scope scenario summary.

**Acceptance Scenarios**:

1. **Given** Meter utama contains Kulkas and both are selected, **When** the summary is read, **Then** total is `null`, reason `scope_conflict`, and individual values remain.
2. **Given** Meter utama is requested through the single-asset summary, **When** read, **Then** the total is its own value. The user can persist a parent-only site selection from 028.
3. **Given** Kulkas has two unresolved sources, **When** read, **Then** its value is withheld and each source's value is listed: never their sum.
4. **Given** unknown overlap between two selected assets, **When** read, **Then** the combined total is refused.
5. **Given** two unrelated meters with no evidence of disjointness, **When** the default summary includes both candidates, **Then** individual values remain visible and the combined total and contribution percentages are withheld.

### User Story 3 - Honest completeness (Priority: P1)

**Why this priority**: Coverage must never be averaged away (PRD §11.3).

**Independent Test**: Learning-partial scenario.

**Acceptance Scenarios**:

1. **Given** Pompa Air lacks 24–25 Oktober, **When** read, **Then** per-asset coverage, gaps, minimum coverage and concurrent coverage are all returned.
2. **Given** a selected total of zero, **When** ranking is read, **Then** no percentage appears.

### Edge Cases

- An ordinary interval may be allocated across a period or binding boundary only as a visible uniform-within-interval estimate. Use the same deterministic allocation in all queries so parts sum exactly to the source value. If the resolution does not support the split, disclose the gap instead.
- A long valid counter delta can support its whole-span total. It cannot produce a number or measured time coverage for a narrower subperiod.
- Half-open windows from the site's local calendar; weeks start Monday.
- A full interval ending exactly at now is included.

## Requirements

### Functional Requirements

- **FR-001**: The API MUST return selected window (UTC and local), timezone, included and excluded assets with reasons, energy, coverage, gaps, latest measurement, origins and revision.
- **FR-002**: Energy MUST be a decimal string; unavailable MUST be `null` with a reason.
- **FR-003**: Until 028, the default candidates MUST be all active assets. A combined total MUST require a single asset or demonstrably disjoint loads. Seeded H/I fixtures carry known disjointness. Never infer it from a missing relation or an unrelated source ID.
- **FR-004**: Contribution percentages MUST be computed by the service and omitted for a zero total.
- **FR-005**: Queries MUST use the site clock.
- **FR-006**: A requested local-date range MUST be capped at 366 days before querying data.

### Key Entities

- **Summary**: window, scope, per-asset rows, combined quality, availability reasons.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Golden JSON for H and I passes byte for byte in CI.
- **SC-002**: Every energy oracle in PRD §19 that needs no tariff, schedule or output passes.

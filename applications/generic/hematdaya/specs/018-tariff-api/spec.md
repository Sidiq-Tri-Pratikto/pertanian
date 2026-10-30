# Feature Specification: Tariff and cost API

**Feature Branch**: `018-tariff-api`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M3 Settings and cost
**Depends on**: 011
**Size**: M
**Covers**: FR-08, AT-07, AT-08, AT-09
**Flips**: manifest capability `cost` → `available`

## User Scenarios & Testing

### User Story 1 - Qualified cost from a tariff (Priority: P1)

**Why this priority**: Cost is the most meaningful number for many users, and the easiest to overclaim.

**Independent Test**: Fixture oracles.

**Acceptance Scenarios**:

1. **Given** `h-base` with synthetic Rp1.500/kWh, **When** the week is read, **Then** cost is `22050` with covered energy `14.700` and synthetic provenance.
2. **Given** `i-base`, **When** read, **Then** day `36000`, week `216000`, four weeks `864000`.
3. **Given** the household change variant, **When** read, **Then** `24150`; the industrial variant, `220500`.

### User Story 2 - Unknown is not free (Priority: P1)

**Why this priority**: AT-07 and AT-08.

**Independent Test**: No tariff versus explicit zero.

**Acceptance Scenarios**:

1. **Given** no tariff, **When** read, **Then** cost is `null` with `missing_tariff`, and energy is unaffected.
2. **Given** an explicit zero tariff, **When** read, **Then** cost is `0` with its provenance.

### User Story 3 - Effective dates (Priority: P1)

**Why this priority**: AT-09: 1 kWh at Rp1.000 then 1 kWh at Rp2.000 is Rp3.000, not Rp4.000.

**Independent Test**: Split oracle.

**Acceptance Scenarios**:

1. **Given** two tariffs, **When** a period spans them, **Then** each interval uses its own rate.
2. **Given** an interval crossing a tariff boundary, **When** computed, **Then** it splits by overlap under a stated uniform assumption and is flagged.
3. **Given** a gap in tariff history, **When** computed, **Then** cost is incomplete with covered energy stated, never a zero-price interval.
4. **Given** a new tariff effective now, **When** saved, **Then** old costs do not change; a confirmed retroactive correction recomputes and is audited.

### Edge Cases

- Negative or non-finite tariffs are refused.
- Cost never comes from a rounded displayed kWh.
- A scope conflict gives `scope_conflict`, not a cost.

## Requirements

### Functional Requirements

- **FR-001**: Tariffs MUST be effective-dated, non-negative, per-site, with provenance.
- **FR-002**: Cost MUST use integer arithmetic and round once.
- **FR-003**: Summaries MUST state availability, covered energy and tariff provenance.
- **FR-004**: Routes MUST use the capability guard.

### Key Entities

- **Tariff**: site, effective from, milli-rupiah per kWh, provenance.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All cost oracles in PRD §19 pass exactly.
- **SC-002**: `core-only` returns `capability_disabled` with identical energy.

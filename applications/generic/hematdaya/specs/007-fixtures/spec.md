# Feature Specification: Demo fixtures

**Feature Branch**: `007-fixtures`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M1 Energy core
**Depends on**: 006
**Size**: S
**Covers**: FR-17, AT-05, AT-06
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Exact, generated fixtures (Priority: P1)

The household and industrial fixtures come from one deterministic generator with exact oracles.

**Why this priority**: PRD §19 fixes these numbers. They are the proof that the whole calculation path is right.

**Independent Test**: Generate each fixture and assert row counts and hourly values.

**Acceptance Scenarios**:

1. **Given** fixture H, **When** generated, **Then** it has 2,688 rows, four disjoint assets, integer Wh, explicit zeros, Asia/Jakarta, range 2026-09-28 00.00 to 2026-10-26 00.00 exclusive.
2. **Given** fixture I, **When** generated, **Then** it has 2,688 rows, Sundays are explicit zeros, and output days match PRD §19.3.
3. **Given** the household change variant, **When** generated, **Then** TV has +200 Wh at 19.00 on the seven selected-week days only.
4. **Given** the industrial variant, **When** generated, **Then** Kompresor has +500 Wh at 18.00 on the six selected-week output days only.

### User Story 2 - Named scenarios (Priority: P1)

**Why this priority**: FR-17 requires repeatable states, including combinations.

**Independent Test**: Every scenario in the catalog builds without error.

**Acceptance Scenarios**:

1. **Given** the scenario catalog, **When** read, **Then** each entry has an ID, a readable Indonesian name and description, and a segment.
2. **Given** a scenario, **When** built twice, **Then** the output is identical.

### Edge Cases

- No AC appears in any fixture.
- Synthetic tariff Rp1.500/kWh is labelled as synthetic, never as a PLN rate.
- "Hari ini" on the virtual Monday is empty, which is correct.

## Requirements

### Functional Requirements

- **FR-001**: The generator MUST be pure and deterministic.
- **FR-002**: The catalog MUST include: household base, no tariff, change, current period, learning plus no tariff plus partial, valid zero, stale plus offline, historical plus offline, scope overlap, empty, industry base, optional, change, current period.
- **FR-003**: Fixtures MUST go through the same ingestion service as any other source.

### Key Entities

- **Scenario**: ID, name, description, segment, generator, virtual now, initial period, optional tariff, schedule, metric.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Hourly sums reproduce: H day 2.100, week 14.700, four weeks 58.800 kWh; I output day 24.000, week 144.000, four weeks 576.000 kWh.
- **SC-002**: Current-period oracles at 2026-10-21 12.00 reproduce: H 0.870 and 5.070 kWh; I 13.000 and 61.000 kWh.

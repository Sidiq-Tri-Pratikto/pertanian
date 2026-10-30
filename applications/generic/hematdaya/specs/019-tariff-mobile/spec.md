# Feature Specification: Tariff and cost on mobile

**Feature Branch**: `019-tariff-mobile`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M3 Settings and cost
**Depends on**: 017, 018
**Size**: S
**Covers**: FR-08, UX-06, AT-07, S09, S03
**Flips**: registry `estimasi-biaya` → `available`

## User Scenarios & Testing

### User Story 1 - See cost with its limits beside it (Priority: P1)

**Why this priority**: Monetary feedback depends on tariff credibility (PRD §14.1).

**Independent Test**: `h-base` Beranda.

**Acceptance Scenarios**:

1. **Given** synthetic tariff, **When** Beranda opens, **Then** "Estimasi biaya energi terpantau" shows Rp22.050, says the tariff is simulated, and says it is not a bill.
2. **Given** no tariff, **When** Beranda opens, **Then** "Biaya belum dihitung · tarif belum diatur" shows with an optional action, and energy stays.
3. **Given** Detail biaya, **When** opened, **Then** tariff, effective dates, covered energy and bill limitation show.

### User Story 2 - Set a tariff (Priority: P2)

**Why this priority**: Optional, but the path from missing to known must work.

**Independent Test**: Enter 1.444,70 and save.

**Acceptance Scenarios**:

1. **Given** the tariff field, **When** a decimal comma value is entered and saved, **Then** cost updates after acknowledgment.
2. **Given** an empty field, **When** saved, **Then** tariff stays absent, not zero.
3. **Given** core-only, **When** settings open, **Then** the section explains the module is off.

### Edge Cases

- `1.5` asks for a comma and is not guessed.
- Explicit `0` shows Rp0 with its source.

## Requirements

### Functional Requirements

- **FR-001**: `HDCostEstimate` MUST take service strings and multiply nothing.
- **FR-002**: `HDNumericField` MUST keep raw text and never turn empty into 0.

### Key Entities

Tariff and cost from 018.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Displayed cost equals the API value in every scenario.

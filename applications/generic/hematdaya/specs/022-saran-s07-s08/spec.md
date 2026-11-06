# Feature Specification: Saran and evidence screens

**Feature Branch**: `022-saran-s07-s08`
**Created**: 2026-10-30
**Status**: Implemented on `f/022-023-saran-feedback`; Jest tests use responses recorded from the 021 service (`h-change`, `h-base`, `h-learning-partial`); web checked against the live API; Android not run
**Milestone**: M4 Evidence
**Depends on**: 013, 021
**Size**: M
**Covers**: FR-13, UX-04, AT-01, AT-02, S07, S08, P04
**Flips**: registry `saran` → `available`

## User Scenarios & Testing

### User Story 1 - Understand one observation (Priority: P1)

**Why this priority**: P04: identify the observed value, comparison, quality and unknown cause.

**Independent Test**: `h-change` from Beranda to evidence in one tap.

**Acceptance Scenarios**:

1. **Given** `h-change`, **When** Beranda opens, **Then** the featured observation reads "TV naik 1,400 kWh (+55,56%)" with Lihat dasar saran.
2. **Given** evidence, **When** opened, **Then** it reads in order: observed, comparison, quality and scope, unknown, inspection step.
3. **Given** Detail perhitungan, **When** opened, **Then** resolution, threshold, policy version and arithmetic show.
4. **Given** Lihat data pembanding, **When** opened, **Then** the aligned chart and table show the same current/reference numbers from the selected evidence revision and its common mask.
5. **Given** a newer evidence revision arrives after a card is shown, **When** the user opens that card, **Then** the original revision remains visible and is marked superseded where applicable.

### User Story 2 - The list stays honest (Priority: P1)

**Why this priority**: S07 separates notices from observations and never invents alarms.

**Independent Test**: Base, learning and partial scenarios.

**Acceptance Scenarios**:

1. **Given** `h-base`, **When** Saran opens, **Then** "Belum ada perubahan yang memenuhi kriteria pada periode ini" shows and says it is not an efficiency or safety verdict.
2. **Given** learning, **When** Saran opens, **Then** "Belum cukup periode pembanding" shows with a link to history.
3. **Given** partial data, **When** Saran opens, **Then** data notices sit apart from observations.

### Edge Cases

- Saran umum is labelled and never reads as analysis of this site.
- Back preserves period and list position.
- A household demo finishes this journey with no AC, schedule or output (AT-01); so does industry (AT-02).

## Requirements

### Functional Requirements

- **FR-001**: The screens MUST render evidence strings from the service.
- **FR-002**: There MUST be no "Terapkan", shutdown action or diagnosis.
- **FR-003**: Each item MUST name asset, statement, period and qualification.
- **FR-004**: A featured or listed observation MUST link with its insight ID and exact evidence revision. The evidence view, calculation detail, chart and table MUST use that revision's frozen snapshot.

### Key Entities

Insight and notice from 021.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Evidence is reachable in one tap from a populated Beranda.
- **SC-002**: AT-01 and AT-02 are evidenced on web and Android for read paths and feedback after 023.

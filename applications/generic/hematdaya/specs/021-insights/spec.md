# Feature Specification: Insights and evidence

**Feature Branch**: `021-insights`
**Created**: 2026-10-30
**Status**: Implemented on `f/m4-evidence`; AT-17 numbers, revision, retirement, concurrency, notice and copy-lint tests pass. The manifest `core` capability is now `available`
**Milestone**: M4 Evidence
**Depends on**: 020
**Size**: L
**Covers**: FR-13, FR-19, AT-11, AT-17
**Flips**: manifest capability `core` → `available`

## User Scenarios & Testing

### User Story 1 - One rule for small and large loads (Priority: P1)

**Why this priority**: PRD §12.2 rejects a fixed 3 kWh threshold, and AT-17 proves a small household change qualifies.

**Independent Test**: H change variant.

**Acceptance Scenarios**:

1. **Given** `h-change`, **When** evaluated, **Then** one observation: TV 3,920 vs 2,520 kWh, +1,400 kWh, +55,56%, r = 0,168, threshold 0,840.
2. **Given** `h-base`, **When** evaluated, **Then** no observation.
3. **Given** `i-change` without schedule, **When** energy is evaluated, **Then** Kompresor +3,000 kWh does not qualify, because 30% of 36 kWh is 10,8 kWh.

### User Story 2 - Evidence that cannot be rewritten (Priority: P1)

**Why this priority**: FR-13, FR-19: an insight keeps its snapshot, and feedback never silently moves.

**Independent Test**: Change data; the old revision stays readable.

**Acceptance Scenarios**:

1. **Given** an observation, **When** read, **Then** its revision carries asset and scope, period, observed value, historical values, median, change, percent or why not, per-window coverage, common mask and aligned current/reference series, origin, resolution, policy version, generated time and "Yang belum diketahui".
2. **Given** corrected data changes the numbers, **When** re-evaluated, **Then** a new revision exists, the old one is marked superseded, and it stays readable.
3. **Given** the same inputs evaluated twice, **When** compared, **Then** no new revision appears.
4. **Given** a committed import or correction makes an observation ineligible, **When** the period is next read, **Then** the old observation no longer appears as active, and its original revision remains readable as superseded.
5. **Given** concurrent reads of the same changed inputs, **When** they evaluate the observation, **Then** exactly one new revision becomes current, or the active observation is retired once if it no longer qualifies.

### User Story 3 - Advice stays advice (Priority: P1)

**Why this priority**: PRD §2 and §12.1.

**Independent Test**: Scan generated copy.

**Acceptance Scenarios**:

1. **Given** a continuous expected asset, **When** usage changes, **Then** an observation may appear, and it never recommends interruption (AT-11).
2. **Given** any insight, **When** its copy is read, **Then** it has no diagnosis, waste claim, savings claim or instruction to switch anything off.

### Edge Cases

- Blocking data-quality notices rank separately from observations.
- Observations rank by additional kWh, then recency, then stable ID.
- A decrease is described with the same gates, never as verified savings.
- No alert is invented to fill the list.

## Requirements

### Functional Requirements

- **FR-001**: An increase MUST qualify only if `C − B > 0` and `C − B >= max(0.30 × B, 3 × MAD, 5 × r)`.
- **FR-002**: Unknown resolution MUST suppress automatic alerts.
- **FR-003**: Evidence MUST be stored as an immutable revision with policy ID and version.
- **FR-004**: Copy MUST be built from the snapshot, never free text generation.
- **FR-005**: Notices MUST cover partial coverage, stale source and scope conflict.
- **FR-006**: Writes that change inputs MUST invalidate affected insight identities or periods in the same transaction. Current insight reads MUST re-evaluate that state before returning active results, then atomically replace or retire revisions without deleting old evidence or feedback.

### Key Entities

- **Insight**, **InsightRevision**. See `docs/roadmap/architecture.md`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AT-17 exact numbers pass, and `h-base` and `i-base` produce zero observations.
- **SC-002**: A copy lint test rejects forbidden words across all generated strings.

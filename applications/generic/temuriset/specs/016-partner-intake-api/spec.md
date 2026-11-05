# Feature Specification: Partner profiles, opportunities and typed requirements

**Feature Branch**: `016-partner-intake-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M4 Partner intake
**Depends on**: 007
**Size**: L
**Covers**: FR08, FR09, AC22, AC23, AC24, AC25
**Flips**: none

## User Scenarios & Testing

### User Story 1 - A partner states its mandate honestly (Priority: P1)

A personal or organization party publishes a partner profile (subtype, sectors, stages, regions, support forms, check or support range, review expectations, contact route, intake status) and one or more versioned opportunities with typed requirements.

**Why this priority**: FR08–FR09; matching evaluates opportunity versions.

**Independent Test**: Recipients A–E from the fixtures.

**Acceptance Scenarios**:

1. **Given** Investor B as a personal party, **When** a profile with equity checks USD 50000–150000 is saved, **Then** no organization is required.
2. **Given** a source-reported directory profile with unconfirmed intake, **When** read, **Then** it is labelled "Dilaporkan sumber" and "Ketersediaan belum dikonfirmasi", and no active intake is claimed (AC22).
3. **Given** a partner closes direct intake, **When** a general direct pitch is attempted, **Then** it is unavailable, while specific active opportunities are still evaluated separately (AC23).
4. **Given** a contact route `EXTERNAL`, **When** a user follows it, **Then** the API records an external handoff event that is never a submitted pitch (AC24).
5. **Given** Mitra A publishes A1, A2 and A3, **When** they are read, **Then** each has its own version, intake and requirements, and nothing merges across them (AC25).

### User Story 2 - Requirements are typed and visible (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a requirement with operator outside `equals`, `in_set`, `intersects`, `minimum`, `maximum`, `range_overlap`, `exists`, `manual_review`, **When** saved, **Then** it is refused.
2. **Given** a narrative requirement without a mapping, **When** saved, **Then** it is stored as `manual_review` and never auto-rejects.
3. **Given** an applicant, **When** reading an active opportunity, **Then** every requirement that may block submission is visible with its reason, stage and verification mode.

### Edge Cases

- States: `DRAFT` → `ACTIVE` ↔ `PAUSED` → `CLOSED`, `EXPIRED` at `closes_at` via a worker job and lazy check.
- An edit to an active opportunity creates a new version; pitches keep the version they targeted.
- No assets under management, credentials or capacity are invented; unknown stays unknown.

## Requirements

### Functional Requirements

- **FR-001**: Profiles MUST distinguish general thesis from current availability, and owner-confirmed from source-reported.
- **FR-002**: Opportunities MUST be versioned with outcome, included and excluded scope, support, accepted stages, relationship forms, timing, financial basis and requirements.
- **FR-003**: Requirements MUST carry field, operator, value, mandatory flag, applies-at stage, verification mode, reason, visibility and version.
- **FR-004**: A general-intake opportunity MUST be labelled "berdasarkan profil umum mitra" and usable only when direct intake is open.

### Key Entities

- **PartnerProfile**, **Opportunity**, **OpportunityVersion**, **Requirement**, **ExternalHandoff**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC22–AC25 pass; Recipients A–E load as test factories used again by 019 and 021.

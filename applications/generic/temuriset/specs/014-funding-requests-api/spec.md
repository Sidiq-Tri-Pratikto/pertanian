# Feature Specification: Company funding requests

**Feature Branch**: `014-funding-requests-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M3 Needs and funding
**Depends on**: 009
**Size**: M
**Covers**: FR07, AC19, AC67
**Flips**: manifest capability `company_funding` → `available` once its routes ship behind the guard

## User Scenarios & Testing

### User Story 1 - One raise, several inventions (Priority: P1)

A company records one funding request with a total target and a desired contribution per investor, linked to several invention versions, without becoming several raises.

**Why this priority**: FR07 and journey J02.

**Independent Test**: FRaise01 with F04 and F05.

**Acceptance Scenarios**:

1. **Given** Demo Circular Materials Ltd with an identified legal entity, **When** FRaise01 is saved with target USD 500000, desired contribution USD 50000–100000, partial and syndicated funding accepted, and links to F04 and F05 versions, **Then** one request with two links exists and the target is stored once (AC19).
2. **Given** a proposed company, **When** the request uses `PROPOSED_ENTITY`, **Then** it carries the label "Perusahaan belum didirikan" and no legal entity.
3. **Given** a change of target, **When** saved, **Then** a new version is created and a sent snapshot keeps the old target.
4. **Given** `project-support-only`, **When** any funding mutation is called, **Then** it is refused with `CAPABILITY_UNAVAILABLE`, project support still works, and existing funding records stay readable to their owners (AC67).

### Edge Cases

- Company financing stage and each invention's maturity are separate fields.
- No valuation, share count or percentage is accepted or derived.
- A link to an archived invention version is refused.

## Requirements

### Functional Requirements

- **FR-001**: A funding request MUST own its target; links MUST NOT copy amounts into inventions.
- **FR-002**: `EXISTING_ENTITY` MUST reference a legal entity; `PROPOSED_ENTITY` MUST NOT.
- **FR-003**: Legal entities MUST store name, jurisdiction, registration reference and review status; a declared entity is labelled as declared.
- **FR-004**: Every funding route MUST use `require_capability("company_funding")`.

### Key Entities

- **FundingRequest**, **FundingInventionLink**, **LegalEntity**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC19 and AC67 pass in all three compositions.

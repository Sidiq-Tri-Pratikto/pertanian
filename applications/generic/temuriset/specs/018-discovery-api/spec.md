# Feature Specification: Discovery, search and saved lists

**Feature Branch**: `018-discovery-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M5 Discovery and matching
**Depends on**: 013, 014, 016
**Size**: L
**Covers**: FR10, AC28, AC29, AC30
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Partners browse inventions and funding requests; inventors browse partners (Priority: P1)

Separate result types: published inventions, active funding requests (one card per raise), and partner profiles with their active opportunities. Results come from a public projection only.

**Why this priority**: FR10; investor discovery is a primary task.

**Independent Test**: Search the F01–F06 and A–E factories through the API.

**Acceptance Scenarios**:

1. **Given** a new partner with no history, **When** discovery opens, **Then** sections "Sesuai profil Anda" (from explicit preferences), "Baru diterbitkan" and "Pilihan kurator" return results with no trend label (AC28).
2. **Given** filters that match nothing, **When** searched, **Then** the response is empty with the active filters echoed and a suggested deliberate relaxation, and hard requirements are never broadened silently (AC29).
3. **Given** the owner refreshes its own invention 50 times, **When** activity is counted, **Then** no trend increments, and no trend label exists in R1 (AC30).
4. **Given** "water filter", **When** searched in English, **Then** ClearSpring is found through the alias table, as with "filter air".
5. **Given** FRaise01 with two inventions, **When** funding results are listed, **Then** it appears once.

### User Story 2 - Save and say "kurang relevan" privately (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a saved item, **When** the list is filtered to saved, **Then** it appears for that party only.
2. **Given** "Kurang relevan", **When** pressed, **Then** the item leaves that party's results and nothing public changes.

### Edge Cases

- Archiving, unpublishing or closing intake removes the projection row through the outbox consumer.
- Private facts, documents and drafts never enter `search_documents`.
- Results are paginated with an opaque cursor; at most 100 per page.

## Requirements

### Functional Requirements

- **FR-001**: `search_documents` MUST hold only published fields, maintained by outbox consumers.
- **FR-002**: Search MUST use Postgres full-text (`simple`) plus `pg_trgm`, with an Indonesian–English alias table.
- **FR-003**: Filters MUST include sector, stage, purpose, support form, region, intake status and comparable financial range.
- **FR-004**: Saved items and relevance feedback MUST affect only the acting party's lists.
- **FR-005**: Curated selection MUST be an explicit flag set by an operator, never computed from activity.

### Key Entities

- **SearchDocument**, **SavedItem**, **RelevanceFeedback**, **AliasTerm**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC28–AC30 pass; the isolation harness proves a private fact string is unsearchable.

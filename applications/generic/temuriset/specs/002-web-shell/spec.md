# Feature Specification: Web shell

**Feature Branch**: `002-web-shell`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M0 Foundations
**Depends on**: 001
**Size**: M
**Covers**: FR01, S01, S02, UX-24
**Flips**: none; every registry entry starts as `coming_soon`

## User Scenarios & Testing

### User Story 1 - Choose how to use TemuRiset with nothing set up (Priority: P1)

A visitor reads what TemuRiset does, picks Inovator or Investor/Mitra, and reaches that persona's navigation with no account, company or institution.

**Why this priority**: PRD section 3 forbids a fictitious institution, and the persona drives navigation from the first screen.

**Independent Test**: Open `/`, choose a persona, arrive at its first destination.

**Acceptance Scenarios**:

1. **Given** a first visit, **When** `/` opens, **Then** it redirects to `/start`, which offers exactly two choices and no text field.
2. **Given** Inovator is chosen, **When** the form is submitted, **Then** Beranda opens with Beranda, Inovasi Saya, Temukan Investor/Mitra, Pitching dan Diskusi and Profil.
3. **Given** Investor/Mitra is chosen, **When** the form is submitted, **Then** Jelajahi opens with Jelajahi, Kebutuhan/Mandat, Pitching Masuk, Diskusi dan Jadwal and Profil.
4. **Given** no choice, **When** the form is submitted, **Then** an alert asks for one and nothing is stored.
5. **Given** a persona was chosen, **When** Profil is opened, **Then** the view can be changed and the change is confirmed.

### User Story 2 - Honest empty product (Priority: P1)

Every destination says what exists today. Nothing shows a fake match, amount, score or count.

**Acceptance Scenarios**:

1. **Given** Beranda, **When** it renders, **Then** it shows "Belum ada yang perlu dikerjakan" with no number, chart or invented activity.
2. **Given** any destination, **When** it renders, **Then** its planned features are listed under "Segera hadir".

### User Story 3 - See what is coming (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a planned feature row, **When** "Lihat rencana" is pressed, **Then** a "Segera hadir" screen says what is planned and that no data is created or stored.
2. **Given** an unknown feature address, **When** it opens, **Then** the screen says so and links to every planned feature.
3. **Given** Profil, **When** it renders, **Then** "Rencana fitur" lists every planned feature.

### User Story 4 - Know whether the service answers (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a reachable API, **When** Beranda loads, **Then** it shows "Layanan tersedia" and the release, through the web origin's proxy.
2. **Given** an unreachable API, **When** Beranda loads, **Then** an Indonesian alert offers "Coba lagi" and every destination keeps working.
3. **Given** a non-retryable failure, **When** it shows, **Then** the service message and reference ID appear and no retry is offered.

### Edge Cases

- Below 48 rem the tab bar shows four destinations plus Lainnya; above it, the top navigation shows all five.
- Long Indonesian copy wraps at 320 px with no horizontal scroll.
- Spec numbers appear only in development builds.

## Requirements

### Functional Requirements

- **FR-001**: The persona MUST select navigation and copy only, never access, and live in an http-only cookie until 008.
- **FR-002**: Colours, spacing and type MUST come from the copied design-system stylesheets, checked for drift.
- **FR-003**: Every planned feature MUST exist in one registry, every S01–S18 screen MUST be covered by it, and every feature MUST link to an existing spec folder.
- **FR-004**: Browsers MUST call only the web origin; `/api/v1` and `/health` are forwarded to the API.
- **FR-005**: The binding to TemuRiset Design System 1.0.0-draft and its deviations MUST be recorded (UX-24).

## Success Criteria

### Measurable Outcomes

- **SC-001**: `make check` passes: ESLint with no warnings, TypeScript strict, Vitest above 80% line coverage.
- **SC-002**: `make build` produces a production build; every route is dynamic and server-rendered.
- **SC-003**: axe reports no violations in jsdom for start, Beranda, partner pitches, coming soon, unknown feature and Profil.

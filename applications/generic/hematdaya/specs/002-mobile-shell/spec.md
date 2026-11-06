# Feature Specification: Mobile shell

**Feature Branch**: `002-mobile-shell`
**Created**: 2026-10-30
**Status**: Built, awaiting review
**Milestone**: M0 Foundations
**Depends on**: 001
**Size**: M
**Covers**: UX-01, UX-02, UX-03, UX-07, UX-12, S01, S02
**Flips**: none; every registry entry starts as `coming_soon`

## User Scenarios & Testing

### User Story 1 - Open the app with nothing set up (Priority: P1)

A new user opens HematDaya, reads what it does, optionally picks a context, and reaches the three destinations with no account, hardware or setup.

**Why this priority**: PRD §7 forbids any prerequisite for the core journey.

**Independent Test**: Launch, press Mulai or Lewati, arrive at Beranda.

**Acceptance Scenarios**:

1. **Given** a fresh launch, **When** the welcome screen shows, **Then** it states the value in one sentence, says the app never switches equipment, and offers Mulai, Coba demo and Lewati with no form to complete.
2. **Given** Industri is chosen, **When** the user presses Mulai, **Then** Beranda shows industrial examples, and nothing else changes.
3. **Given** the user presses Lewati, **When** Beranda shows, **Then** examples are neutral.

### User Story 2 - Honest empty product (Priority: P1)

Every destination says what exists today. Nothing shows a fake number, axis or alarm.

**Why this priority**: The base must never look like a working monitor.

**Independent Test**: Visit each tab and check for absent figures.

**Acceptance Scenarios**:

1. **Given** Beranda with no data, **When** it renders, **Then** it shows "Belum ada data energi" with no kWh, no Rp and no chart.
2. **Given** Saran with no data, **When** it renders, **Then** it shows "Belum ada saran" and says this is not an efficiency verdict.

### User Story 3 - See what is coming (Priority: P1)

Every planned feature opens a "Segera hadir" screen, and Pengaturan lists them all.

**Why this priority**: The product owner asked for coming soon on every planned feature.

**Independent Test**: Open Pengaturan → Rencana fitur → any row.

**Acceptance Scenarios**:

1. **Given** Beranda, **When** the user presses Impor data, **Then** the Segera hadir screen opens inside the Beranda tab, and Kembali returns to Beranda.
2. **Given** a tab with a detail screen open, **When** the user visits another tab and returns, **Then** the detail screen is still there.
3. **Given** an unknown feature address, **When** it opens, **Then** the app says so and offers a way back.

### User Story 4 - Know whether the service answers (Priority: P2)

**Why this priority**: It proves the contract end to end and keeps the app honest when the service is down.

**Independent Test**: Stop the API and reload Beranda.

**Acceptance Scenarios**:

1. **Given** a reachable API returning a valid capability manifest, **When** Beranda loads, **Then** it shows "Layanan tersedia" and the release.
2. **Given** an unreachable API, **When** Beranda loads, **Then** it explains the failure in Indonesian, offers Coba lagi, and every tab keeps working.
3. **Given** a non-retryable failure, **When** it shows, **Then** the user sees its safe message and reference ID when provided. The retry action is unavailable.
4. **Given** a successful HTTP response with invalid JSON or an invalid manifest, **When** it is read, **Then** it shows the safe unavailable state without a release or raw payload.
5. **Given** repeated retryable failures, **When** the server provides a wait or maximum attempt count, **Then** Coba lagi honors both, including the initial request in the count. Network failures use a maximum of three total attempts.

### Edge Cases

- Tab bar stays at the bottom at every width, per the design system.
- Long Indonesian copy wraps at 320 px with no horizontal scroll.
- Spec numbers appear only in development builds.

## Requirements

### Functional Requirements

- **FR-001**: The app MUST have exactly three labelled primary destinations: Beranda, Perangkat, Saran.
- **FR-002**: The selected tab MUST be shown beyond colour.
- **FR-003**: All colours, spacing and type MUST come from the generated design tokens.
- **FR-004**: Every planned feature MUST exist in one registry, and every S01–S12 screen MUST be covered by it.
- **FR-005**: Every interactive control MUST be at least 48 × 48.
- **FR-006**: Context choice MUST change examples only.
- **FR-007**: The app MUST show no energy, cost or comparison value of any kind.

### Key Entities

- **Feature**: id, Indonesian title, summary, points, screen ids, spec ids, status.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `make check`, `make doctor` and `make export` pass.
- **SC-002**: Web build at 320, 390 and 1280 px shows no horizontal overflow, no target under 48 px, and text contrast of at least 4.5:1.
- **SC-003**: Keyboard: Tab reaches controls with a visible ring, Enter activates, focus lands on the new heading.

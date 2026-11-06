# Feature Specification: Browser checks in CI

**Feature Branch**: `003-browser-checks`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M0 Foundations
**Depends on**: 002
**Size**: M
**Covers**: UX-19, UX-20, UX-21, UX-23
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Every PR proves the real pages in a real browser (Priority: P1)

jsdom cannot see contrast, focus visibility, reflow or sticky-bar overlap. A Playwright suite runs against the production build and a live API on every web PR.

**Why this priority**: Accessibility and responsive claims need rendered evidence (PRD section 13), and later journey tests need a harness.

**Independent Test**: `make e2e` from the web app passes locally and in CI.

**Acceptance Scenarios**:

1. **Given** a production build served by `next start` and the API running, **When** the suite runs, **Then** every route renders with no console error and no failed request.
2. **Given** each route at 320, 360, 768 and 1280 CSS px, **When** measured, **Then** the document has no horizontal scroll.
3. **Given** root text at 200%, **When** each route is measured at 320 px, **Then** there is no horizontal scroll and the primary action is reachable.
4. **Given** axe in Chromium with all rules including colour contrast, **When** each route is checked, **Then** there are no violations.
5. **Given** keyboard only, **When** Tab moves through each route at 360 px, **Then** every focused element is visible and not covered by the tab bar, and the skip link moves focus to the main region.

### User Story 2 - The built output is checked separately from development (Priority: P2)

**Acceptance Scenarios**:

1. **Given** CI, **When** the suite runs, **Then** it targets `next build` plus `next start`, never `next dev`, and the report names the browser, viewport and build.

### Edge Cases

- A test that needs data skips with a stated reason until the spec that creates the data adds a fixture.
- The design system hides one of the two navigations at every width; axe runs per width so `landmark-unique` is checked for real.

## Requirements

### Functional Requirements

- **FR-001**: Playwright MUST run Chromium against the production build and a live API in CI.
- **FR-002**: An overflow audit (ported from the prototype's `walkHelpers.audit()`) MUST run on every route at 320, 360, 768 and 1280 px, plus 200% text at 320 px.
- **FR-003**: axe-core MUST run in the browser on every route, with contrast enabled.
- **FR-004**: A keyboard test MUST check focus visibility and the sticky tab bar at 360 px.
- **FR-005**: Each later web spec MUST add its routes and journey to this suite.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The suite runs in under five minutes in CI and uploads its HTML report as an artifact.
- **SC-002**: Breaking contrast in `app.css` or adding a fixed 400 px element makes the suite fail.

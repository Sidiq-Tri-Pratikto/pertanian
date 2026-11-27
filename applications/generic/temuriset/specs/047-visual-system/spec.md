# Feature Specification: Visual system 1.1 (revamp R1)

**Feature Branch**: `047-visual-system`
**Created**: 2026-11-27
**Status**: Built, awaiting review
**Milestone**: Post-M11 revamp, first of six (plan: R1 visual system, R2 discovery and decisions, R3 bilingual foundation, R4 public invention page, R5 public updates, R6 invention follow)
**Depends on**: 003
**Covers**: no PRD requirement changes; design system release 1.1.0-draft
**Size**: S–M
**Sources**: `reports/temuriset-invention-follow-handoff/`, `reports/TemuRiset five revamp proposals.md`, `reports/TemuRiset UI redesign directions.md` (pertanian root, untracked design work)

## Context

The revamp mockups keep TemuRiset's palette (teal `#0F766E` actions, `#115E59` links, `#F0FDFA` selected surfaces, white surfaces, slate text), which the design system already ships. What they add is a typeface with real weight contrast, a large page title, a logo, photo frames and compact list rows. The owner decided on 27 November 2026 to adjust the design system for these, and picked logo option B (two paths meeting at one node) from three drawn options.

## User Scenarios & Testing

### User Story 1 - One recognisable look on every screen (Priority: P1)

Every page, signed in or not, shows the TemuRiset mark and word at the start of the bar and one large page title, set in IBM Plex Sans.

**Acceptance Scenarios**:

1. **Given** any route, **When** it renders, **Then** the bar starts with the mark (decorative) and the word "TemuRiset", which is a link to `/`, and the page has exactly one `h1` in `tr-sys-type-display`.
2. **Given** the browser has no IBM Plex Sans, **When** a page loads, **Then** the self-hosted woff2 files load with `font-display: swap`; no request leaves the site.
3. **Given** 200% text at 320 CSS px, **When** any route renders, **Then** nothing scrolls sideways and the primary action stays reachable.

### User Story 2 - Patterns ready for the next revamps (Priority: P2)

The design system offers `tr-media` (owner-published photo, 4:3, `tr-sys-radius-media`), `tr-toolbar`, `tr-chips`/`tr-chip`, `tr-list`/`tr-listrow` (a selected row marks a real state with a teal edge on teal-50) and `tr-listdetail` (two columns from 64 rem). R2 and R4 use them; R1 only ships them.

## Requirements

- **FR-001**: `--font-sans` starts with "IBM Plex Sans"; system sans stays the fallback.
- **FR-002**: Three weights ship (400, 600, 700). `tr-ref-weight-medium` (500) is removed because no 500 file ships and browsers would fall back to 400; labels, buttons and tabs move to 600.
- **FR-003**: New `tr-sys-type-display` (`clamp(2rem, 1.5rem + 1.5vw, 2.5rem)`, 1.15, 700); `tr-sys-type-heading-lg` becomes 700.
- **FR-004**: `TR.Logo` and the `plus` icon glyph join the bundle; `Screen` uses the logo and a display title.
- **FR-005**: Fonts are IBM Plex Sans 2.0.0 Latin1 split woff2 files, unmodified, with `OFL.txt` and recorded SHA-256 hashes. `make design` copies them, and the drift test compares them byte for byte.
- **FR-006**: The web deviations D1, D2, D11 and D16 are folded into the design system and removed from `app.css`.
- **FR-007**: Colours are unchanged; `node tools/build.mjs` contrast pairs still pass.

## Out of scope

Discovery and decision layouts (R2), locale and English (R3), public page and photos (R4).

## Decisions

- Logo B over the mockup's "+" square, because "+" already means "add" in the product.
- Self-hosted woff2 in the design system package instead of `next/font/google` (needs the network at build) or `@fontsource` (an extra dependency that the plain-HTML workbench cannot use).

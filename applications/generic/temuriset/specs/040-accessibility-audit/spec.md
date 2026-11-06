# Feature Specification: Accessibility audit of assembled journeys

**Feature Branch**: `040-accessibility-audit`
**Created**: 2026-11-05
**Status**: Local Chromium checkpoints audited on the integrated synthetic build. Full staging, J04/J05, screen-reader verification and remaining scoped conditions are open.
**Milestone**: M11 Portability and operations
**Depends on**: 032, 035
**Size**: M
**Covers**: UX-19, UX-20, UX-21, UX-22
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Evidence for WCAG 2.2 AA, not a claim (Priority: P1)

**Acceptance Scenarios**:

1. **Given** J01–J05 on staging, **When** walked keyboard-only, **Then** every step is operable with visible, unobscured focus, and dialogs trap and return focus (UX-19).
2. **Given** each screen, **When** measured, **Then** text, control, icon, focus and state contrast meet the targets, and no information depends on colour alone (UX-20).
3. **Given** 200% browser zoom and 320 CSS px, **When** each journey runs, **Then** no content or primary action is lost (UX-21).
4. **Given** NVDA with Firefox and VoiceOver with Safari, **When** each journey runs, **Then** labels, errors, status announcements and reduced motion behave as specified (UX-22).

### Edge Cases

- Results are PASS, FAIL, NOT RUN or BLOCKED with surface and version. Local production-build checks and actual staging checks have separate rows. A missing journey or assistive-technology pairing is recorded with its gating reason.

## Requirements

### Functional Requirements

- **FR-001**: The audit MUST record each check with browser, assistive technology, viewport, zoom and build.
- **FR-002**: Each FAIL MUST be linked to a fix with retest evidence or a reproducible issue. If no issue can be filed during the audit, retain the prepared issue details and keep disposition open.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `docs/roadmap/accessibility-audit.md` lists every UX-19 to UX-22 check with evidence.

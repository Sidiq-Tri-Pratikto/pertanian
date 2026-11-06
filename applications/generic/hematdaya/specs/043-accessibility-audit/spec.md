# Feature Specification: Accessibility and platform audit

**Feature Branch**: `043-accessibility-audit`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M10 Platforms and usability
**Depends on**: 042
**Size**: M
**Covers**: UX-07, UX-08, UX-09, UX-10, UX-14, AT-45, AT-46
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Works with assistive technology (Priority: P1)

**Why this priority**: Browser checks cannot pass native requirements (handoff §12).

**Independent Test**: Run core tasks with TalkBack and VoiceOver.

**Acceptance Scenarios**:

1. **Given** TalkBack and VoiceOver, **When** core tasks run, **Then** every control has an Indonesian name, role and state, and status changes are announced.
2. **Given** OS text at 200%, **When** used, **Then** nothing is lost and long names wrap.

### User Story 2 - Works on the web (Priority: P1)

**Why this priority**: AT-46.

**Independent Test**: Keyboard-only tasks.

**Acceptance Scenarios**:

1. **Given** keyboard only, **When** core tasks run, **Then** focus is visible, logical and never trapped; Escape closes sheets and focus returns.
2. **Given** 320 px and 400% zoom at 1280, **When** used, **Then** content reflows with no horizontal scroll.

### Edge Cases

- This checklist is not a WCAG certification and must not be called one.
- Record measured hit areas per runtime: CSS px, dp and points separately.

## Requirements

### Functional Requirements

- **FR-001**: Each UX check MUST be recorded per runtime with tool, device and result.
- **FR-002**: Reduced motion MUST be verified on each platform.
- **FR-003**: Task-blocking findings MUST be fixed and retested before G4 passes. Filing records the issue but leaves that gate open.

### Key Entities

None.

## Success Criteria

### Measurable Outcomes

- **SC-001**: UX-07 to UX-10 and UX-14 each have per-runtime evidence.
- **SC-002**: The G4 evidence index links the other applicable UX checks to their feature results and records a passing retest for each task blocker.

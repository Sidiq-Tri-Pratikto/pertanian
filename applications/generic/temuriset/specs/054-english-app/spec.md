# Feature Specification: English for the signed-in app (revamp R7)

**Feature Branch**: `054-english-app`
**Created**: 2026-11-28
**Status**: Built, awaiting review
**Milestone**: Post-M11 revamp, last of the revamps
**Depends on**: 050, 053
**Covers**: S01, UX-01
**Size**: L
**Sources**: revamp plan R7+ (`specs/050-bilingual-foundation` deferred the signed-in screens)

## Context

Spec 050 made every signed-out screen and email bilingual. Signed-in screens stayed Indonesian. This spec makes every signed-in screen available in English: Beranda, portfolio and public page, needs and raises, discovery and matches, partner profiles and mandates, pitches, revisions, discussion, scheduling, partnerships, settings, privacy, import and export.

## User Scenarios & Testing

### User Story 1 - Switch the whole app (Priority: P1)

1. **Given** any signed-in screen, **When** the person presses EN in the header, **Then** the page reloads in English with `<html lang="en">`; ID switches back. The choice is remembered in the `tr_locale` cookie, also set by the signed-out switch and by saving the account language in Profil.
2. **Given** English, **Then** navigation, titles, buttons, fields, statuses, empty states, errors from the service, dates and the turn texts on Beranda and in pitch rooms are English. What people wrote (titles, summaries, mandate requirements) stays as written.

### User Story 2 - Indonesian stays the default (Priority: P1)

**Given** no choice, **Then** every screen is Indonesian exactly as before; existing tests are unchanged.

## Requirements

- **FR-001**: `t('teks Indonesia', values)` returns the source or its English entry in `src/features/i18n/app-en.ts`; shared components (Screen, Status, Button, fields, Select, Dialog, EmptyState, SummaryList, Tabs) translate text they receive.
- **FR-002**: Server components read the language from a per-request store set by `requireMe`; client components from `LocaleProvider`.
- **FR-003**: A test fails when a literal `t()` key has no English, when a placeholder differs between languages, or when `t()` runs while a module loads.
- **FR-004**: The service's whose-turn texts (`app/discussion/service/next_action.py`) follow `X-TemuRiset-Locale`; matching labels, requirement reasons, discovery sections and availability labels are translated where they are shown.

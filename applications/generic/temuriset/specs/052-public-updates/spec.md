# Feature Specification: Public updates (revamp R5)

**Feature Branch**: `052-public-updates`
**Created**: 2026-11-27
**Status**: Built, awaiting review
**Milestone**: Post-M11 revamp, sixth PR of the revamps; stacked on 051
**Depends on**: 006, 050, 051
**Covers**: S01, UX-01
**Size**: M
**Sources**: `reports/temuriset-invention-follow-handoff/IMPLEMENTATION-PLAN.md` ("Latest milestone" and inventor updates)

## Context

The public invention page (051) is a snapshot. The follow handoff's "latest milestone" needs news the inventor writes over time, and following by email (053) needs one event per piece of news. This spec adds public updates: the managing party drafts, publishes, corrects and withdraws short updates, and the newest three appear on the public page. No email is sent yet.

## User Scenarios & Testing

### User Story 1 - The owner writes and publishes an update (Priority: P1)

1. **Given** a published invention, **When** the owner writes a title (at most 120 characters) and text (at most 1,200) under "Kabar publik" and saves, **Then** it is a draft nobody else sees.
2. **Given** a draft and the public page on, **When** the owner presses "Terbitkan", **Then** the update shows on `/temuan/{id}` and `/en/inventions/{id}` under "Kabar terbaru" / "Latest updates" with its date, newest first, at most three.
3. **Given** the public page off, the invention archived, unpublished or suspended, **When** the owner publishes, **Then** `INVALID_TRANSITION` says to turn on the public page; nothing changes. Drafts can still be written while the page is off, but not once the invention is archived (`CONFLICT`).

### User Story 2 - Corrections and withdrawals never repeat an announcement (Priority: P1)

1. **Given** a published update, **When** the owner corrects its text, **Then** the page shows the correction at once and the update keeps its first publication date.
2. **Given** a published update, **When** withdrawn and published again, **Then** it disappears and reappears with its first publication date.
3. **Given** any of the above, **Then** `invention.update_published` is emitted exactly once per update, on its first publication, so following (053) sends each update at most once.

### User Story 3 - Text in another language is labelled (Priority: P2)

**Given** an update written in Indonesian on the English page (or the reverse), **Then** it carries `lang` and the "Written in …" label.

## Requirements

- **FR-001**: Migration 0024 adds `invention_updates` (`invention_id` cascade, author account and party, `title` 120, `body` checked at 1,200, `content_locale` `id`/`en`, `status` `DRAFT`/`PUBLISHED`/`WITHDRAWN`, `published_at` never reset, `withdrawn_at`, `version`) with an index on (`invention_id`, `status`, `published_at`).
- **FR-002**: `GET`/`POST /api/v1/inventions/{id}/updates`, `PUT …/{update_id}` with `expected_version`, `POST …/{update_id}/publish` and `…/withdraw`; all need `EDIT_PORTFOLIO` and answer `NOT_FOUND` to other parties. Creating, publishing and withdrawing take an `Idempotency-Key`. Every change is audited.
- **FR-003**: `GET /api/v1/teasers/inventions/{id}` adds `latest_updates` (up to three published, newest first), only when the public page is on; investor-news-only summaries show none.
- **FR-004**: All five routes are registered in `tests/integration/test_isolation.py`; another party's draft text never leaks.

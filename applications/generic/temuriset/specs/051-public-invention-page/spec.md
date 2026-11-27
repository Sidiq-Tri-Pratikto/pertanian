# Feature Specification: Public invention page (revamp R4)

**Feature Branch**: `051-public-invention-page`
**Created**: 2026-11-27
**Status**: Built, awaiting review
**Milestone**: Post-M11 revamp, fifth PR of the revamps; stacked on 050
**Depends on**: 006, 016, 046, 047, 050
**Covers**: S01, UX-01
**Size**: L
**Sources**: `reports/temuriset-invention-follow-handoff/IMPLEMENTATION-PLAN.md` (sections 2 and 3, "Public invention page")

## Context

The investor summary at `/temuan/{id}` was only visible when the owner opted into investor news (`investor_digest`). The follow handoff wants a public page the owner turns on separately, with an owner-published photo and a short field-test summary, so the invention can be shared before anyone follows it (specs 052 and 053). The two choices stay independent: a public page never puts the invention into investor alerts or the weekly digest.

## User Scenarios & Testing

### User Story 1 - The owner publishes a page (Priority: P1)

1. **Given** a published invention, **When** the owner ticks "Tampilkan halaman publik inovasi ini" and saves, **Then** `/temuan/{id}` and `/en/inventions/{id}` show the title, sector, stage, summary and keywords to anyone, and the investor-news switch is unchanged.
2. **Given** the same form, **When** the owner adds a field-test summary (at most 600 characters), picks one of their own uploaded images and describes it, **Then** the page shows the summary under "Uji lapangan" and the photo at its real size.
3. **Given** a photo without a description, a file that is not an image, or a file of another party, **When** saved, **Then** `VALIDATION_FAILED` on `photo_alt`, `FILE_TYPE_UNSUPPORTED` or `FILE_NOT_AVAILABLE`, and nothing is saved.

### User Story 2 - The photo carries nothing private (Priority: P1)

1. **Given** a JPEG, PNG or WebP with EXIF, XMP, IPTC or text chunks, **When** a visitor loads the photo, **Then** the bytes have no metadata, the EXIF rotation is applied by the page, and the response has `nosniff`, `Content-Security-Policy: default-src 'none'; sandbox` and a five-minute public cache.
2. **Given** the page switched off, the invention archived or unpublished, or the file erased, **When** the page or photo is requested, **Then** both answer 404; every photo request rechecks.

### User Story 3 - A real 404 and the right metadata (Priority: P2)

1. **Given** an unknown or unavailable invention, **When** `/temuan/{id}` or `/en/inventions/{id}` opens, **Then** the response status is 404 with the "not available" page in that language.
2. **Given** an available page, **When** rendered, **Then** it has a title, description, `id`/`en` alternates, and `robots: index` only when the public page is on (investor-news-only pages stay `noindex`). Text written in another language than the page carries `lang` and a "Written in …" label.

## Requirements

- **FR-001**: Migration 0023 adds one new table, `invention_public_pages` (one row per invention, `invention_id` unique with `ON DELETE CASCADE`), holding `enabled`, `enabled_at`, `field_test`, `photo_version_id` (foreign key, `ON DELETE SET NULL`), `photo_alt` (CHECK: required with a photo), `photo_width`, `photo_height`, `photo_orientation` and `content_locale` (CHECK `id`/`en`). It changes no existing table, so the expand-only migration check passes; an invention without a row has the page off.
- **FR-002**: `PUT /api/v1/inventions/{id}/public-page` needs `EDIT_PORTFOLIO`, `expected_version`, and records audit `invention.public_page`.
- **FR-003**: `GET /api/v1/teasers/inventions/{id}` is visible when `investor_digest OR public_page`; alerts and the digest still require `investor_digest`. It adds `follow_enabled`, `field_test_summary`, `photo` and `content_locale`; the field test and photo appear only with the public page on.
- **FR-004**: `GET /api/v1/teasers/inventions/{id}/photo` serves the chosen version with metadata stripped by a standard-library walker (`app/documents/service/public_image.py`). No new dependency.
- **FR-005**: Both routes are registered in `tests/integration/test_isolation.py`.

# Feature Specification: Bilingual foundation (revamp R3)

**Feature Branch**: `050-bilingual-foundation`
**Created**: 2026-11-27
**Status**: Built, awaiting review
**Milestone**: Post-M11 revamp, fourth PR of six revamps; stacked on 049
**Depends on**: 006, 046, 047
**Covers**: S01, UX-01
**Size**: M–L
**Sources**: `reports/temuriset-invention-follow-handoff/IMPLEMENTATION-PLAN.md` (section 4, "Ship Indonesian and English together")

## Context

The follow-an-invention handoff ships in Indonesian and English from the first release. Everything was Indonesian: the page language, the copy, the service's error messages and every email. This spec adds the language machinery and translates every signed-out screen and email, so the public invention page and following (specs 051 to 053) are born bilingual. Signed-in screens stay Indonesian until the English sweep.

## User Scenarios & Testing

### User Story 1 - English addresses (Priority: P1)

1. **Given** `/en/start`, `/en/start/code`, `/en/subscribe`, `/en/subscribe/confirm`, `/en/subscribe/manage` or `/en/inventions/{id}`, **When** opened, **Then** the same page as the Indonesian address renders in English with `<html lang="en">`, English titles and English links that stay under `/en`. Indonesian addresses are unchanged, including `/temuan/{id}`.
2. **Given** any signed-out page, **When** the visitor presses the ID/EN switch, **Then** the same page and step opens in the other language. An email already typed comes along in this tab's storage, never in the address.

### User Story 2 - The service speaks the page's language (Priority: P1)

1. **Given** a request with `X-TemuRiset-Locale: en`, **When** it fails, **Then** the message is English while the code, status and recovery stay the same, and the response carries `Content-Language: en`. Errors raised with a custom Indonesian message stay Indonesian until the English sweep.
2. **Given** a subscription made from an English page, **When** its confirmation, alerts or digest are sent, **Then** they are in English with `/en/...` links; the stored language decides, not the page used later.
3. **Given** a sign-in code request, **When** the email is sent, **Then** it is in the account's language, or the page's language for a new address.

### User Story 3 - Inventor content is labelled (Priority: P2)

**Given** the English summary page, **When** it shows inventor-written text, **Then** that text carries `lang="id"` with a "Written in Indonesian" label. Stored values (sectors, stages) are shown with English names but sent unchanged.

## Requirements

- **FR-001**: `src/proxy.ts` rewrites `/en/...` to the Indonesian route and sets `x-tr-locale: en`; `layout.tsx` sets `<html lang>` from it.
- **FR-002**: Catalogs `src/features/i18n/{id,en}.ts`; `en` is typed as the Indonesian shape, so a missing key fails the typecheck, and a test compares their keys.
- **FR-003**: The web sends `X-TemuRiset-Locale` on every request (browser from `<html lang>`, server reads from `x-tr-locale`); `app/core/locale.py` middleware reads it.
- **FR-004**: Every public error code, status and field message has English (unit-tested).
- **FR-005**: No migration and no new route. `subscribe()` now sends `locale`.

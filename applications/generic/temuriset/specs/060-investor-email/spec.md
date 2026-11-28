# Feature Specification: Investor email revamp (HTML with text fallback)

**Feature Branch**: `060-investor-email`
**Created**: 2026-11-28
**Status**: Seeded, not started
**Milestone**: Revamp 2, demo feedback ([plan](../../docs/roadmap/revamp-2-demo-feedback.md)); Track B
**Depends on**: 046, 053, 056
**Size**: L
**Covers**: FR26, AC85, AC86, AC87
**Flips**: nothing

## Context

Investors who subscribe or follow without an account receive plain-text emails today: correct, but easy to skip. Demo feedback asked for emails an investor wants to read. Research (see the revamp page §6) points to a simple single-column HTML message with a full plain-text alternative, short scannable blocks, one clear action per item, and one-click unsubscribe headers for bulk mail. This spec applies that to every email a subscriber or follower without an account receives:

| Email | Today | After |
|---|---|---|
| Subscription confirmation | text | HTML + text, one button |
| Already subscribed (manage link) | text | HTML + text |
| Direct alert (one invention) | text | HTML card + text |
| Weekly digest (up to five) | text | HTML cards + text |
| Follow confirmation, already following | text | HTML + text |
| Follow update (one public update) | text | HTML update card + text |

Sign-in codes and invitations stay plain text (not part of this spec).

## Layout (every email)

1. **Preheader** (hidden preview line, ≤ 90 characters): the most useful fact, e.g. "Air dan sanitasi · Prototipe · TKT 4 — cocok dengan kata kunci 'air'".
2. **Header**: "TemuRiset" wordmark in text and teal (no image required), and "Demo · Data fiktif" on demo deployments.
3. **Lead**: one sentence saying why this email arrived ("Inovasi baru yang sesuai minat Anda").
4. **Card(s)**, max width 600 px, single column:
   - optional public photo (owner-published, already metadata-free), width 100 %, with its alt text;
   - title as a link to the public page;
   - facts line: "Air dan sanitasi · Prototipe · TKT 4" (TKT only when stated);
   - two-line summary (≤ 240 characters, cut at a word);
   - "Mengapa Anda menerima ini": matched terms as small chips (sektor, tahap, kata kunci);
   - field-test line when the public page has one;
   - one primary button "Lihat ringkasan" (bulletproof table button) and one text link "Ikuti inovasi ini".
5. **Digest only**: up to five cards ordered by match level, then a link "Atur minat Anda".
6. **Footer**: why they receive it (topics and since when, or the followed invention), "Atur langganan", "Berhenti berlangganan" (one click), "Ganti bahasa email: English" (or "Bahasa Indonesia"), and "TemuRiset — pertemuan inovasi dan investor".

Rules: system fonts, body 16 px, line height 1.5, text colour slate-900 on white, links teal-700 (contrast ≥ 4.5:1), all styles inline, `role="presentation"` layout tables, `lang` on `<html>`, `<meta name="color-scheme" content="light dark">`, no web fonts, no tracking pixels, no external CSS, every image has alt text and the email reads fully with images off, total HTML < 100 KB (Gmail clips at 102 KB).

## User Scenarios & Testing

### User Story 1 - An alert worth opening (Priority: P1)

1. **Given** a confirmed subscriber and a matching invention, **When** the alert is sent, **Then** it is multipart: `text/plain` (today's content, reorganised like the HTML) and `text/html` with the layout above; both carry the same facts, links and footer (AC85).
2. **Given** the invention has a public photo, **Then** the card shows it with alt text; without one, the card has no empty image box.
3. **Given** an English subscriber, **Then** every word, date and stage name is English and `<html lang="en">` (AC87).
4. **Given** the email client blocks images, **Then** nothing essential is missing.

### User Story 2 - A digest that scans in ten seconds (Priority: P1)

1. **Given** five matches, **Then** the subject reads "5 inovasi sesuai minat Anda minggu ini" and the preheader names the first two titles.
2. **Given** a phone at 320 px, **Then** cards stack, buttons are at least 44 px tall, nothing scrolls sideways.

### User Story 3 - Leaving is one click (Priority: P1)

1. **Given** any alert, digest or follow update, **Then** the message carries `List-Unsubscribe: <https://…/api/v1/unsubscribe/one-click?t=…>` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` (RFC 8058) (AC86).
2. **Given** a mail client posts to that address, **Then** the subscription (or the one follow) is unsubscribed without sign-in or confirmation page, and repeating it changes nothing.
3. **Given** the footer link, **Then** it opens the existing manage page where "Berhenti berlangganan" also works.

### User Story 4 - Change the email language (Priority: P2)

**Given** the footer link "Ganti bahasa email", **Then** the manage page (subscription or follow) lets the person switch between Bahasa Indonesia and English; later emails follow it. Subscriptions gain the language setting that follows already have.

### User Story 5 - Review before sending (Priority: P1)

**Given** development, **When** a developer opens `GET /api/v1/dev/mail-preview/{template}?lang=id|en`, **Then** the HTML renders in the browser with sample data for each template; the development mailbox returns `html` beside `body`.

## Requirements

- **FR-001**: One content model per email (`EmailContent`: subject, preheader, lead, cards, footer) rendered twice, to text and to HTML, so both parts can never disagree.
- **FR-002**: Mailbox port: `send(..., body, html=None, headers=None)`; development mailbox stores `html` (new nullable column, migration 0027); loopback relay sends both parts and the headers; the relay payload limit rises from 8 KB to 128 KB, still checked.
- **FR-003**: One-click unsubscribe: `POST /api/v1/unsubscribe/one-click?t=` accepts `List-Unsubscribe=One-Click`, needs no cookie, is idempotent, and works for subscriptions and follows. The token is a separate single-purpose link token (purpose `unsubscribe`, 365 days), hashed at rest; the path is excluded from request logs because RFC 8058 requires the token in the URL.
- **FR-004**: `PUT /api/v1/subscriptions/manage` accepts `locale`.
- **FR-005**: No HTML template dependency: stdlib `html.escape` and small render functions; every interpolated value escaped; links absolute `https` from `WEB_ORIGIN`.
- **FR-006**: Relay rechecks (053) unchanged: a queued HTML email is dropped exactly like a text one.

## Success Criteria

- The demo shows a subscriber receiving an alert whose HTML preview looks like a product card, in Indonesian and English.
- Snapshot tests fix each template's HTML and text; size < 100 KB; no unescaped value (test with `<script>` in a title).

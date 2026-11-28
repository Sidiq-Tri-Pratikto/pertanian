# Implementation Plan: Investor email revamp

**Branch**: `f/060-investor-email` | **Spec**: [spec.md](spec.md) | **Track**: B | **Needs**: 056 merged (TKT in cards)

## Files

```text
applications/temuriset-api/
├── migrations/versions/0027_mailbox_html.py           # mailbox_messages.html (nullable text) — take the next free number after rebasing
├── app/identity/repository/sqlalchemy/models.py       # MailboxMessageRecord.html
├── app/identity/service/mailbox_service.py            # send(..., html=None, headers=None); relay payload; 128 KB cap
├── app/identity/service/mail_jobs.py                  # relay job carries html + headers (sealed as today)
├── app/subscriptions/service/email/                   # NEW package
│   ├── content.py      # EmailContent, Card, Footer dataclasses + builders per email kind
│   ├── render_text.py  # EmailContent → text
│   ├── render_html.py  # EmailContent → HTML (inline styles, tokens below)
│   └── tokens.py       # colours and sizes copied from design tokens (hex), one place
├── app/subscriptions/service/mail.py                  # keep public functions; each now returns (subject, text, html, headers)
├── app/subscriptions/service/service.py, follows.py   # pass html + headers; mint the one-click token
├── app/subscriptions/service/unsubscribe.py           # NEW: one-click handler for both kinds
├── app/subscriptions/router.py                        # POST /unsubscribe/one-click; PUT /subscriptions/manage locale
├── app/dev/router.py                                  # GET /dev/mail-preview/{template}
├── app/core/logging.py                                # skip /api/v1/unsubscribe/one-click in request logs
└── tests/
    ├── unit/subscriptions/test_email_render.py        # snapshots (text + HTML) per template × lang; escaping; size
    ├── integration/subscriptions/test_email_html.py   # alert/digest/follow produce both parts + headers; dev mailbox html
    ├── integration/subscriptions/test_one_click.py    # POST works without cookie, idempotent, follow and subscription
    └── integration/test_isolation.py                  # new routes in NOT_DATA_ROUTES (token-only)
applications/temuriset-web/src/
├── views/subscriptions/ManageView.tsx, FollowManageView.tsx   # language select for subscriptions; one-click success page not needed
├── features/i18n/app-en/mail.ts
└── tests/manage-language.test.tsx
```

## Contracts

```python
# mailbox port
async def send(self, session, *, to_email: str, subject: str, body: str,
               html: str | None = None, headers: dict[str, str] | None = None,
               reference: MailReference | None = None) -> None

# one-click (RFC 8058): body is application/x-www-form-urlencoded "List-Unsubscribe=One-Click"
POST /api/v1/unsubscribe/one-click?t={token}   → 200 {"status": "unsubscribed"} (also for an already-unsubscribed token)
                                                → 404 NOT_FOUND for an unknown or expired token

PUT /api/v1/subscriptions/manage   body: {token, topics?, locale?}
GET /api/v1/dev/mailbox            items gain "html": str | null
GET /api/v1/dev/mail-preview/{template}?lang=id|en   templates: confirm, already, alert, digest, follow_confirm, follow_already, follow_update
```

Headers on alert, digest and follow update:

```text
List-Unsubscribe: <https://{origin}/api/v1/unsubscribe/one-click?t={token}>, <mailto:…> (mailto only when a sender address is configured)
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```

## Content model

```python
@dataclass(frozen=True)
class Card:
    title: str
    url: str
    facts: list[str]
    summary: str
    reasons: list[str]
    photo_url: str | None
    photo_alt: str | None
    field_test: str | None
    primary: tuple[str, str]  # (label, url)
    secondary: tuple[str, str] | None


@dataclass(frozen=True)
class EmailContent:
    lang: str
    subject: str
    preheader: str
    lead: str
    cards: list[Card]
    action: tuple[str, str] | None  # single button for confirmations
    footer_reason: str
    manage_url: str
    unsubscribe_url: str | None
    language_url: str | None
    demo: bool
```

`render_text(content)` and `render_html(content)` are the only renderers. Word lists for both languages stay in `mail.py`'s tables (extend `_TEXT` / `_FOLLOW_TEXT`).

## HTML rules (checked by tests)

- Doctype + `<html lang>`; `<meta charset="utf-8">`, `<meta name="viewport" content="width=device-width,initial-scale=1">`, `<meta name="color-scheme" content="light dark">`.
- Hidden preheader: `<div style="display:none;max-height:0;overflow:hidden">…</div>`.
- Outer table width 100 %, inner 600 px max (`max-width:600px;width:100%`); cards are tables with 24 px padding, 1 px border `#E2E8F0`, radius 12 px.
- Text `#0F172A` on `#FFFFFF`, muted `#475569`, link and button `#0F766E` (white text on the button), chips `#F0FDFA` background with `#115E59` text. Font stack `-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif`; 16 px body, 22 px titles.
- Bulletproof button: `<table role="presentation"><tr><td style="background:#0F766E;border-radius:8px"><a style="display:inline-block;padding:12px 20px;color:#FFFFFF;…">…</a></td></tr></table>`, min height 44 px.
- Every dynamic value through `html.escape`; URLs built with `urllib.parse.quote` for path parts.
- Total size < 100 KB; no `<style>` blocks, no scripts, no external resources except the public photo URL.

## Tasks

1. Content model + text renderer; port today's texts into builders; snapshot tests prove the text part keeps every link and fact it has today (diff reviewed).
2. HTML renderer + tokens; snapshot per template × language; escaping test; size test; accessibility asserts (lang, alt, role=presentation, no empty links).
3. Mailbox port `html`/`headers`; migration 0027; dev mailbox returns `html`; loopback relay sends both and the headers; payload cap 128 KB; existing relay tests extended.
4. One-click token (purpose `unsubscribe`) for subscriptions and follows, minted per email; route; logging skip; isolation registry; integration tests (no cookie, idempotent, wrong token 404, recheck drops queued mail afterwards).
5. Subscription `locale` in manage; web select on ManageView; footer link to it; test.
6. Dev preview route (development only, 404 otherwise) with sample data; test.
7. Demo: `docs/demo/scenario.md` step "Tunjukkan email investor" using `/api/v1/dev/mail-preview/alert?lang=id`.
8. English in `app-en/mail.ts` for the manage-page additions.

## Done when

```bash
cd applications/temuriset-api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head && DEMO_MODE=false make check
cd ../temuriset-web && make check
```

Manual: open each preview in a browser at 320 and 1280 px, in ID and EN, with images on and off; send one alert through the loopback relay test and read both parts.

## Do not

- Do not add an HTML template library; stdlib only.
- Do not put tokens in any URL except the one-click address (RFC 8058 requires it) and keep that path out of logs.
- Do not change sign-in code or invitation emails.
- Do not include tracking pixels or open tracking.

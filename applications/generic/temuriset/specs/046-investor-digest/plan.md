# Implementation Plan: Investor quick subscription, topic alerts and weekly digest

**Branch**: `f/046-investor-digest` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-api/
├── app/subscriptions/
│   ├── router.py                 # POST /subscriptions, /confirm, GET|PUT /subscriptions/manage, POST /unsubscribe,
│   │                             #   GET /teasers/inventions/{id}
│   ├── model/schema.py
│   ├── repository/sqlalchemy/    # investor_subscriptions, subscription_deliveries, subscription_requests
│   └── service/
│       ├── service.py            # subscribe, confirm, manage, unsubscribe, teaser
│       ├── matching.py           # pure: topic match level and reason line
│       ├── mail.py               # alert and digest text, sent through the mailbox port
│       └── jobs.py               # invention consumer, alert delivery, weekly digest job
├── app/portfolio/                # inventions.investor_digest + PUT /inventions/{id}/investor-digest
├── app/dev/router.py             # POST /dev/digest runs the weekly digest now
└── migrations/versions/0022_investor_subscriptions.py
applications/temuriset-web/src/
├── app/langganan/page.tsx, app/langganan/konfirmasi/page.tsx, app/langganan/atur/page.tsx, app/temuan/[id]/page.tsx
├── features/subscriptions/
└── views/subscriptions/
```

## Data

| Table | Columns |
|---|---|
| `investor_subscriptions` | `email` (unique, lower-cased), `topics` JSONB (`sectors`, `stages`, `keywords`), `status` (`PENDING`, `ACTIVE`, `UNSUBSCRIBED`), `confirm_token_sha256`, `confirm_expires_at`, `manage_token_sha256`, `confirmed_at`, `consent_source`, `locale`, `version` |
| `subscription_deliveries` | `subscription_id`, `invention_id`, `kind` (`ALERT`, `DIGEST`), `week`; unique (`subscription_id`, `invention_id`) |
| `subscription_requests` | `email_sha256`, `address_sha256`, `created_at`, for rate limits |
| `inventions.investor_digest` | Boolean, default false |

## Matching

`match(topics, invention)` returns `ALERT`, `DIGEST` or `None` with the matched terms. Groups are sectors, stages and keywords; a filled group matches when the invention's sector, stage, or title, summary and keywords contain one of its terms. All filled groups matching is `ALERT`; at least one is `DIGEST`.

## Mail

Alerts and digests use `mailbox_for(settings).send(...)` with a `MailReference(kind="subscription")`. The loopback relay rechecks before delivery that the subscription is still active. The development mailbox stores the message for `/dev/mailbox`. A disabled mailbox refuses the subscription itself.

## Test Plan

Pure matching table; subscribe, confirm, enumeration, rate limits, disabled mail; opt-in switch and capability; alert, cap, digest, once per invention, empty week; manage and unsubscribe; teaser projection and leak test; isolation for the switch; jsdom and axe for the pages; one Playwright journey from subscription to alert to teaser to signup.

## Out of Scope

A real email provider (042), open and click tracking, and linking a subscription to a later account.

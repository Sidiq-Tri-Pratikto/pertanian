# Implementation Plan: Web sign-in, onboarding and context

**Branch**: `008-web-auth-context` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/
├── api/server.ts                 # serverGet with forwarded cookies (from 004); getMe()
├── api/client.ts                 # post(), with Idempotency-Key and Origin-safe same-origin calls
├── app/start/page.tsx            # persona, name, email, locale, time zone
├── app/start/kode/page.tsx       # code entry, resend
├── app/settings/page.tsx         # account, organizations, members, invitations
├── app/undangan/[token]/page.tsx # invitation acceptance
├── components/tr/                # port TextField, Select, ErrorSummary, ContextSwitcher, FieldError, SummaryList
├── features/session.ts           # requireMe() replaces requirePersona(); redirect with return path
└── views/{StartView, CodeView, SettingsView, InvitationView}.tsx
e2e/auth.spec.ts                  # reads codes from /api/v1/dev/mailbox
```

Remove the persona cookie and the persona Server Action once the account carries the persona; keep the redirect behaviour.

## Copy

Use the handoff lexicon: "Bertindak sebagai", "Masuk", "Kirim kode", "Kode verifikasi", "Kirim ulang kode", "Terima undangan". Errors are two clauses and come from the API envelope.

## Test Plan

View tests for each state including error summary focus; page tests with mocked `/me`; Playwright for both personas, wrong code, resend, context switch, invitation accept; axe on every new view; 003 suite extended with signed-in routes.

## Out of Scope

Profile publication (031), privacy and reports (035).

## Task Outline

1. Port the form components with tests.
2. Server fetch with cookies, `requireMe`.
3. S01 and code screens.
4. Context switcher in the shell and on action screens.
5. Settings, organizations and invitations.
6. Playwright journeys, registry flip.

# Implementation Plan: Web shell

**Branch**: `002-web-shell` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Summary

The starter has no web client, so this adds `applications/temuriset-web` by hand: Next.js 16 App Router, React 19, TypeScript 6, ESLint 10 with `eslint-config-next`, Vitest 5 with jsdom and Testing Library, and axe. Design-system stylesheets are copied verbatim; seven `TR` components are ported to TSX with the same class names.

## Technical Context

**Language/Version**: TypeScript 6.0, Node 24, Next.js 16.4.5, React 19.3.1
**Testing**: Vitest 5, Testing Library, axe-core
**Target Platform**: Desktop and phone browsers
**Project Type**: Web client plus API

## Project Structure

```text
applications/temuriset-web/
├── next.config.ts                 # rewrites /api/v1 and /health to API_URL
├── src/app/                       # routes: start, home, inventions, discover, opportunities, pitches, settings,
│                                  #   segera-hadir/[feature], root redirect, not-found
├── src/api/                       # client.ts, errors.ts, schema.generated.ts
├── src/components/tr/             # Icon, Button, Status, EmptyState, NextStep, ChoiceGroup, Screen
├── src/design/                    # tokens.css, bundle.css (copied), app.css (deviations D1, D2)
├── src/features/                  # persona, session, actions, registry, destinations, ServiceStatus
├── src/views/                     # StartView, DestinationView, ComingSoonView, SettingsView, parts
└── tests/                         # components, pages, service status, a11y, registry, design drift
```

## Decisions

- Persona is a server-read cookie so navigation renders without a flash; the form posts to a Server Action, so it works without JavaScript. 008 replaces the cookie with the account preference.
- Pages are thin: read the persona, pick a destination, render a view. Views are tested directly.
- `Screen` uses real links (deviation D3). The registry and destinations are data, so feature PRs flip entries instead of editing screens.

## Test Plan

Persona parsing and destinations; component behaviour (blocked and busy buttons, choice labels, current destination, Lainnya, skip link); every page with and without a persona; the persona action stores an http-only cookie and refuses other values; service status success, unreachable with retry, final failure with reference; failure parsing never leaks a non-envelope body; axe on each view; copied stylesheets equal the source; registry covers S01–S18 and links existing specs.

## Out of Scope

Accounts and sessions (006, 008), browser-level checks (003), any feature.

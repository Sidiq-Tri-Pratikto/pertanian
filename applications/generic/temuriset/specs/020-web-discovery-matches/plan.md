# Implementation Plan: Discovery and match screens

**Branch**: `020-web-discovery-matches` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/
├── app/discover/page.tsx, app/matches/page.tsx
├── components/tr/{InventionCard, TextField}.tsx    # if not ported yet
├── features/discovery/{filters.ts, api.ts}         # filters in the URL so Back restores them
└── views/discovery/{DiscoverView, PartnerCard, MatchesView, MatchCard}.tsx
e2e/matching.spec.ts
```

## Prototype Reference

`vm.discover`, `vm.matches`, `Matches.dc.html`, the abstain fix recorded in the prototype handoff section 11.

## Test Plan

Filter URL round trip; card and match states; abstain group; external route copy; Playwright J01 to preflight entry; axe.

## Out of Scope

Preflight (024).

## Task Outline

1. Filters in URL; discovery views.
2. Match view with Disclosure details.
3. Return paths from gaps.
4. Playwright, registry flips.

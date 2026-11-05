# Implementation Plan: Relationship and public profile screens

**Branch**: `032-web-relationship-profile` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/
├── app/partnerships/new/page.tsx, app/partnerships/[id]/page.tsx, app/profiles/[partyId]/page.tsx
├── components/tr/PartnershipConsent.tsx
└── views/relationships/{ProposeView, PartnershipView, PublicProfileView}.tsx
e2e/j05-relationship.spec.ts
```

## Prototype Reference

`vm.partnership`, `vm.profile`, `Partnership.dc.html`, `Profile.dc.html`; walker `j05` and `j05b`.

## Test Plan

Consent component states; correction dialog; restriction; signed-out profile; J05 Playwright; axe.

## Out of Scope

Agreement execution of any kind.

## Task Outline

1. Port PartnershipConsent with tests.
2. Propose and confirm screens.
3. Public profile, signed out.
4. J05 journey, registry flips.

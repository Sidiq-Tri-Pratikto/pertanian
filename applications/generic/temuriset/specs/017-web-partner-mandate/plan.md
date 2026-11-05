# Implementation Plan: Partner profile and mandate editor

**Branch**: `017-web-partner-mandate` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/
├── app/partners/[partyId]/page.tsx, app/opportunities/page.tsx, app/opportunities/[id]/edit/page.tsx
├── components/tr/{RequirementRow, Disclosure, Link}.tsx
└── views/intake/{PartnerView, MandatesView, MandateEditView, MandateReview}.tsx
e2e/intake.spec.ts
```

## Prototype Reference

`vm.partner`, `vm.opportunity`, `Partner.dc.html`, `Opportunity.dc.html`.

## Test Plan

View states, external route copy, review step, stale version; Playwright; axe.

## Out of Scope

Incoming pitches (026), discovery (020).

## Task Outline

1. Ports with tests.
2. Profile view and own mandates list.
3. Mandate editor and review.
4. Playwright, registry flips.

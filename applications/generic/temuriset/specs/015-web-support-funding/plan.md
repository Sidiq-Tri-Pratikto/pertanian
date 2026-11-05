# Implementation Plan: Support and funding screens

**Branch**: `015-web-support-funding` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/
├── app/support-requests/page.tsx, [id]/page.tsx
├── app/funding-requests/[id]/page.tsx, [id]/edit/page.tsx
├── components/tr/{FinancialScope, FundingRequestCard, Checkbox}.tsx
├── features/money.ts             # formatRange(currency, min, max) on strings; mirrors TR.format.range
└── views/needs/{SupportListView, SupportView, FundingView, FundingEditView}.tsx
e2e/needs.spec.ts
```

## Prototype Reference

`vm.support`, `vm.funding`, `srFinancial`, `fundingCard`; `TR.format.amount` and `range` in the design-system bundle for the formatter oracle.

## Test Plan

Money formatter against `TR.format` cases (null, open-ended, equal, decimals); view states; return path; capability-off notice; Playwright; axe.

## Out of Scope

Matching (020), pitches (024).

## Task Outline

1. Money formatter and FinancialScope port.
2. Support list and form.
3. Funding read and edit.
4. Step 3 links; Beranda queue item.
5. Playwright, registry flips.

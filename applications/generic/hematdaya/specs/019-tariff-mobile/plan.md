# Implementation Plan: Tariff and cost on mobile

**Branch**: `019-tariff-mobile` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Add cost to Beranda and asset detail, and the tariff section to settings.

## Project Structure

```text
src/components/hd/HDCostEstimate.tsx
src/components/hd/HDNumericField.tsx
src/features/settings/TariffSection.tsx
src/features/cost/useTariffs.ts
```

## Mobile

The native cost component receives the amount, coverage and estimate status from the summary. Port `HD.format.parseDecimal` for field validation, and submit a canonical decimal string. Omit `effective_from` for the service's effective-now default. For a retroactive correction, show and confirm the chosen date in the site timezone, then submit the resolved instant with `is_correction: true`. Blank input sends no mutation. Display cost and tariff provenance from the confirmed response only.

Keep the operation key from 018 with the confirmed draft for a retry after an unknown result. A changed draft needs a new confirmation and operation key. Verify the same owner before resuming a save after sign-in in 037.

Offer a split estimate when the summary reports `uniform_split_available`. Keep the user's explicit opt-in with the selected window and include `allow_uniform_tariff_split` in the summary query and cache key for Beranda and asset detail. Display the server's covered energy and split assumption, or the reason the affected portion remains unknown.

## Prototype Reference

`costBlock` and the tariff part of `Settings` in `hematdaya-app.js`.

## Test Plan

Test known, missing, zero and partial amounts and accepted and declined splits. Verify decimal comma, dot rejection, blank input preserving an existing tariff, disabled capability, effective-now default, retroactive confirmation and cancellation, and draft retention after save failure.

## Out of Scope

Bill reconciliation.

## Task Outline

1. HDNumericField.
2. HDCostEstimate with Detail biaya.
3. Tariff section.
4. Flip registry.

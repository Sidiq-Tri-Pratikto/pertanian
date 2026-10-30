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

Unlike the web `HD.CostEstimate`, the native component receives `amount_idr` and copy from the summary. Port `HD.format.parseDecimal` for field validation only; the service validates again.

## Prototype Reference

`costBlock` and the tariff part of `Settings` in `hematdaya-app.js`.

## Test Plan

Known, missing, zero, split, partial; decimal comma; empty; dot rejected; capability off; save failure keeps draft.

## Out of Scope

Bill reconciliation.

## Task Outline

1. HDNumericField.
2. HDCostEstimate with Detail biaya.
3. Tariff section.
4. Flip registry.

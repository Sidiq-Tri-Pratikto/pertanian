# Implementation Plan: Populated Beranda

**Branch**: `013-beranda-s03` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Replace the empty Beranda with the populated S03 when a workspace has data.

## Project Structure

```text
src/lib/format.ts                    # Indonesian formatting from decimal strings, no floats
src/components/hd/HDPeriodSelector.tsx
src/components/hd/HDScopeSummary.tsx
src/components/hd/HDEnergyMetric.tsx
src/components/hd/HDDataQuality.tsx
src/components/hd/HDContributionRanking.tsx
src/components/hd/HDChartDataAlternative.tsx
src/components/hd/HDDisclosure.tsx
src/features/energy/useSummary.ts
src/app/(tabs)/(beranda)/beranda.tsx
```

## Mobile

- `format.ts` ports `HD.format` for `14,700 kWh`, `Rp22.050`, `57,14%`, `19–25 Oktober 2026`, working on strings. Bar widths may use `Number()` for layout only, never for a displayed value.
- `HDContributionRanking` takes `share_percent` from the service; it computes nothing.
- Shape mismatches to reconcile with the system: `last7` vs this-week, `Provenance` `demo` vs `simulated`, `meter` vs `site_total`.

## Prototype Reference

`Beranda`, `rankingAlt`, `qualityBlock`, `firstGap` in `hematdaya-app.js`. Component contracts in `docs/design/components/`.

## Test Plan

Each scenario: base, today empty, current, partial, zero, scope conflict. Formatting table tests. Tap count. Period change retains scope. Refresh failure keeps content. No schedule or output card. 320 px and large text.

## Out of Scope

Cost value (019), insights (022), scope editing (029).

## Task Outline

1. `format.ts` with table tests.
2. Components, smallest first, each with its states.
3. `useSummary` with navigation context.
4. Compose S03 in reading order.
5. Flip registry entries.

# Implementation Plan: Saran and evidence screens

**Branch**: `022-saran-s07-s08` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
src/components/hd/HDInsightSummary.tsx
src/components/hd/HDEvidencePanel.tsx
src/features/insights/{useInsights.ts, useInsight.ts}
src/app/(tabs)/(saran)/saran.tsx
src/app/(tabs)/(beranda,perangkat,saran)/saran/[id].tsx
```

## Summary

Screens over 021. Beranda gains its featured observation.

## Mobile

This spec introduces `src/components/hd/HDHistoryChart.tsx` for the aligned current and reference series, with its text summary and data table; 015 extends it for asset history (revised plan, 2026-11-06).

`HDEvidencePanel` follows the design system's ordered steps (see the `design-system-binding` notes in `docs/design/README.md`). Pass the exact revision from Beranda or Saran into the detail route, read it through 021's `?revision=` contract, and include it in the query key. Display supersession status when the service reports it. Reuse 015's `HDHistoryChart` and data alternative with the frozen current/reference series and mask from that revision. Keep mutable asset history out of the evidence panel.

## Prototype Reference

`Saran`, `Insight` in `hematdaya-app.js`, `PatternEvidence` in the design system.

## Test Plan

Test the featured item, evidence order, calculation detail, and shared chart and table support. Correct the data between showing a card and opening it, then verify the exact selected revision remains visible. Cover no finding, learning, notices, back position, and the absence of forbidden actions.

## Out of Scope

Feedback actions (023).

## Task Outline

1. HDInsightSummary.
2. HDEvidencePanel.
3. Saran list.
4. Evidence route.
5. Beranda featured slot.
6. Flip registry.

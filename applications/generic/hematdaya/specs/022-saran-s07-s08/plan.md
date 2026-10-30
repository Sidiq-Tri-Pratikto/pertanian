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

`HDEvidencePanel` follows the design system's ordered steps. Its headings differ from the brief; the system's wording stands until the owner decides (see `design-system-binding` notes in `docs/design/README.md`). The comparison chart reuses `HDHistoryChart` with the reference series.

## Prototype Reference

`Saran`, `Insight` in `hematdaya-app.js`, `PatternEvidence` in the design system.

## Test Plan

Featured item; order of evidence; calculation detail; comparison table; no finding; learning; notices; back position; forbidden actions absent.

## Out of Scope

Feedback actions (023).

## Task Outline

1. HDInsightSummary.
2. HDEvidencePanel.
3. Saran list.
4. Evidence route.
5. Beranda featured slot.
6. Flip registry.

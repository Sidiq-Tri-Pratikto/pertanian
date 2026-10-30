# Implementation Plan: Metric screen

**Branch**: `033-metric-s12` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
src/components/hd/HDOutputMetricPreview.tsx
src/features/output/{useMetricDraft.ts, MetricForm.tsx}
src/app/(tabs)/(beranda,perangkat,saran)/metrik.tsx
```

## Summary

S12 over the output API. Every result comes from `/preview`.

## Prototype Reference

`Metric` in `hematdaya-app.js`. Unlike the prototype, the client calls the preview route and does not compute.

## Test Plan

Actual; estimated; partial day confirmation; zero; missing; disable; back keeps draft; capability off; keyboard and large text.

## Out of Scope

Comparison history of intensity on screen beyond Saran.

## Task Outline

1. Form and draft.
2. Preview call.
3. Save and disable.
4. Beranda and detail display.
5. Flip registry.

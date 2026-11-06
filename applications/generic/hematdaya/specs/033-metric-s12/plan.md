# Implementation Plan: Metric screen

**Branch**: `033-metric-s12` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
src/components/hd/HDOutputMetricPreview.tsx
src/features/output/{useMetricDraft.ts, MetricForm.tsx}
src/app/(tabs)/(beranda,perangkat,saran)/metrik.tsx
```

## Summary

S12 over the output API, with entry points from S09 and the asset detail from 014. Every proposed result comes from `POST /sites/{site_id}/output-metric/preview`.

Keep the preview fingerprint alongside the exact draft it represents. Clear both preview result and fingerprint when any input changes, and ignore responses for an older draft. On confirmation, send the reviewed definition and denominator together through `PUT /sites/{site_id}/output-metric` with that fingerprint. Refresh Beranda and asset detail only after acknowledgment. A rejected or stale save leaves the confirmed metric and draft intact and presents a field correction or a new preview action.

## Prototype Reference

`Metric` in `hematdaya-app.js`. Unlike the prototype, the client calls the preview route and does not compute.

## Test Plan

- Actual, estimated, partial day confirmation, zero.
- Missing, entry from S09 and S06, edit after preview, late preview response for an older draft.
- Stale and rejected saves, one request saves definition and input, disable, back keeps draft.
- Capability off, keyboard and large text.

## Out of Scope

Comparison history of intensity on screen beyond Saran.

## Task Outline

1. Form and draft.
2. Preview call.
3. Aggregate save and disable.
4. Beranda and detail display.
5. Flip registry.

# Implementation Plan: Insight feedback

**Branch**: `023-feedback` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/feedback/
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/service.py
migrations/versions/0008_create_insight_feedback.py
src/features/insights/useFeedback.ts
src/app/(tabs)/(beranda,perangkat,saran)/saran/tersembunyi.tsx
```

## Summary

Harmless, reversible feedback with visibility rules applied by the service.

## API Contract

`POST /api/v1/insights/{insight_id}/feedback` with `{action, revision}`; returns the visibility state and `until`. Insights list gains `visibility` and a `hidden` count. `GET /api/v1/sites/{site_id}/insights/hidden`.

## Prototype Reference

`saveFeedback`, `feedbackState`, `Hidden`, `restoreBtn`; test AT-39.

## Test Plan

Each action; idempotent retry; snooze on frozen and wall clocks; restore; revision change; measurements untouched; foreign insight; failure keeps state; flash with restore link.

## Out of Scope

Push (045).

## Task Outline

1. Migration and service tests.
2. Router with idempotency.
3. Visibility in insights list.
4. Mobile actions and hidden list.
5. Flip registry.

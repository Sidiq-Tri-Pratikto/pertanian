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

`POST /api/v1/insights/{insight_id}/feedback` with `{action, revision}` and `Idempotency-Key` returns the visibility state and `until`. Verify the insight owner and revision membership before replaying or applying an operation. Enforce unique keys per principal and feedback operation. Bind each key to the insight ID, revision and action, and store the original outcome atomically with the feedback. Identical retries, including concurrent ones, return that outcome. Reject a different payload for the same key without applying a change. Keep the same key on the client when retrying an unknown outcome.

The insights list gains `visibility` and a `hidden` count. `GET /api/v1/sites/{site_id}/insights/hidden` reads the owner's hidden results. Apply visibility to the revision that received the feedback. Equivalent recomputation retains it, and a genuinely new revision does not inherit it.

## Prototype Reference

`saveFeedback`, `feedbackState`, `Hidden`, `restoreBtn`; test AT-39.

## Test Plan

Test each action, lost-response and concurrent retries, and key reuse with a different action, insight or revision. Verify snooze on both clocks, restore, equivalent and changed revisions, unchanged measurement identities, values and totals, and rejection of foreign insight or revision IDs. Test preserving state on failure and the restore link after hiding.

## Out of Scope

Push (045).

## Task Outline

1. Migration and service tests.
2. Router with idempotency.
3. Visibility in insights list.
4. Mobile actions and hidden list.
5. Flip registry.

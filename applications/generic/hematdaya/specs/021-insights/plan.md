# Implementation Plan: Insights and evidence

**Branch**: `021-insights` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Deterministic rules on top of comparison, immutable evidence revisions, and ranked lists.

## Project Structure

```text
app/insights/
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{rules.py, notices.py, copy.py, service.py}
migrations/versions/0007_create_insights.py
```

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/sites/{site_id}/insights?start_date=&end_date=` | `observations[]`, `notices[]`, `learning_count`, `comparable_count` |
| `GET /api/v1/insights/{insight_id}` | Current revision with evidence; `?revision=` for an older one |

## Design

Evaluate on read for the requested period, upsert by `identity_key` (`kind:asset:period`). Evidence hash decides whether a new revision is needed. Compute-on-read keeps recompute simple, per the architecture decisions. Policy ID `change`, version 1.

## Prototype Reference

`evaluateInsights`, `insightCopy`, `feedbackState`, `staleSources`, `RULE_TEXT`.

## Test Plan

AT-17 numbers; no observation for base fixtures; revision on change; idempotent evaluation; ranking; decrease wording; continuous asset copy; forbidden-word lint; notices for partial, stale, scope; owner isolation.

## Out of Scope

Outside-window and intensity rules (030, 032), feedback (023), mobile (022).

## Task Outline

1. Rule tests from oracles.
2. Rules and notices.
3. Copy with lint.
4. Migration and revision logic.
5. Router, contract; flip `core`.

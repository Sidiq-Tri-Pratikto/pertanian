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
| `GET /api/v1/sites/{site_id}/insights?start_date=&end_date=` | Active observations with IDs and revisions, notices, `learning_count`, `comparable_count` |
| `GET /api/v1/insights/{insight_id}` | Current active revision after re-evaluation. `?revision=` returns the specified frozen revision with supersession status |

## Design

Evaluate on read for the requested period, keyed by `identity_key` (`kind:asset:period` within the site). Expose an invalidation operation so 026 and other relevant writes record the affected identities or periods atomically with the input changes. Read the matching input version and apply one atomic, version-checked transition. If inputs change during evaluation, recompute before publishing. If a current observation no longer qualifies, clear its active status and mark its old revision superseded. Return active results only after resolving pending invalidation for the requested data.

Hash the semantic evidence snapshot, including policy ID and version. Exclude generation time and invalidation metadata so equivalent evidence retains its revision and feedback. Enforce unique revision numbers per insight and update the current revision and supersession status in one transaction. Store the aligned comparison series and common mask in the immutable snapshot with the window and scope. Exact revision reads return that snapshot, even after correction or retirement. Initial policy ID is `change`, version 1.

## Prototype Reference

`evaluateInsights`, `insightCopy`, `feedbackState`, `staleSources`, `RULE_TEXT`.

## Test Plan

Verify AT-17 values and that base fixtures produce no observation. Test correction and retirement, historical revision reads, atomic invalidation and rollback, and concurrent reads without duplicate or stale publication. Verify equivalent recomputation, ranking, copy for decreases and continuous assets, forbidden words, notices for partial or stale data and scope conflicts, and owner isolation.

## Out of Scope

Outside-window and intensity rules (030, 032), feedback (023), mobile (022).

## Task Outline

1. Rule tests from oracles.
2. Rules and notices.
3. Copy with lint.
4. Migration and revision logic.
5. Router, contract; flip `core`.

# Implementation Plan: Optional organization review

**Branch**: `033-organization-review` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/review/
├── router.py                     # /workspace/review-queue, /workspace/reviews/{id}/approve|return, /review-checklists
├── service/gates.py              # PublicationGate and SubmissionGate implementations
├── service/composition_change.py # refuse while pending
└── repository/sqlalchemy/        # review_checklists, review_items
applications/temuriset-web/src/app/workspace/review-queue/page.tsx
.github/workflows/temuriset-web.yml   # matrix over COMPOSITION for e2e
migrations/versions/0018_review.py
```

## Prototype Reference

`decideReview`, `setFlag('orgReview')` in `domain.js`; `vm.review`. The prototype returned items as WITHDRAWN; the PRD says return to the previous state, which this spec implements.

## Test Plan

AC58–AC60; return to origin state; reviewer scope limits; queue view, axe; composition matrix in CI.

## Out of Scope

Moderation (034).

## Task Outline

1. Gates with AC58/AC59 tests.
2. Queue, approve, return.
3. Composition change rule (AC60).
4. S17 web screen.
5. CI composition matrix; flips.

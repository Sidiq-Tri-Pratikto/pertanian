# Implementation Plan: Decisions and itemized revisions

**Branch**: `025-decisions-revisions-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/pitches/
├── router.py                     # + /begin-review, /decisions, /revision-rounds, /revision-items/{id}/answer,
│                                 #   /revision-items/{id}/review, /resubmit, /withdraw, /close
├── service/transitions.py        # the PRD section 7 table as data; one function applies it
├── service/decisions.py
└── service/revisions.py
migrations/versions/0013_decisions_revisions.py
```

## Prototype Reference

`decide`, `requestRevision`, `saveAnswer`, `resubmit`, `reviewItem`, `withdraw` in `domain.js`; oracles AC40–AC44, J03, "approved cannot go to revision".

## Test Plan

Transition table exhaustive test; AC40–AC45; concurrent decisions; answer drafts with versions; attachment failure keeps answers; isolation; outbox events for notifications.

## Out of Scope

Discussion and tasks (027), scheduling (028), web (026).

## Task Outline

1. Transition table and exhaustive test.
2. Begin review, decisions with concurrency.
3. Rounds, items, answers.
4. Resubmit with new submission and grants.
5. Item review, withdraw, close; contract.

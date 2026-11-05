# Implementation Plan: Deliberate pitch submission

**Branch**: `023-pitch-submission-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/pitches/
├── router.py                     # POST /pitches; GET /pitches?box=outgoing|incoming; GET /pitches/{id}
├── model/{models.py, schema.py}  # PitchStatus: DRAFT, PENDING_WORKSPACE_REVIEW, SUBMITTED, UNDER_REVIEW,
│                                 #   REVISION_REQUESTED, APPROVED_FOR_DISCUSSION, REJECTED, WITHDRAWN, CLOSED
├── repository/sqlalchemy/        # pitches (partial unique index), pitch_submissions, pitch_submission_files
└── service/submission.py         # recheck, freeze, grants via documents service, rate limit
migrations/versions/0012_pitches.py
```

## API Contract

`POST /api/v1/pitches` (Idempotency-Key) `{acting_party_id, preflight_token, brief, files: [{document_id, version}]}` → 201 `{"pitch_id", "status": "SUBMITTED", "submission": 1, "operation_id"}`.

Codes: `DUPLICATE_PITCH` 409 (with `pitch_id`), `TARGET_CLOSED` 409, `PREFLIGHT_STALE` 409, `NOT_READY` 422, `RATE_LIMITED` 429.

## Prototype Reference

`submitPitch`, `activePitch`, `freeze`; oracles F01-STALE, AC26, F01-TIMEOUT, F05 duplicate.

## Test Plan

AC26, AC37–AC39; stale; not ready; rate limit; snapshot unchanged after edits; grants only for chosen versions; parallel submits; isolation; outbox notification event.

## Out of Scope

Decisions (025), web (024).

## Task Outline

1. Migration with partial index; failing AC tests.
2. Recheck and freeze.
3. Grants and notification event.
4. Idempotency and parallel test.
5. Lists and detail, contract.

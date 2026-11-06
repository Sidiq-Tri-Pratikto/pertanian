# Implementation Plan: Relationship records confirmed on the same version

**Branch**: `030-partnerships-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/relationships/
├── router.py                     # Pitch proposal and eligibility, plus versioned partnership actions
├── service/service.py            # propose, correct, confirm, decline, restrict, contest
├── service/consent.py            # Checksums and effective fields
└── repository/sqlalchemy/        # partnerships, partnership_versions, partnership_confirmations, partnership_restrictions
migrations/versions/0016_relationships.py
```

## Prototype Reference

`proposePartnership`, `requestCorrection`, `confirmPartnership`, `restrictField`, `effectiveFields` in `domain.js`; oracles J05 and AC21.

## Test Plan

AC21, AC52–AC54; checksum binding; restriction append-only; contest hides; property test on consent; route isolation; two simultaneous proposals for the same pitch.

## Integration decisions

Read proposal options through the same eligibility rules as proposal creation. Lock the pitch before validating and inserting a proposal, so simultaneous parties produce one relationship and a recoverable conflict. Keep public consent and review decisions in the API.

## Out of Scope

Public profile pages (031, 032).

## Task Outline

1. Consent function with property tests.
2. Versions and checksums.
3. Propose, correct, confirm, decline.
4. Restrictions and contest; contract.

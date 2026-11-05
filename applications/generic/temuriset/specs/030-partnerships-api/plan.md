# Implementation Plan: Relationship records confirmed on the same version

**Branch**: `030-partnerships-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/relationships/
├── router.py                     # /partnerships, /{id}, /confirmations, /corrections, /restrictions, /decline, /request-review
├── service/service.py            # propose, correct, confirm, decline, restrict, contest
├── service/consent.py            # effective_fields(version, confirmations, restrictions)
├── service/checksum.py
└── repository/sqlalchemy/        # partnerships, partnership_versions, partnership_confirmations, partnership_restrictions
migrations/versions/0016_relationships.py
```

## Prototype Reference

`proposePartnership`, `requestCorrection`, `confirmPartnership`, `restrictField`, `effectiveFields` in `domain.js`; oracles J05 and AC21.

## Test Plan

AC21, AC52–AC54; checksum binding; restriction append-only; contest hides; property test on consent; isolation.

## Out of Scope

Public profile pages (031, 032).

## Task Outline

1. Consent function with property tests.
2. Versions and checksums.
3. Propose, correct, confirm, decline.
4. Restrictions and contest; contract.

# Implementation Plan: Reports, moderation and privacy requests

**Branch**: `034-moderation-privacy-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/moderation/
├── router.py                     # /reports, /operator/reports, /operator/reports/{id}/actions, /privacy-requests
├── service/reports.py, service/privacy.py, service/retention.py
└── repository/sqlalchemy/        # reports, operator_actions, privacy_requests, retention_policies
migrations/versions/0019_moderation.py
```

## Test Plan

AC64, AC66; suspension effects on discovery; operator scope; isolation of reports.

## Out of Scope

Web (035), legal process.

## Task Outline

1. Reports and operator queue.
2. Suspension effects.
3. Privacy requests with retention policy data.

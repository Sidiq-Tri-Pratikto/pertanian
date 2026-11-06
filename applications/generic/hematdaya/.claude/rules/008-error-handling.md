---
description: Error handling non-negotiables for all code that produces or consumes failures.
alwaysApply: true
trigger: always_on
---
# Error Handling

Applies to all code that produces or consumes failures: routers, services, middleware, workers, tests. Read the full policy `.specify/memory/error-handling.md` (EH-01 to EH-13, X-01 to X-07) and `docs/error-handling/deviation.md` only when you change an error boundary: handlers, middleware, `app/core/errors/`, the public envelope, a resolver, the recorder or sanitizer, or when you execute an `EH-Tnn` subtask.

Non-negotiables:

1. Normalize every failure at the boundary that handles or exposes it. Every error has a stable `code`, a two-clause message (what happened, what to do next), a `reference_id`, and `recovery`. Unexpected failures use the registered fallback and a safe default message.
2. Extend `AppError` in `app/core/errors/base.py` and register codes in `codes.py`. No second base error, code style, or envelope. No `HTTPException` in application code.
3. Translate inconsistent third-party errors through one resolver per integration point: `raise resolve(raw_error) from raw_error`. Never re-raise a specific error as a generic one.
4. Messages and API responses never contain status text, class names, provider jargon, `str(e)`, stack traces, `debug_info`, secrets, or "see the logs".
5. Sanitize before anything reaches `debug_info`, logs, or traces. No PII, credentials, tokens, or confidential data on any surface. Reuse `app/core/errors/sanitize.py`; do not write a second sanitizer.
6. External clients get one envelope `{"error": {"code", "message", "request_id", "recovery"}}`, mapped from internal codes once in `public.py`, with an `INTERNAL_ERROR` fallback.
7. Record each failure once, at the boundary that finally catches it, with `reference_id`, `code`, service, operation, timestamp, and sanitized `debug_info`. The `request_id` returned to the client resolves to that record.
8. Every public error states `recovery.retryable`. Retryable errors state `retry_after_seconds` (plus the `Retry-After` header) and `max_attempts`. Unknown failures and non-idempotent operations are not retryable.
9. A failure inside error handling never hides the original error. Use `emergency_log`.
10. Ship failure-path tests with the change: assert message, code, response, `request_id`, the record, recovery, and that injected fake secret values appear nowhere.

Do not defer error handling to a later task. A PR is blocked only by a finding it introduces or an open P0 on a path it touches; other gaps are reported, not fixed in the same PR.

Lint: CI enforces ruff `E722`, `BLE001`, `S110`, `S112`, `B904`. A boundary that must catch everything says why: `# noqa: BLE001 - <reason>`. Log caught failures through the recorder, not `logger.exception`, whose raw traceback bypasses the sanitizer.

Skills: `implement-error-handling` to build or fix failure behavior; `robust-error-handling` to audit.

---
description: Code review checklist. Use when reviewing a change.
globs: ".github/**"
alwaysApply: false
trigger: model_decision
paths:
  - ".github/**"
---
# Code Review Standards

## Priorities

1. Correctness: does the change do what the spec or issue says?
2. Security and data loss.
3. Contract breaks: API, error codes, migrations.
4. Tests: do they fail if the logic breaks?
5. Simplicity: can code be deleted?

Style belongs to ruff. Do not comment on what it fixes.

## Flag

- Hardcoded values that should be settings.
- Missing input validation at trust boundaries.
- Blocking I/O in async code.
- Inefficient queries, unbounded lists, missing pagination.
- Unjustified new dependencies or abstractions with one implementation.
- Missing or inadequate tests.
- Security issues: injection, broken authorization, secrets in logs.

## Error handling

For new or changed code, flag:

- **Missing handling:** a failure path with no typed error, an untyped raise reaching a consumer, a swallowed error, or a generic re-raise that drops the type or cause.
- **Unsafe data:** status text, class names, provider jargon, `debug_info`, stack traces, `str(e)`, or secrets in messages, responses, logs, or traces.
- **Second family:** a new base exception or envelope beside `app/core/errors/`.
- **Missing record:** a system failure not recorded exactly once at the boundary.
- **Bad codes:** unregistered, repurposed, or internal codes sent to clients.
- **Missing reference ID:** no `request_id`, or one that does not match the recorded `reference_id`.
- **Recovery gaps:** no `recovery.retryable`, missing `Retry-After`, unbounded retries, or retries of non-idempotent operations.
- **Missing failure tests:** see `003-testing`.

Flag gaps the PR did not introduce as notes, not blockers, unless they are P0 on a touched path.

## Feedback

Be specific, cite the rule or spec, and suggest the fix. Separate blockers from suggestions.

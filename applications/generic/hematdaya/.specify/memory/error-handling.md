# Error Handling Constitution

Policy version 1.0.

This file states the rules every adopting project follows. It contains no audit procedure and no priority labels; auditing lives in the `robust-error-handling` skill.

**MUST / MUST NOT** are mandatory outcomes. **SHOULD** is a recommended pattern; an equivalent design is acceptable when the deviation, its reason, and the evidence that the outcome still holds are documented. A deviation never waives actionable messages, secure diagnostics, automation support, automated testing, ownership, or release verification.

## Contents

- [Short version](#short-version)
- [Adoption](#adoption)
- [Canonical fields](#canonical-fields)
- [Rules EH-01 to EH-13](#rules)
- [Reference shapes](#reference-shapes)
- [Error catalog template](#error-catalog-template)
- [Completeness test](#completeness-test)
- [Additional safeguards (X-01 to X-07)](#additional-safeguards)

## Short version

This block is the Error Handling section of the constitution:

```markdown
### Error Handling (Non-negotiable)

Every failure serves three audiences and each gets only its own content: the user gets a two-clause
message (what happened, what to do next); agents and automation get a stable `code`, a documented
`debug_info` schema, and `recovery` guidance; engineers get a `reference_id` that resolves to exactly
one sanitized record in centralized logging and monitoring.

- Normalize every failure at the boundary that handles or exposes it; unexpected failures use a
  registered fallback code and a safe, actionable default message.
- Translate inconsistent third-party errors through one resolver per integration point; preserve the cause.
- Never put status codes, class names, provider jargon, debug data, or secrets in a user message or API response.
- Sanitize before anything reaches `debug_info`, logs, traces, or monitoring.
- External clients get one versioned envelope `{error: {code, message, request_id, recovery}}`
  mapped from internal codes in one place.
- Every public error states `recovery.retryable`; retryable errors state wait time and max attempts.
- A failure inside error handling must never hide the original error.
- Failure paths are tested end to end (message, code, response, reference ID, record, privacy with
  fake secrets, recovery); release only with that evidence or an approved PR exception.

Full rules: `.specify/memory/error-handling.md` (EH-01 to EH-13, X-01 to X-07).
```

## Adoption

1. This file lives at `.specify/memory/error-handling.md`. Project-specific mappings (base error, code prefix, envelope, sanitizer, surfaces) live in `docs/error-handling/deviation.md`.
2. The always-on rule `.claude/rules/008-error-handling.md` carries the non-negotiables. Read this full file only when adding or changing exception handlers, error classes or codes, the public envelope, the recorder, retries, or failure-path tests.
3. New and changed code follows these rules immediately. A PR is blocked only by a finding it introduces or by an open P0 (as rated by the `robust-error-handling` audit) on a path it touches. Existing production code is audited, owned, and remediated through its own subtasks. Do not rewrite unrelated legacy code during a feature change; report the gap instead.
4. **Legacy baseline exception.** When the first audit of a service is committed, the accountable manager records one approved X-02 exception that covers every open P1/P2 finding in that audit, with an expiry date and a burn-down tracked in the audit file. Releases may proceed under it; open P0s are never covered. New findings after that date are not covered.
5. Instructions do not enforce themselves. Enforcement comes from code, failure-path tests, PR/CI checks, and human review (EH-13).

## Canonical fields

Use these names unless the project already publishes an equivalent contract; then document the mapping.

| Field | Where | Meaning |
| --- | --- | --- |
| `code` | internal error | Stable, scoped, machine-readable failure **type**, e.g. `APP-PROVIDER-RATE-LIMIT`. Independent of class name and message. Never repurposed. |
| `default_message` / `message` | internal error, public envelope | Two clauses: what happened, then what to do next. Safe for any user surface. |
| `debug_info.error_type` | internal error | Required. Class name of the original raw error. |
| `debug_info.original_message` | internal error | Required. Sanitized text of the original raw error. |
| `debug_info.traceback` | internal error | Optional. Sanitized; only when the raw error has one. |
| `debug_info.upstream_request_id` | internal error | Optional. The `request_id` returned by an internal upstream service whose failure caused this one (X-07). |
| `recovery.retryable` | internal error, public envelope | Required boolean on every public error. |
| `recovery.retry_after_seconds` | internal error, public envelope | Optional. Wait before retrying; also sent as the `Retry-After` HTTP header. |
| `recovery.max_attempts` | internal error, public envelope | Optional. Total attempts including the first; minimum 1. |
| `recovery.escalate_when` | internal error only | Optional. Condition that needs a human. Never sent to external clients. |
| `reference_id` | internal error, diagnostic record | One failure **occurrence**. Assigned once on construction; preserved through wrapping. At least 64 bits of randomness, e.g. `ref_` + `uuid4().hex`; short IDs collide and break "exactly one record". |
| `error.request_id` | public envelope | The same value as `reference_id`, returned to the client. |
| `error.code` | public envelope | Public, documented code, e.g. `RATE_LIMITED`. Never the internal code. |

## Rules

### EH-01 - Normalize failures at boundaries

- Every handled or externally visible failure MUST produce a stable nonempty code, a complete safe message, and a reference ID; when it reaches a client it also carries `recovery.retryable` (EH-09). Retry timing and `escalate_when` are documented only where a retry or escalation actually exists; a validation failure is simply `retryable: false`. Unexpected failures MUST use a registered fallback with the same guarantees; a missing code or incomplete message is never the fallback.
- Public boundaries MUST normalize failures from application code, framework validation, authentication/authorization, external dependencies, and uncaught exceptions. Background workers and scheduled jobs MUST normalize terminal failures even without an HTTP response.
- SHOULD use one error family per library/application: a shared base and concrete typed errors. Raw native errors may exist internally only if they are normalized before reaching a consumer.
- MUST NOT leave some user-reachable paths untyped (`raise ValueError("something went wrong")`), swallow a failure, or return a misleading success.

### EH-02 - Centralize inconsistent dependency translation

- SHOULD route third-party errors with inconsistent shapes through one resolver per integration point (an LM provider SDK, an external ranking API, a moderation service). The resolver returns the typed error; the caller raises it and chains the cause: `raise resolve(raw_error) from raw_error`.
- Resolution order SHOULD prefer structured signals: response detail code, then message pattern, then HTTP status, then exception name, then a safe fallback. Message-pattern matching MUST be centralized, tested, and backed by the fallback.
- Errors from the module's own logic (validation, invalid state) are raised as typed errors directly; no resolver is needed.
- MUST NOT raise deep in feature code past the resolver without a documented reason, or catch a specific error only to re-raise a generic `RuntimeError` / `Exception` / `Error`.

### EH-03 - Actionable human messages

- Every default and public message MUST use the two-clause template: what happened, then the next step. Example: "The input size is too large. Please reduce the input size and try again."
- Messages MUST NOT contain HTTP status text, provider or internal jargon, internal codes, class names, stack traces, hostnames, or debug data (`"429 Too Many Requests"`, `"RateLimitError: rate_limit_exceeded"`).
- Messages MUST NOT point at things the user cannot see ("see debug info", "check the logs"). If support is the next step, show the reference ID.
- Default rendering (`__str__`, `getMessage()`, `Error.message`, UI toasts) MUST be the message only. Debug output requires an explicit call such as `verbose()`.

### EH-04 - Stable error codes and one catalog

- Every error type MUST have a stable, library-scoped code independent of class name and message. Base and fallback codes are registered before publication.
- Published internal and public codes MUST NOT be repurposed. Public codes are deprecated with notice, never silently removed.
- Every error MUST be listed in one catalog consumers can read without opening source (see the template below).
- Consumers MUST branch on code and documented fields, never on message text. A class-name prefix in the message is not a code.

### EH-05 - Structured, preserved diagnostics

- `debug_info` MUST follow one documented minimum schema across the library: `error_type` and sanitized `original_message` always; sanitized `traceback` optional. Keys MUST NOT vary by raise path.
- When an app wraps an SDK/library error in its own error model, it MUST keep the original type (chained cause), original code, `debug_info`, and `reference_id` alongside the app code.
- An app or library MUST NOT grow a second, incompatible exception family beside the first.

### EH-06 - Protect sensitive data on every surface

- Messages, API responses, `debug_info`, logs, traces, and observability data MUST NOT contain PII, credentials, API keys, tokens, prompts, or confidential content.
- Redact or exclude sensitive values **before** they reach `debug_info` or any sink; upstream SDK errors and HTTP bodies can contain any of them.
- Serialize explicitly selected safe fields; never serialize an internal exception wholesale.
- If sanitization fails, emit a minimal safe record, never the original payload.

### EH-07 - Stable public error contract

- Every external error boundary MUST return one documented, versioned envelope, decoupled from internal codes, with the same shape on every endpoint and team.
- Internal codes MUST map to public codes explicitly in one place, with a registered `INTERNAL_ERROR` fallback.
- Public responses MUST NOT contain the internal code, exception class name, SDK message, `debug_info`, or `escalate_when`.
- `request_id` (one occurrence) MUST be distinct from `code` (one failure type).

### EH-08 - Centralized logging, monitoring, and reference IDs

- Every system failure MUST reach centralized logging and monitoring. A local log, a print, or the exception object alone is not enough.
- Record once, at the boundary that finally catches the failure; raise sites stay unaware of logging. Wrappers and middleware MUST NOT create duplicate records.
- The record MUST contain `reference_id`, internal `code`, service, operation, timestamp, and sanitized `debug_info`.
- The reference ID returned to the user MUST resolve to exactly one diagnostic record. Never return an ID that was not recorded.
- Expected client failures (4xx) are still recorded, at info or warning level in the structured logs, because they return a `request_id`. Only system failures (5xx, terminal worker failures) go to the error tracker, grouped by `code`, never into one generic issue.

### EH-09 - Recovery and retry guidance

- Every public error MUST include `recovery.retryable`. Retryable errors document `retry_after_seconds` and `max_attempts`; escalating errors document `escalate_when` internally and give the user a safe next step.
- When `retry_after_seconds` is exposed over HTTP, send a matching `Retry-After` header.
- Clients and agents MUST stop when `retryable` is false or attempts reach `max_attempts`, then surface the message and reference ID to a human.
- Unknown failures default to `retryable: false`.

### EH-10 - Error handling must survive its own failure

- Logging failure, unavailable monitoring, full storage, or a failing handler MUST NOT hide the original error or prevent its safe response.
- Provide a minimal emergency path (for example `emergency_log(reference_id, code)`) that does not recurse into the failing handler.

### EH-11 - Test the complete failure lifecycle

- Automated tests and CI MUST deliberately create timeouts, authentication failures, rate limits, unavailable dependencies, malformed responses, and unexpected exceptions where applicable.
- Each failure test MUST verify the message, error code, API response, reference ID, centralized diagnostic record, privacy protection, and recovery behavior. Asserting only that something raised is not enough.
- Inject known fake secret **values** (API key, bearer token, email, prompt text) and assert none appear in messages, responses, logs, or records. Checking that a key name is absent is not enough.
- Test failures of error handling itself (logging failure, unavailable observability, full storage, failing handler).
- A resolver-only test is not a full-chain test. Full-chain tests call the public entry point and check the response and the diagnostic record.
- Add a regression test for every reported error defect. Run resilience/chaos tests in staging first; consider production only after staging results are reviewed.

### EH-12 - Clear ownership

- Every identified issue MUST have an assigned engineer and accountable manager, including issues spanning teams. Unclear ownership is a blocker, not a reason to leave it unassigned.
- Document the review scope (systems, components, failure paths). The manager submits scope, completed fixes, and test results.
- Escalate blockers immediately with impact and what is needed. Never report a fix complete without test evidence or hide unresolved issues.

### EH-13 - Release evidence through existing PR and CI

- Error handling is a mandatory release requirement. Do not release with an open error-handling finding: fix it, or record an approved exception (X-02) on the PR. Pre-existing findings are covered by the legacy baseline exception until it expires (see Adoption). Merging a PR is gated more narrowly: by findings the PR introduces and by open P0s on paths it touches.
- Evidence comes from existing tools, not a separate checklist document. Each project names its tool for: failure tests (CI), static analysis, dependency scanning, guideline review, the PR template, and human approval.
- AI PR review checks new or changed code for missing error handling, privacy risks, missing logging, incorrect codes, missing reference IDs, and missing failure tests. A human reviewer stays accountable.
- A green CI run alone is not proof; confirm the failure-path tests exist.
- Add these lines to the Author Checklist in `.github/pull_request_template.md`:

```markdown
- [ ] Failure-path tests added or updated (timeout, auth, rate limit, dependency down, malformed response, unexpected exception)
- [ ] No sensitive data in messages, API responses, logs, or diagnostic records
- [ ] New or changed error codes are registered and mapped to a public code
- [ ] Retry and escalation guidance documented where it applies
```

## Reference shapes

Language-neutral shapes (Python syntax). Names such as `APP-UNKNOWN`, `BaseError`, and `service="example-service"` are examples, not values to copy: a project keeps its own published code prefix, base error, service name, and envelope, and documents the mapping to the canonical fields. Idiomatic Python is in the `robust-error-handling` skill's `references/python.md`.

```python
class DebugInfo(TypedDict):
    error_type: str                  # required
    original_message: str            # required, sanitized
    traceback: NotRequired[str]      # optional, sanitized

class RecoveryInfo(TypedDict):
    retryable: bool                         # required
    retry_after_seconds: NotRequired[int]
    max_attempts: NotRequired[int]
    escalate_when: NotRequired[str]         # internal only

class BaseError(Exception):
    code: str = "APP-UNKNOWN"              # registered fallback
    default_message: str = (
        "We could not complete the operation. "
        "Contact support and provide the reference ID shown with this error."
    )
    recovery: RecoveryInfo = {"retryable": False}

    def __init__(self, message=None, *, error=None, reference_id=None, debug_info=None):
        self.message = message or self.default_message
        self.reference_id = reference_id or f"ref_{uuid4().hex}"     # once, on construction
        self.debug_info = debug_info or build_debug_info(error)      # sanitized
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message                  # message only

    def verbose(self) -> str:
        return f"{self.message}\nDebug Info:\n{self.debug_info}"

class ProviderRateLimitError(BaseInvokerError):
    code = "APP-PROVIDER-RATE-LIMIT"
    default_message = "The request was rate limited. Please try again later."
    recovery = {"retryable": True, "retry_after_seconds": 30, "max_attempts": 3,
                "escalate_when": "still failing after max_attempts"}

# Central resolver: returns, does not raise.
try:
    provider.call(prompt)
except Exception as raw_error:
    raise resolve(raw_error) from raw_error

# Public contract: one map, one fallback, nothing internal.
PUBLIC_ERROR_BY_APP_CODE = {
    "APP-PROVIDER-RATE-LIMIT": PublicError("RATE_LIMITED", 429,
        "The request was rate limited. Please try again later.",
        recovery={"retryable": True, "retry_after_seconds": 30, "max_attempts": 3}),
}
FALLBACK_PUBLIC_ERROR = PublicError("INTERNAL_ERROR", 500,
    "We could not complete the request. Contact support and provide the reference ID.",
    recovery={"retryable": False})

# Boundary handler: the one place that records; survives its own failure.
@app.exception_handler(AppError)
def handle_app_error(request, app_error):
    public = PUBLIC_ERROR_BY_APP_CODE.get(app_error.code, FALLBACK_PUBLIC_ERROR)
    try:
        record_system_failure(reference_id=app_error.reference_id, code=app_error.code,
                              service="example-service", operation=request.url.path,
                              timestamp=utcnow().isoformat(),
                              debug_info=sanitize(app_error.debug_info))
    except Exception:
        emergency_log(reference_id=app_error.reference_id, code=app_error.code)
    headers = {}
    if "retry_after_seconds" in public.recovery:
        headers["Retry-After"] = str(public.recovery["retry_after_seconds"])
    return JSONResponse(status_code=public.http_status, headers=headers, content={
        "error": {"code": public.code, "message": public.message,
                  "request_id": app_error.reference_id, "recovery": public.recovery}})
```

Public response for that failure:

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "The request was rate limited. Please try again later.",
    "request_id": "ref_3f9a1c2e8b7d4e6fa0c1d2e3f4a5b6c7",
    "recovery": { "retryable": true, "retry_after_seconds": 30, "max_attempts": 3 }
  }
}
```

The 30 seconds and 3 attempts are examples, not defaults. Keep code, message, HTTP status, recovery, and headers consistent in one definition per error.

## Error catalog template

Keep one catalog per library/service in docs (GitBook, `docs/errors.md`, or equivalent), not only in source:

| Internal code | Public code | HTTP status | Default message | Trigger | retryable | retry_after_seconds | max_attempts | escalate_when | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `APP-PROVIDER-RATE-LIMIT` | `RATE_LIMITED` | 429 | The request was rate limited. Please try again later. | Provider returns 429 or a rate-limit error code | true | 30 | 3 | still failing after max_attempts | team / owner |
| `APP-UNKNOWN` | `INTERNAL_ERROR` | 500 | We could not complete the request. Contact support and provide the reference ID. | Any unrecognized failure | false | - | - | always | team / owner |

## Completeness test

Error handling is complete for a scope only when every answer is yes:

1. Can the user understand what failed and what to do next?
2. Can an automated consumer identify the failure using a stable code and documented structured fields?
3. Can an authorized engineer use the reference ID to locate sufficient sanitized diagnostic context in centralized logging and monitoring?
4. Do automated tests verify the message, failure response, diagnostic record, and sensitive-data protection?
5. Does each identified issue have an assigned engineer and accountable manager?
6. Has the manager submitted the review scope, completed fixes, and test results?
7. Is retry and escalation guidance documented for every retryable or escalating failure?

## Additional safeguards

Safeguards beyond the core rules. Apply them where the mechanism exists in the project.

### X-01 - Replay-safe, bounded retries

Retry eligibility depends on operation semantics, not status alone: a timeout can happen after a write commits. Retry side effects only with idempotency keys, deduplication, or verified unapplied state. Enforce time and attempt budgets, backoff with jitter for repeated transient failures, cancellation, and protection against retries multiplying across layers. An upstream provider credential failure is not evidence that the end user's credentials are wrong; map it using application context. Sources: [AWS Builders' Library: timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/), [making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).

### X-02 - Approved exception record

An approved PR exception names the rule, risk, reason, scope, engineer and manager, approver, expiry or review date, mitigation, and remediation plan. An alternative architecture with equivalent outcomes is a documented deviation, not an exception.

### X-03 - Safe, proportionate logging

Use structured events. Encode untrusted CR/LF and delimiters, bound event size and depth, and never log raw exception objects that bypass redaction through causes or automatic traceback capture. Protect diagnostic storage with least privilege and retention limits. Log security-relevant auth failures with safe context; ordinary validation rejections are not system-error incidents. Source: [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html), [OWASP Error Handling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html).

### X-04 - Correct transport semantics and compatible contracts

Use HTTP status and headers that describe the failure ([RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)); never turn REST failures into 200 responses. An existing [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) contract is acceptable: keep `application/problem+json` and add code, reference, and recovery as documented extensions. GraphQL keeps its standard `errors` array with public fields in `extensions` and may return partial data ([GraphQL response rules](https://spec.graphql.org/September2025/#sec-Response)). Do not silently replace a published contract.

### X-05 - Cancellation, cleanup, streams, and queues

Do not convert cancellation or shutdown signals into retryable failures or swallow them in broad catches; in Python re-raise `asyncio.CancelledError` after cleanup ([Python task cancellation](https://docs.python.org/3/library/asyncio-task.html#task-cancellation)). Cleanup errors must not replace the primary failure. After stream headers are committed, use a documented error event or close; never send a second response. Queue jobs distinguish retry from terminal failure, use dead-letter handling, and never acknowledge failed work as success.

### X-06 - Realistic record uniqueness and safe correlation

"Exactly one record" means one canonical logical record, not exactly-once transport. Deduplicate at the sink by occurrence key when delivery can replay; keep retry-attempt events separate from the terminal record. Treat inbound correlation IDs as untrusted: validate, bound, and keep them separate from the generated occurrence ID. A reference ID is never an authorization credential; diagnostic lookup enforces user/tenant access.

### X-07 - Internal service-to-service contracts

An API called by another internal service (for example one application in this repository calling another) is a public error boundary: EH-07 and EH-09 apply in full, and a change to its envelope, codes, or status is a breaking change for the caller.

- Migrate the consumer first. The caller learns to parse both the old and the new shape in its own PR before the producer changes its responses.
- The caller translates the upstream envelope through its resolver into its own typed error. It never copies the upstream body or message text into its own message, logs, or response.
- Carry correlation across the hop: send `X-Request-ID` on outbound calls, and store the upstream `error.request_id` as `debug_info.upstream_request_id` so an engineer can follow one failure through every service.
- Retries happen in one layer only (X-01). When the upstream returns `recovery`, the caller honors `retryable`, `retry_after_seconds`, and `max_attempts` instead of its own defaults.

# Check catalog and priority rubric

The constitution's rules (EH-01 to EH-13, X-01 to X-07) are the policy. The checks below are the concrete things an audit looks for; each maps to one or more EH rules. Cite both in findings, for example `EH-06 / D4`. Check IDs are stable.

Group letters:

- **S** taxonomy and structure
- **M** message content
- **D** debug / diagnostic content
- **C** consumer / app wrapping
- **P** client / API error contract
- **L** centralized logging, monitoring, and reference IDs
- **R** recovery, retry, and resilience of error handling itself
- **T** testing and prevention
- **G** release evidence

Ownership (EH-12) is enforced by the report (engineer and accountable manager per finding and subtask, review scope, manager submission), not by a check ID.

Retired IDs: D3 → L2/L4, D8 → L1. Map old IDs when reading an older report.

The separation test (SKILL.md) decides mixed-concern findings: name the human clause, the agent field, and the producer. A finding that mixes them cites the check for the part that leaked.

**Outcome vs pattern.** Each check states a mandatory outcome. A shared base class, a resolver, or a specific helper is the recommended way to meet it. A different architecture passes when the report records a deviation with its reason and the evidence that the outcome still holds. A deviation never waives M (actionable messages), D4 (secure diagnostics), D12/P1 (codes and structure for automation), L, R1, T, G, or ownership.

## Priority rubric (P0 / P1 / P2)

This rubric exists only for audits; the constitution has no priority labels. Every finding, subtask, and verification-queue item gets exactly one priority with a one-line rationale based on reachability, impact, likelihood, and scope. There is no P3 and no unprioritized "nice to have".

| Priority | Timing | Meaning |
|---|---|---|
| P0 | Immediate containment and remediation; blocks the affected release. | A reachable path exposes secrets, credentials, tokens, PII, or prompts to users, clients, logs, traces, or `debug_info`; a reachable route or job skips its authentication or authorization check, so a failure that should be rejected succeeds; a failure silently corrupts or loses data, or reports success; an unsafe retry can duplicate an irreversible effect (payment, message send, committed write); an error-handler failure takes down a critical service or makes failures invisible. |
| P1 | Fix before the next release of the affected component. | A consumer gets an untyped or generic error, no stable code, or `debug_info` / class name / internal code on the wire. A system failure has no reference ID, no centralized record, or an ID that does not resolve. Wrapping drops the cause, code, `debug_info`, or `reference_id`. The envelope differs across endpoints. A public error has no `recovery.retryable`; retries are unbounded. A handler failure masks the original error. A critical surface has no full-chain or fake-secret test. A missing baseline piece blocks any of these. |
| P2 | Scheduled with an owner and a bounded plan. | Partial gaps with no evidence of critical harm: a message lacks its next step; `debug_info` keys differ by path; a resolver is bypassed without a note; a record misses one field; the catalog or runbook is incomplete; a lint gate is missing while the code is currently clean; `print` in non-entrypoint code; PR checklist lines are missing; duplicated mappings that currently behave correctly. |

Adjustments:

- Raise P2 to P1 when the surface is public (customer API, SDK, UI, or an API another internal service calls, X-07). Lower P1 to P2 for internal-only tooling with no consumer outside the process. This adjustment never creates or removes a P0; P0 requires P0-type harm with a shown path.
- Order inside a priority by blast radius: number of consumers (services, clients) affected, then number of routes or jobs, then how often the path fails. List findings in that order so "start here" is deterministic across runs.
- An auth/authorization bypass found during the audit is reported here (P0) and also flagged to the user for a security review; the error-handling fix is only the containment.
- A style issue is never P0. A missing test is not automatically P1. Uncertainty is not proof of safety: an unconfirmed P0-type risk goes to the verification queue as provisional P0 with the exact check needed.
- Confidence (high / medium / low) is reported separately and never changes the priority.
- Priority is not a release waiver. Under EH-13 every open finding, P2 included, needs a fix or an approved exception recorded on the PR before release.

## S: Taxonomy and structure

| ID | EH | Check | Typical evidence |
|---|---|---|---|
| S1 | EH-01 | Every user-visible failure, including an unexpected one, is normalized at the boundary that handles or exposes it into a reviewed message and the consistent error shape. Errors the module raises subclass one module base (and a shared ancestor when the platform has one). A raw `ValueError`, `RuntimeException`, `Error`, or equivalent that can reach a consumer fails. | `raise ValueError("something went wrong")` on a path a caller can hit; a boundary with no catch-all translation |
| S2 | EH-02 | A third-party integration point whose errors arrive in inconsistent shapes goes through one resolver. Own-logic failures (validation, illegal state) are typed raises and do not need a resolver. A bypass at a third-party boundary carries a comment that states why. | several `except ProviderX` blocks each raising a different ad-hoc type; or one generic type for timeout, auth, and validation |
| S3 | EH-02 | A catch keeps the specific failure. Re-raising as a bare `RuntimeError`, `Exception`, or `Error` with one shared message fails. Translate through the resolver or a typed subclass, and chain the cause. | `except (Timeout, Auth, Validation): raise RuntimeError("operation failed")` |
| S4 | EH-01, EH-05 | One family per module: the same base and the same fields (`code`, message, `debug_info`, `recovery`, `reference_id`). A second shape beside it fails. | a `BaseError` hierarchy next to a plain `Exception` subclass with no `debug_info`, or a type whose fields are never set |
| S5 | EH-04 | Callers branch on type or `code`, never on message text. | `if "not found" in str(e)`, `err.message.includes(...)`, `e.getMessage().contains(...)` |
| S6 | EH-01, EH-04 | Every concrete error has a stable code and a complete default message. A base default that can reach a user is safe and actionable, and the base fallback code is registered. A missing code or incomplete message is never the fallback. | base `code = None`; base `default_message = "An error occurred."` reaching a user via the catch-all handler |

## M: Message content

| ID | EH | Check | Typical evidence |
|---|---|---|---|
| M1 | EH-03 | The user-facing message is two clauses: what happened, then what to do next. It stands alone. Generic text, a missing next step, or a pointer at something the reader cannot open fails. | `"Something went wrong"`, `"Skill operation failed."`, `"See debug info for more details."`, `"Check the logs."` |
| M2 | EH-03 | The message contains no HTTP status line, provider or internal jargon, exception class name, stack trace, SQL, file path, hostname, upstream body, or internal identifier used as the sentence. | `default_message = "429 Too Many Requests"`, `detail=str(e)`, `"[OpenAILMInvoker] Authorization failed"` |
| M3 | EH-07, X-04 | Transport status matches the failure class: client faults 4xx, server faults 5xx, dependency outage 502/503/504; CLI exits non-zero. Status is the transport field, not the message. | `200` with an error body on REST; `sys.exit(0)` inside `except` |
| M4 | EH-03 | A validation failure names each offending field and the accepted form, in one response. | a single "invalid request" for a multi-field form |
| M5 | EH-03, EH-04 | Each error type has one fixed default message. Call sites do not assemble the user string from class names, status codes, or `str(error)`. | `f"[{type(e).__name__}] {msg}"` shown to users; tests or branches that compare message strings |

## D: Debug / diagnostic content

| ID | EH | Check | Typical evidence |
|---|---|---|---|
| D1 | EH-01 | A caught error is handled, re-raised, or logged with context. An empty catch is valid only for a named, expected, harmless condition, with a comment. | `except: pass`, `catch (e) {}`, `.catch(() => {})`, `catch` returning `null` with no log |
| D2 | EH-05 | The cause chain survives (`raise X from e`, `cause`, a constructor that takes the raw error). `debug_info.error_type` and `original_message` come from that raw error. | `raise X(...) from None`, `new RuntimeException(e.getMessage())`, `throw new Error("x")` without `cause` |
| D4 | EH-06 | `debug_info`, logs, and traces are sanitized before they are stored or emitted. Redaction is one helper or logger filter. API keys, tokens, passwords, cookies, auth headers, credentials, request payloads, full bodies, prompts, and personal data stay out. A sanitizer failure emits a minimal safe record. | `logger.info(headers)`, `original_message` set to the raw upstream body, `console.log(req.body)` |
| D5 | EH-08 | `print` / `System.out` / `console.*` / `printStackTrace()` is not the diagnostic path. | `e.printStackTrace()`, `print(e)`, `console.error(err)` in server code |
| D6 | EH-01, X-05 | Catch the narrowest type the code handles. A broad catch belongs at the resolver or the boundary handler. Cancellation is not trapped: `BaseException` / bare `except` / swallowed `CancelledError` in Python, `InterruptedException` without re-interrupt in Java, `AbortError` treated as a product failure in TS. | `except Exception` mid-service, `catch (Throwable t)`, empty `InterruptedException` catch |
| D7 | EH-01 | Every promise, future, and task is awaited or has a handler. Process-level handlers log unhandled rejections. | floating promise, dropped `asyncio.create_task`, `CompletableFuture` never joined |
| D9 | X-05 | Failure paths release resources and roll back partial state; cleanup errors do not replace the primary failure. | `close()` outside `finally`, missing `with` / try-with-resources |
| D10 | EH-05 | Every error exposes `debug_info` with the documented minimum schema: `error_type` and `original_message` always; `traceback` only when one exists. A path that emits a different key set fails. | `{"status_code": 500, "response_body": "..."}` on one path and `{"error_type": ...}` on another |
| D11 | EH-03 | Default rendering is the message only (`__str__`, `getMessage()`, `Error.message`). `debug_info` comes only from an explicit verbose/debug method. | `__str__` concatenates the traceback; a toast built from `verbose()` |
| D12 | EH-04 | Every error type has a stable library-scoped `code`, independent of class name and message; it is the error tracker's grouping key. A published code is not repurposed. | no `code` attribute; `message = f"[{class_name}] {text}"` used as the grouping key |
| D13 | EH-04 | Every error class is listed in one catalog a consumer can open without reading source: `code`, default message, trigger, recovery. | the only list is `exceptions.py` |

## C: Consumer / app

| ID | EH | Check | Typical evidence |
|---|---|---|---|
| C1 | EH-05 | An app that wraps a library error keeps the original type (chained cause), the original `code`, `debug_info`, and `reference_id` on the app error, so the boundary that records it has the full trail. | `raise AppError("failed")` with no `from`; app error built without the SDK `reference_id` or `debug_info` |
| C2 | EH-05 | The app's own errors share one base and the same fields. A second family in the same app fails. | `FeatureDisabledError(BaseError)` beside `AIPError(Exception)` with a different constructor |

## P: Client / API error contract

| ID | EH | Check | Typical evidence |
|---|---|---|---|
| P1 | EH-07 | Every client-facing error uses one stable, versioned envelope: `error.code`, `error.message`, `error.request_id`, `error.recovery`. An existing RFC 9457 or GraphQL contract with equivalent fields passes. | `{"error": str(sdk_error)}`, a bare string body, a different object on one route |
| P2 | EH-07 | Internal code, class name, SDK message, `debug_info`, and `escalate_when` are mapped, not copied. The map from internal to public code lives in one place and has an `INTERNAL_ERROR` fallback. | handler returns `exc.code` or `exc.debug_info`; mapping dicts duplicated per router |
| P3 | EH-07, EH-08 | `request_id` identifies this occurrence; `code` identifies the kind. Both are present and neither is used as the other. | code reused as the correlation ID; request ID omitted on 5xx |
| P4 | EH-04 | A documented public code keeps its meaning. Removing or reusing it is a deprecation with notice, recorded as a breaking change. | a published `RATE_LIMITED` now returned for auth failures |
| P5 | EH-07 | The envelope shape is the same on every endpoint and every team's service, including framework validation and auth errors. | `/v1/invoices` returns `error.message` and `/v1/jobs` returns `detail`; framework 422 bypasses the envelope |
| P6 | EH-04 | Public codes are listed in one consumer-facing catalog (code, message, trigger, recovery) outside the handler source. | the only list is the handler's mapping dict |
| P7 | X-07 | An internal service call is treated as a public boundary. The caller parses the upstream envelope through its resolver, never copies the upstream body or message into its own message, logs, or response, sends `X-Request-ID`, keeps the upstream `request_id` as `debug_info.upstream_request_id`, and honors upstream `recovery`. A producer envelope change ships only after the consumer parses both shapes. | `logger.warning(f"... {response.text}")`; `message=response.text`; caller reads `error_data["details"]` that the producer is about to rename |

## L: Centralized logging, monitoring, and reference IDs

| ID | EH | Check | Typical evidence |
|---|---|---|---|
| L1 | EH-08 | Every system failure is recorded once, in centralized logging and monitoring (structured sink plus the error tracker for unexpected failures), by the boundary that finally catches it. The raise site stays unaware of logging. Expected client errors record at warning or info. Tracker events are grouped by `code`. | the same exception logged in repository, service, and controller; a worker that logs only to a local file; no tracker hook on the catch-all handler; every unknown failure sent as one static `capture_message` event |
| L2 | EH-08 | A reference ID with at least 64 bits of randomness is assigned once, on error construction; a wrapping app error carries the original value over (C1). The same value appears in the centralized record and in the response, in its own field, never only inside the sentence. | response with no `request_id`; record and response carrying different IDs |
| L3 | EH-08 | The record has `reference_id`, `code`, `service`, `operation`, `timestamp`, and sanitized `debug_info` (D4). Operation is a route template or safe name, not a raw URL with sensitive query parameters. | a log line with only `str(e)`; no operation or service name |
| L4 | EH-08 | A reference ID shown to a user resolves to a diagnostic record. An ID minted for the response but never recorded, or recorded where engineers cannot query, fails. | `uuid4()` generated in the handler and returned without being logged |

## R: Recovery, retry, and resilience

| ID | EH | Check | Typical evidence |
|---|---|---|---|
| R1 | EH-09 | Every public error carries `recovery.retryable`. Unknown failures default to `false`. | envelope without `recovery`; fallback mapped as retryable |
| R2 | EH-09 | A retryable error documents `retry_after_seconds` and `max_attempts`; when exposed over HTTP, the `Retry-After` header matches. | 429 with no `Retry-After`; header and body disagree |
| R3 | EH-09 | Clients, SDKs, and agents stop retrying when `retryable` is false or attempts reach `max_attempts`, then surface the message and reference ID. Retry loops are bounded in attempts and time. | `while True: retry`; tenacity/retry config with no stop; frontend auto-resubmits forever |
| R4 | EH-09, X-01 | Retry eligibility depends on operation semantics. Side-effecting operations retry only with idempotency or deduplication; retries do not multiply across layers. | client, SDK, and gateway each retry 3 times; timeout on a payment POST retried blindly |
| R5 | EH-10 | A failure in the logger, monitoring, storage, sanitizer, serializer, or handler does not hide the original error or its safe response. A bounded, non-recursive emergency path keeps the code and reference ID. | `record_system_failure()` call with no `try`; handler that raises while serializing `debug_info` |
| R6 | EH-07, EH-09 | `escalate_when` and other internal recovery fields stay internal; the public message gives a safe human next step. | `escalate_when` serialized into the client envelope |

## T: Testing and prevention

| ID | EH | Check | Typical evidence |
|---|---|---|---|
| T1 | EH-11 | Each surface and each P0/P1 fix has an automated failure-path test covering the expected errors and the unexpected-failure fallback (non-empty code, message, and reference ID on the fallback). | handler tests cover only success responses; no test drives the catch-all handler |
| T2 | EH-11 | Failure tests assert the contract, not only that something failed: transport status, code, exact message, `request_id`, `recovery`, body free of stack/`debug_info`/secrets, and the centralized record (level, internal code, same reference ID, sanitized `debug_info`). | `pytest.raises(Exception)`, `assertThrows(Exception.class)`, `toThrow()` with no argument |
| T3 | EH-11, EH-13 | CI gates the patterns this catalog forbids: Python ruff `E722,BLE001,S110,S112,B904,TRY400,T201`; Java PMD `EmptyCatchBlock, AvoidCatchingGenericException, PreserveStackTrace, AvoidPrintStackTrace` or Error Prone `CatchAndPrintStackTrace`; TS ESLint `no-empty`, `@typescript-eslint/no-floating-promises`, `@typescript-eslint/only-throw-error`, `prefer-promise-reject-errors`, `no-console`. | lint config without these rules |
| T4 | EH-11 | Each external dependency at a surface has tests for timeout, auth failure, rate limit, unavailable dependency, malformed response, and unexpected exception, asserting the resolver branch (the typed error). | happy-path mocks only |
| T5 | EH-08, EH-11 | A full-chain test proves correlation: the reference ID returned by the public entry point finds exactly one record with the expected internal code. A resolver-only test is not full-chain. | no test reads the record back by the returned ID |
| T6 | EH-11 | Each reported defect about a missing or unclear error has a regression test. | a fixed bug ticket with no test asserting the corrected message or code |
| T7 | EH-06, EH-11 | Privacy is tested with known fake secret **values** (API key, bearer token, email, prompt text) injected into upstream errors and inputs, asserting absence from messages, response bytes, logs, and records. Checking only that a key name is absent fails. | test asserts `"api_key" not in body` |
| T8 | EH-10, EH-11 | Failures of error handling itself are tested: logger or recorder raises, monitoring unavailable, storage full, handler fails. The original status, code, and reference ID survive. | no test monkeypatches the recorder to fail |
| T9 | EH-11 | Resilience or chaos testing with controlled failure injection runs in staging (production only after staging results are reviewed). | no fault-injection plan for critical dependencies |

## G: Release evidence

| ID | EH | Check | Typical evidence |
|---|---|---|---|
| G1 | EH-13 | `.github/pull_request_template.md` (or equivalent) has the four error-handling Author Checklist lines. | template exists without them; no template |
| G2 | EH-13 | Automated PR review has error-handling guideline instructions and is a required check; a human reviewer still approves. | review config with no error-handling instructions; check not required |
| G3 | EH-13 | Failure-path tests run in CI as a required check, alongside static analysis and dependency scanning. Green CI alone is not accepted as proof that failure tests exist. | CI runs unit tests only on main; failure tests skipped or marked optional |

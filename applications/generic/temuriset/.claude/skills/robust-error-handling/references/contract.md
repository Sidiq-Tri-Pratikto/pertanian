# Target error contract

The shape a fix converges on. Reuse the repo's existing base type, code registry, and envelope when they already match this contract. When the repo has a published contract that differs (different field names, problem+json, a prefix style already shipped), keep that contract, close the gaps that do not break clients, and record the deviation in the report. Do not add a second envelope beside a published one.

The outcomes below are mandatory. The classes, resolver, and helpers are the recommended way to reach them; another architecture is fine when the report records the deviation, its reason, and the evidence that each outcome still holds.

Five audiences, five representations. They share one failure and stay unmixed:

| Audience | Reads | Never receives |
|---|---|---|
| End user (UI, toast, chat, CLI prose) | `message` only: what happened, then what to do next | `debug_info`, class name, internal code, stack |
| Agent / on-call / log pipeline | internal `code` + `debug_info` + `recovery` | a second prose format of the same message |
| App wrapping a library | original type, original `code`, `debug_info`, `reference_id`, chained cause | a collapsed generic error with the trail dropped |
| External client | public envelope `error.code`, `error.message`, `error.request_id`, `error.recovery` | SDK code, class name, `debug_info`, `escalate_when` |
| Support engineer | the reference ID from the client payload, looked up in centralized logging/monitoring | an ID that resolves to no record, or one buried only inside a sentence |

## 1. Taxonomy

One base exception per module. Modules that share a platform share one ancestor, then a per-module base.

```python
class BaseError(Exception):
    """Root of every error this platform raises."""
    code: str = "LIB-UNKNOWN"  # registered fallback code, never None
    default_message: str = (
        "We could not complete the operation. "
        "Contact support and provide the reference ID shown with this error."
    )
    recovery: RecoveryInfo = {"retryable": False}  # unknown failures are not retryable

    def __init__(
        self,
        message: str | None = None,
        *,
        error: Exception | None = None,
        reference_id: str | None = None,  # set only when wrapping, to carry the original over
        debug_info: DebugInfo | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.reference_id = reference_id or generate_reference_id()  # assigned once, on construction
        self.debug_info = debug_info or build_debug_info(error)      # sanitized, minimum schema
        super().__init__(self.message)

class BaseInvokerError(BaseError):
    """Root of every error this module raises."""
    code = "LIB-INV-INVERR"
    default_message = (
        "The model request could not be completed. "
        "Please try again, or contact support with the reference ID."
    )

class ProviderRateLimitError(BaseInvokerError):
    code = "LIB-INV-RATE-LIMIT"
    default_message = "The request was rate limited. Please try again later."
    recovery = {
        "retryable": True,
        "retry_after_seconds": 30,
        "max_attempts": 3,
        "escalate_when": "still failing after max_attempts",  # internal only
    }
```

**Resolver.** Use one resolver when a component calls a third-party dependency that raises inconsistently shaped errors at one integration point (a provider SDK, an external ranking API, a moderation service). The resolver inspects the raw failure and returns a typed error. Feature code raises that result; it does not pick types inline.

```python
def resolve(raw_error: Exception) -> BaseInvokerError:
    if code := extract_response_detail_code(raw_error):
        return ERROR_BY_RESPONSE_CODE[code](error=raw_error)
    if pattern := match_message_pattern(raw_error):
        return ERROR_BY_PATTERN[pattern](error=raw_error)
    if status := extract_http_status(raw_error):
        return ERROR_BY_STATUS[status](error=raw_error)
    return ERROR_BY_EXCEPTION_NAME.get(type(raw_error).__name__, InvokerRuntimeError)(error=raw_error)
```

A resolver is not required for errors this module originates itself (invalid input, illegal internal state). Those are raised as typed subclasses directly.

A raise that skips the resolver at a third-party boundary is allowed only with a comment that states why. A catch that re-raises a generic `RuntimeError` / `Exception` / `Error` and drops the specific type fails the taxonomy: the agent can no longer tell the failures apart.

## 2. Message

Fixed template, two clauses, in this order:

1. What happened.
2. What to do next.

```python
default_message = "The request was rate limited. Please try again later."
default_message = "The input size is too large. Please reduce the input size and try again."
```

The message is complete on its own. It does not point at logs, `debug_info`, or a support tool the reader cannot open. Match the convention's examples: a direct statement of the failure, then the next action. No HTTP status text, no provider vocabulary, no exception class name, no internal code used as the sentence.

Every concrete type sets its own code and two-clause `default_message`. A base default that can reach a person (the catch-all path for an unexpected failure) is itself safe and actionable, and its fallback code is registered before publication. A missing code or a half-message is never the fallback.

Each type has one `default_message`. Call sites do not build the user string by concatenating class names, status codes, or `str(error)`.

## 3. Diagnostics

`debug_info` is a separate structured object with one documented minimum schema for the whole platform. Extra keys are allowed only when documented; required keys are always present.

| Key | Required | Value |
|---|---|---|
| `error_type` | yes | `type(raw).__name__` of the original failure |
| `original_message` | yes | sanitized `str(raw)` |
| `traceback` | no | sanitized traceback, only when the raw error has one |

```python
debug_info = {
    "error_type": "RateLimitError",
    "original_message": sanitize_error_message(str(error)),
    "traceback": sanitize_traceback(traceback),  # omit when absent
}
```

Default rendering is the message only. The full dump is an explicit call:

```python
def __str__(self) -> str:
    return self.message

def verbose(self) -> str:
    return f"{self.message}\nDebug Info:\n{self.debug_info}"
```

**Internal code.** Every error type has a stable code scoped to the module, independent of the class name and the message text. Example shape: `LIB-INV-RATE-LIMIT` (platform token, library token, then the condition). The code is the error tracker's grouping key. Once published, a code is not reused for a different failure. A class-name prefix in the message (`[OpenAILMInvoker] ...`) is not a code.

**Catalog.** Every error type is listed in one place a consumer can open without reading source (a docs page per module): `code`, default message, and the condition that raises it.

**Sanitization.** `debug_info` often comes from upstream SDKs and HTTP bodies. Redact or drop API keys, authorization headers, credentials, PII, prompts, and request payloads before the object is logged, stored, or attached to the error. Redaction lives in one helper, not in each call site. If the sanitizer itself fails, store a minimal record (`error_type` only, `original_message: "<redacted>"`), never the raw text.

**Recovery.** Every error carries `recovery`, a structured field next to `debug_info`. Humans read the guidance in the message; automation reads the field.

| Key | Required | Value |
|---|---|---|
| `retryable` | yes | safe to retry this operation? Unknown failures: `false` |
| `retry_after_seconds` | no | wait before retrying; sent as the `Retry-After` header too |
| `max_attempts` | no | total attempts including the first; minimum 1 |
| `escalate_when` | no | condition that needs a human; internal only, never on the wire |

Retry eligibility depends on what the operation does, not the status code alone: a timeout on a write may have committed. Retry side effects only with an idempotency key or deduplication.

## 4. Consumer / app

When an application wraps a library error in its own type, the app error carries the library `code`, `debug_info`, and `reference_id`, and is chained from the library error. The wrap site does not log; the boundary that finally catches the app error records it once (section 6).

```python
try:
    result = invoker.invoke(prompt)
except BaseInvokerError as sdk_error:
    app_code = ErrorCodes.parse_from_error_type(sdk_error)
    raise AppError(
        app_code,
        sdk_code=sdk_error.code,
        reference_id=sdk_error.reference_id,
        debug_info=sdk_error.debug_info,
    ) from sdk_error
```

Every exception the app raises uses that same base and the same fields. A second family (a bare `Exception` subclass with no `debug_info`, or a type whose fields are declared and never set) is a defect.

## 5. Public client contract

Applies where the process returns errors to something outside it: a REST or GraphQL API, a frontend, a third-party integrator, another service.

One envelope for every error, on every endpoint, including framework validation and auth errors:

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "The request was rate limited. Please try again later.",
    "request_id": "ref_8f2c1a9e",
    "recovery": { "retryable": true, "retry_after_seconds": 30, "max_attempts": 3 }
  }
}
```

| Field | Role |
|---|---|
| `error.code` | Public, stable, documented. Identifies the kind of failure. Not the internal code. |
| `error.message` | The two-clause message for the client. Not `str(sdk_error)` and not `debug_info`. |
| `error.request_id` | This occurrence: the error's `reference_id`. Distinct from `code`. Resolves to the centralized record (section 6). |
| `error.recovery` | Public recovery contract: `retryable` always; `retry_after_seconds`, `max_attempts` when they apply. Never `escalate_when`. |

Map internal codes to one public definition per error, in one place, with a fallback. Code, status, message, and recovery live together so they cannot drift:

```python
@dataclass(frozen=True)
class PublicError:
    code: str               # public, stable, documented
    http_status: int
    message: str            # safe, two-clause, no internals
    recovery: RecoveryInfo  # public subset: no escalate_when

PUBLIC_ERROR_BY_INTERNAL_CODE = {
    "LIB-INV-RATE-LIMIT": PublicError(
        "RATE_LIMITED", 429,
        "The request was rate limited. Please try again later.",
        recovery={"retryable": True, "retry_after_seconds": 30, "max_attempts": 3},
    ),
    "LIB-RET-CONNECTION": PublicError(
        "SERVICE_UNAVAILABLE", 503,
        "The service is temporarily unavailable. Please try again in a few minutes.",
        recovery={"retryable": True, "retry_after_seconds": 60, "max_attempts": 3},
    ),
}
FALLBACK_PUBLIC_ERROR = PublicError(
    "INTERNAL_ERROR", 500,
    "We could not complete the request. Contact support and provide the reference ID.",
    recovery={"retryable": False},
)
```

When `recovery.retry_after_seconds` is present, send the same value as the `Retry-After` header.

An existing published contract that differs (RFC 9457 `application/problem+json`, GraphQL `errors[].extensions`) is kept: carry `code`, `request_id`, and `recovery` as documented extensions instead of adding this envelope beside it.

A documented public code is permanent. Retiring it is a deprecation with notice, recorded as a breaking change. The public catalog lists each public code, its message, and its trigger, in one place that is not the source file.

HTTP status (or CLI exit code) still matches the failure class: client faults 4xx, server faults 5xx, dependency outage 503. The status is the transport field. It is not the message and it is not the public code.

## 6. Centralized logging, monitoring, and reference IDs

Every system failure is recorded once, by the boundary handler that finally catches it, into centralized logging and monitoring. The raise site never logs. A local log, a printed line, or the exception object alone is not a record.

```python
@app.exception_handler(BaseError)
def record_and_respond(request, err: BaseError):
    public = PUBLIC_ERROR_BY_INTERNAL_CODE.get(err.code, FALLBACK_PUBLIC_ERROR)
    try:
        record_system_failure(
            reference_id=err.reference_id,       # same value as error.request_id in the response
            code=err.code,                       # internal code
            service="example-service",
            operation=request.scope["route"].path,  # route template, not the raw URL
            timestamp=utcnow().isoformat(),
            debug_info=sanitize(err.debug_info),
        )
    except Exception:
        # a secondary failure must not hide the original error
        emergency_log(reference_id=err.reference_id, code=err.code)
    headers = {}
    if "retry_after_seconds" in public.recovery:
        headers["Retry-After"] = str(public.recovery["retry_after_seconds"])
    return JSONResponse(
        status_code=public.http_status,
        headers=headers,
        content={"error": {
            "code": public.code,                 # public code, never err.code
            "message": public.message,
            "request_id": err.reference_id,
            "recovery": public.recovery,
        }},
    )
```

`emergency_log` writes a minimal line (reference ID, internal code, timestamp) to a channel that does not depend on the failing recorder, is bounded, and never recurses into the handler.

| Field | Required |
|---|---|
| `reference_id` | yes; the value assigned on error construction, the same one the user sees |
| `code` | yes; internal code |
| `service`, `operation` | yes; which service and which operation failed, plus entity IDs (tenant, resource) when present |
| `timestamp` | yes |
| `debug_info` | sanitized; present for unexpected and translated failures |
| `level` | `error` for unexpected failures; `warning`/`info` for expected client errors |
| never | secrets, tokens, passwords, cookies, auth headers, full bodies, personal data, prompts |

Unexpected failures also go to the error tracker, grouped by internal `code` and tagged with the reference ID. A reference ID returned to a user must resolve to this record; a test proves it (rules T5).

## Other surfaces

- **CLI.** Human text on stderr is `error[PUBLIC_CODE]: message` plus a separate `reference: req_...` line. The reference is its own line because the text surface has no field for it. `--json` prints the public envelope on stdout. Stack traces and `debug_info` only behind `--debug`. Exit codes stay documented and non-zero on failure (for example 1 unexpected, 2 usage, 3 dependency unavailable).
- **Workers / consumers.** Log the diagnostic record with the job id as `request_id`. Classify retryable vs permanent in code, not in the message. Permanent failures go to a dead-letter record that carries the internal code and `request_id`. A failed message is not acknowledged silently.
- **Frontend.** Check `response.ok`. Parse the envelope. Show `error.message`. Show `error.request_id` beside the message, not inside a rewritten sentence. Branch on `error.code`. Follow `error.recovery`: offer or run a retry only when `retryable` is true, wait `retry_after_seconds`, stop at `max_attempts`. Map network failure and non-JSON gateway responses to a two-clause offline/timeout message with its own code; never render a raw body.
- **Clients and agents.** Retry loops read the recovery contract and stop:

```python
def call_with_recovery(send_request):
    attempts = 0
    while True:
        response = send_request()
        if response.ok:
            return response
        error = response.json()["error"]
        recovery = error["recovery"]
        attempts += 1
        if not recovery["retryable"] or attempts >= recovery.get("max_attempts", 1):
            raise EscalateToHuman(error["message"], reference_id=error["request_id"])
        time.sleep(recovery.get("retry_after_seconds", 1))
```

## Worked instance

```python
err = ProviderRateLimitError(error=raw_provider_error)
err.code            # "LIB-INV-RATE-LIMIT" (failure type, repeats across occurrences)
str(err)            # "The request was rate limited. Please try again later."
err.debug_info      # {"error_type": "RateLimitError", "original_message": "<sanitized>", "traceback": "<sanitized>"}
err.recovery        # {"retryable": True, "retry_after_seconds": 30, "max_attempts": 3, "escalate_when": "..."}
err.reference_id    # "ref_8f2c1a9e" (one occurrence, recorded once at the boundary)
err.verbose()       # message + debug block, only when a developer asks
```

The client response for that failure (HTTP 429, `Retry-After: 30`):

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "The request was rate limited. Please try again later.",
    "request_id": "ref_8f2c1a9e",
    "recovery": { "retryable": true, "retry_after_seconds": 30, "max_attempts": 3 }
  }
}
```

## Full-chain test

The test that proves the whole lifecycle calls the public entry point and reads the captured record. A resolver-only test is a unit test, not this.

```python
FAKE_SECRETS = [
    "sk-test-FAKE-1234567890",       # API key
    "Bearer fake-token-abc123",      # auth header
    "jane.doe@example.com",          # PII
    "my confidential prompt text",   # prompt
]

def test_rate_limit_full_chain(client, failure_store, captured_logs):
    with inject_provider_failure(status=429, body=" ".join(FAKE_SECRETS)):
        response = client.post("/invoke", json={"prompt": "my confidential prompt text"})

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "30"
    error = response.json()["error"]
    assert error["code"] == "RATE_LIMITED"
    assert error["message"] == "The request was rate limited. Please try again later."
    assert error["recovery"] == {"retryable": True, "retry_after_seconds": 30, "max_attempts": 3}

    records = failure_store.find(reference_id=error["request_id"])
    assert len(records) == 1
    assert records[0]["code"] == "LIB-INV-RATE-LIMIT"

    for secret in FAKE_SECRETS:
        assert secret not in response.text
        assert secret not in str(records[0])
        assert secret not in captured_logs.text

def test_recorder_failure_keeps_original_error(client, monkeypatch):
    monkeypatch.setattr("app.errors.record_system_failure", raise_storage_full)
    with inject_provider_failure(status=429):
        response = client.post("/invoke", json={"prompt": "hi"})
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMITED"
    assert response.json()["error"]["request_id"]
```

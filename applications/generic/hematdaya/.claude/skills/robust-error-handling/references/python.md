# Python: wrong vs right

Examples use FastAPI and stdlib `logging`. The shape carries over to Django, Flask, and `structlog`. Rule IDs refer to rules.md. The target fields are contract.md.

## 1. Typed family, resolver, and the public envelope (S1–S4, M1, M2, D10–D12, P1, P2)

Wrong — untyped raise, internals in the body, no split between message and diagnostics:

```python
@app.post("/invoices")
def create_invoice(req: InvoiceRequest):
    try:
        return service.create(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Right — one base, a provider resolver, message-only `str`, diagnostics on `debug_info`, public envelope at the edge:

```python
class DebugInfo(TypedDict):
    error_type: str
    original_message: str
    traceback: NotRequired[str]


class BaseError(Exception):
    code: str = "LIB-UNKNOWN"  # registered fallback code (S6)
    default_message = (
        "We could not complete the request. "
        "Contact support and provide the reference ID shown with this error."
    )

    def __init__(
        self,
        message: str | None = None,
        *,
        error: Exception | None = None,
        reference_id: str | None = None,  # set only when wrapping (C1)
    ) -> None:
        self.message = message or self.default_message
        self.reference_id = reference_id or f"ref_{uuid4().hex}"  # assigned once, on construction; 128 bits (L2)
        super().__init__(self.message)
        self.debug_info = build_debug_info(error) if error else {
            "error_type": type(self).__name__,
            "original_message": self.message,
        }

    def __str__(self) -> str:
        return self.message

    def verbose(self) -> str:
        return f"{self.message}\nDebug Info:\n{self.debug_info}"


class ProviderRateLimitError(BaseError):
    code = "LIB-INV-RATE-LIMIT"
    default_message = "The request was rate limited. Please try again later."
    recovery: RecoveryInfo = {
        "retryable": True,
        "retry_after_seconds": 30,
        "max_attempts": 3,
        "escalate_when": "still failing after max_attempts",
    }


def resolve_provider_error(raw: Exception) -> BaseError:
    if extract_http_status(raw) == 429:
        return ProviderRateLimitError(error=raw)
    return ProviderRuntimeError(error=raw)


@dataclass(frozen=True)
class PublicError:
    code: str
    http_status: int
    message: str
    recovery: RecoveryInfo  # public subset: never escalate_when


PUBLIC_ERROR_BY_INTERNAL_CODE = {
    "LIB-INV-RATE-LIMIT": PublicError(
        "RATE_LIMITED", 429,
        "The request was rate limited. Please try again later.",
        {"retryable": True, "retry_after_seconds": 30, "max_attempts": 3},
    ),
}
FALLBACK_PUBLIC_ERROR = PublicError(
    "INTERNAL_ERROR", 500,
    "We could not complete the request. Contact support and provide the reference ID.",
    {"retryable": False},
)


def record_failure(request: Request, exc: BaseError, status: int) -> None:
    """The one centralized record for a failure (L1, L3). Survives its own failure (R5)."""
    log = logger.warning if status < 500 else logger.error
    try:
        log(
            "app_error",
            extra={
                "reference_id": exc.reference_id,
                "code": exc.code,
                "service": SERVICE_NAME,
                # route template, not the raw URL; unmatched routes (404/405) have no "route" in scope
                "operation": getattr(request.scope.get("route"), "path", "unmatched"),
                "timestamp": datetime.now(UTC).isoformat(),
                "debug_info": exc.debug_info,  # already sanitized by build_debug_info
            },
        )
    except Exception:
        emergency_log(reference_id=exc.reference_id, code=exc.code)


def respond(exc: BaseError) -> JSONResponse:
    public = PUBLIC_ERROR_BY_INTERNAL_CODE.get(exc.code, FALLBACK_PUBLIC_ERROR)
    headers = {}
    if "retry_after_seconds" in public.recovery:
        headers["Retry-After"] = str(public.recovery["retry_after_seconds"])  # R2
    return JSONResponse(
        status_code=public.http_status,
        headers=headers,
        content={"error": {
            "code": public.code,
            "message": public.message,
            "request_id": exc.reference_id,
            "recovery": public.recovery,
        }},
    )


@app.exception_handler(BaseError)
async def handle_app_error(request: Request, exc: BaseError) -> JSONResponse:
    response = respond(exc)
    record_failure(request, exc, response.status_code)
    return response


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    wrapped = BaseError(error=exc)  # fallback code + actionable default (S1, S6)
    record_failure(request, wrapped, 500)
    with contextlib.suppress(Exception):  # tracker outage must not change the response (R5)
        # A static event, not capture_exception(exc): the raw message and traceback locals bypass the sanitizer.
        # The fingerprint keeps distinct failure types in distinct Sentry issues (D12).
        sentry_sdk.capture_message(
            "unexpected_error",
            level="error",
            fingerprint=[wrapped.code, wrapped.debug_info["error_type"]],
            tags={"code": wrapped.code, "reference_id": wrapped.reference_id},
        )
    return respond(wrapped)


def emergency_log(*, reference_id: str, code: str) -> None:
    """Minimal, bounded, non-recursive fallback: no debug_info, no handler re-entry."""
    with contextlib.suppress(Exception):
        sys.stderr.write(f'{{"event":"error_record_failed","reference_id":"{reference_id}","code":"{code}"}}\n')
```

`BaseError` declares `recovery: RecoveryInfo = {"retryable": False}`, so unknown failures are never retryable (R1).

Own-logic failures skip the resolver and raise a typed error directly:

```python
def create(req: InvoiceRequest) -> Invoice:
    if customers.get(req.customer_id) is None:
        raise InvoiceCustomerNotFound(
            f"No customer exists with ID '{req.customer_id}'. Check the ID, or create the customer first."
        )
```

Third-party calls go through the resolver:

```python
try:
    return provider.charge(req)
except ProviderSDKError as error:
    raise resolve_provider_error(error) from error
```

An app that wraps the library error keeps the trail on the app error and leaves the recording to the boundary handler (C1, L1):

```python
except BaseError as sdk_error:
    raise AppError(
        "INVOICE_CHARGE_FAILED",
        sdk_code=sdk_error.code,
        reference_id=sdk_error.reference_id,
        debug_info=sdk_error.debug_info,
    ) from sdk_error
```

`build_debug_info` always sets `error_type` and `original_message`, adds `traceback` only when present, and runs both strings through the shared sanitizer (D4, D10).

## 1a. FastAPI boundary wiring (S1, P5, R5)

Framework failures must reach the same envelope as app errors. Register four handlers: the app base error, Starlette's `HTTPException` (FastAPI's subclasses it; it covers 404/405 from routing and every legacy `raise HTTPException`), `RequestValidationError` (422), and `Exception`.

```python
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    wrapped = error_for_status(exc.status_code)  # typed error per status; never str(exc.detail) as the message
    response = respond(wrapped)
    if isinstance(exc.detail, str):
        # Legacy compatibility only, while clients migrate; remove in its own deprecation subtask.
        response = add_legacy_detail(response, safe_detail(exc.detail))
    record_failure(request, wrapped, response.status_code)
    return response


@app.exception_handler(RequestValidationError)
async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
    wrapped = RequestInvalidError(field_errors=public_field_errors(exc.errors()))  # field + rule, no input values
    response = respond(wrapped)
    record_failure(request, wrapped, response.status_code)
    return response
```

Ordering pitfalls:

- `@app.exception_handler(Exception)` is installed on Starlette's `ServerErrorMiddleware`, the outermost layer. It runs after user middleware has unwound (CORS headers are missing on that response) and Starlette re-raises the exception afterwards, so the server also logs it: do not record it a second time there.
- A `@app.middleware("http")` / `BaseHTTPMiddleware` with its own `try/except Exception` answers first and shadows every handler above. Either delete that catch-all or make it call the same `respond` + `record_failure` path.
- Every raw `HTTPException(detail=str(e))` still leaks through `safe_detail` unless the migration replaces it; the handler only stops new leaks from framework paths.
- Test with `TestClient(app, raise_server_exceptions=False)`, hitting an unknown route (404), a wrong method (405), an invalid body (422), and a route that raises `RuntimeError`.

## 1b. Calling another internal service (X-07, P7)

```python
async def scrape(self, url: str, request_id: str) -> ScrapeResult:
    try:
        response = await self._client.post("/scrape", json={"url": url}, headers={"X-Request-ID": request_id})
    except httpx.TimeoutException as raw:
        raise UpstreamTimeoutError(error=raw) from raw
    if response.status_code >= 400:
        raise resolve_upstream_error(response)  # reads error.code / error.request_id / error.recovery, or legacy detail
    return ScrapeResult.model_validate(response.json())


def resolve_upstream_error(response: httpx.Response) -> BaseError:
    body = safe_json(response)  # {} on non-JSON gateway pages; never response.text
    envelope = body.get("error") if isinstance(body.get("error"), dict) else {}
    error_cls = UPSTREAM_ERROR_BY_PUBLIC_CODE.get(envelope.get("code"), error_for_status(response.status_code))
    return error_cls(
        debug_info={
            "error_type": f"HTTP{response.status_code}",
            "original_message": sanitize_error_message(str(envelope.get("code") or "legacy_error_shape")),
            "upstream_request_id": envelope.get("request_id"),
        },
        recovery=envelope.get("recovery"),  # honor upstream retry guidance instead of local defaults
    )
```

Wrong: `logger.warning(f"Request failed: {response.text}")` and `message=response.text`; the upstream body may contain its own stack text, URLs with tokens, or scraped personal data.

## 2. Collapsing distinct failures (S3)

Wrong:

```python
except (PluginTimeoutError, PluginAuthError, PluginValidationError) as error:
    raise RuntimeError("The skill operation could not be completed.") from error
```

Right:

```python
except (PluginTimeoutError, PluginAuthError, PluginValidationError) as error:
    raise resolve_skill_error(error) from error
```

## 3. Swallowing (D1, D6)

Wrong:

```python
try:
    send_receipt(order)
except:
    pass
```

Right:

```python
try:
    send_receipt(order)
except (smtplib.SMTPException, TimeoutError):
    # A receipt failure must not fail the paid order; the receipts job retries it.
    logger.warning("receipt_send_failed", extra={"order_id": order.id}, exc_info=True)
```

Let `asyncio.CancelledError` propagate. Catch it only to clean up, then re-raise.

## 4. Message content (M1, M5)

Wrong:

```python
default_message = "Error during model invocation. See debug info for more details."
default_message = "429 Too Many Requests"
message = f"[{type(error).__name__}] {default_message}"
```

Right:

```python
default_message = "The request was rate limited. Please try again later."
```

## 5. Secrets inside diagnostics (D4)

Wrong:

```python
debug_info = {"error_type": type(error).__name__, "original_message": str(error)}
logger.info("calling provider", extra={"headers": dict(request.headers)})
```

Right — sanitize, then log identifiers plus the sanitized object:

```python
debug_info = {
    "error_type": type(error).__name__,
    "original_message": sanitize_error_message(str(error)),
    "traceback": sanitize_traceback(traceback.format_exc()) if error.__traceback__ else None,
}
logger.info("calling_provider", extra={"provider": "xendit", "invoice_id": invoice.id})
```

Keep a logger filter that masks `authorization`, `cookie`, `password`, `secret`, `token`, and `api_key` as a second line of defense.

## 6. Branching on message text (S5)

Wrong:

```python
except Exception as e:
    if "not found" in str(e).lower():
        return None
    raise
```

Right:

```python
except InvoiceCustomerNotFound:
    return None
```

## 7. CLI surface (M3, P1)

The text surface has no envelope field, so the reference ID is its own line.

```python
def main() -> int:
    try:
        run(args)
    except BaseError as exc:
        return report(exc)
    except Exception as raw:
        return report(BaseError(error=raw))  # fallback code + actionable default
    return 0


def report(exc: BaseError) -> int:
    record_failure(exc, operation=args.command)  # centralized record, same reference ID
    public = PUBLIC_ERROR_BY_INTERNAL_CODE.get(exc.code, FALLBACK_PUBLIC_ERROR)
    if args.json:
        print(json.dumps({"error": {"code": public.code, "message": public.message,
                                    "request_id": exc.reference_id, "recovery": public.recovery}}))
    else:
        print(f"error[{public.code}]: {public.message}", file=sys.stderr)
        print(f"reference: {exc.reference_id}", file=sys.stderr)
    return EXIT_CODES.get(public.code, 1)
```

`--debug` may print `exc.verbose()`. The default path prints `str(exc)` only.

## 8. Testing the failure path (T1, T2, T4, T5)

```python
def test_rate_limit_uses_public_contract(client, caplog):
    resp = client.post("/invoices", json=payload)

    assert resp.status_code == 429
    body = resp.json()["error"]
    assert body["code"] == "RATE_LIMITED"
    assert body["message"] == "The request was rate limited. Please try again later."
    assert body["request_id"]
    assert "debug_info" not in resp.text
    assert "RateLimitError" not in resp.text
    # correlation (T5): the returned ID finds the record
    record = next(r for r in caplog.records if getattr(r, "reference_id", None) == body["request_id"])
    assert record.code == "LIB-INV-RATE-LIMIT"
    assert record.debug_info["error_type"] == "RateLimitError"


def test_unexpected_error_hides_internals(client, monkeypatch):
    def boom(_req):
        raise RuntimeError("password=hunter2 host=10.0.3.7")

    monkeypatch.setattr(service, "create", boom)
    resp = client.post("/invoices", json=payload)

    assert resp.status_code == 500
    error = resp.json()["error"]
    assert error["code"] == "INTERNAL_ERROR"
    assert error["message"] == BaseError.default_message  # fallback is complete (T1)
    assert error["request_id"]
    assert "hunter2" not in resp.text and "10.0.3.7" not in resp.text
```

Create `TestClient` with `raise_server_exceptions=False` for the 500 test. A dependency test asserts the resolver's typed error (`ProviderRateLimitError`), not only that some exception escaped.

## 9. Recovery and bounded retries (R1–R4)

Wrong: retry everything forever, including a write that may have committed:

```python
@retry(wait=wait_fixed(1))  # tenacity, no stop condition
def charge(req):
    return provider.charge(req)
```

Right: bounded, jittered, only for retryable typed errors, and side effects carry an idempotency key:

```python
@retry(
    retry=retry_if_exception(lambda e: isinstance(e, BaseError) and e.recovery["retryable"]),
    stop=stop_after_attempt(3) | stop_after_delay(20),
    wait=wait_random_exponential(multiplier=1, max=10),
    reraise=True,
)
def charge(req):
    try:
        return provider.charge(req, idempotency_key=req.idempotency_key)
    except ProviderSDKError as error:
        raise resolve_provider_error(error) from error
```

Retry in one layer only. If the SDK already retries, the service layer does not.

## 10. Error handling that fails (R5, T8)

```python
def test_recorder_failure_keeps_original_error(client, monkeypatch):
    def storage_full(*_args, **_kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(logger, "error", storage_full)
    monkeypatch.setattr(logger, "warning", storage_full)
    with inject_provider_failure(status=429):
        resp = client.post("/invoices", json=payload)

    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "RATE_LIMITED"
    assert resp.json()["error"]["request_id"]
```

## 11. Privacy with fake secret values (T7)

Inject literal fake values into the upstream failure and the input; assert the values, not key names, are absent everywhere:

```python
FAKE_SECRETS = ["sk-test-FAKE-1234567890", "Bearer fake-token-abc123",
                "jane.doe@example.com", "my confidential prompt text"]


def test_provider_error_leaks_nothing(client, caplog):
    with inject_provider_failure(status=401, body=" ".join(FAKE_SECRETS)):
        resp = client.post("/invoke", json={"prompt": "my confidential prompt text"})

    error = resp.json()["error"]
    record = next(r for r in caplog.records if getattr(r, "reference_id", None) == error["request_id"])
    for secret in FAKE_SECRETS:
        assert secret not in resp.text
        assert secret not in str(record.__dict__)
        assert secret not in caplog.text
```

## CI gate (T3)

```toml
[tool.ruff.lint]
extend-select = ["E722", "BLE001", "S110", "S112", "B904", "TRY400", "T201"]
```

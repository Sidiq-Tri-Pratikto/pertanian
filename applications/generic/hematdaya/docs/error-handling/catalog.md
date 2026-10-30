# Error Catalog

One row per error. Keep in sync with `app/core/errors/codes.py` and `public.py`. Consumers branch on the public code, never on message text.

| Internal code | Public code | HTTP | Default message | Trigger | retryable | retry_after_seconds | max_attempts |
|---|---|---|---|---|---|---|---|
| `APP-UNKNOWN` | `INTERNAL_ERROR` | 500 | We could not complete the request. Contact support and provide the reference ID shown with this error. | Any unrecognized failure | false | - | - |
| `APP-REQUEST-INVALID` | `BAD_REQUEST` | 400 | The request could not be processed. Please check the request and try again. | Request violates a business rule | false | - | - |
| `APP-NOT-FOUND` | `NOT_FOUND` | 404 | The requested resource was not found. Please check the address and try again. | Resource does not exist | false | - | - |
| `APP-CONFLICT` | `CONFLICT` | 409 | The request conflicts with the current state. Please review the resource and try again. | State conflict | false | - | - |
| `APP-DB-ERROR` | `DATA_ERROR` | 500 | The request could not be completed because of a data error. Contact support with the reference ID. | Database failure | false | - | - |
| `APP-DB-UNAVAILABLE` | `DATABASE_UNAVAILABLE` | 503 | The database is temporarily unavailable. Please try again in a few minutes. | Connection, pool, or operational failure | true | 30 | 3 |

Framework failures use the status map in `public.py`: `UNAUTHORIZED` 401, `FORBIDDEN` 403, `METHOD_NOT_ALLOWED` 405, `VALIDATION_FAILED` 422, `RATE_LIMITED` 429.

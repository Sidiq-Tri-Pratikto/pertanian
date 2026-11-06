# Error Handling Mapping and Deviations

Project mapping onto `.specify/memory/error-handling.md`. Record a deviation here with its reason and the evidence that the required outcome still holds.

## Mapping

| Concept | This project |
|---|---|
| Base error | `AppError` in `app/core/errors/base.py` |
| Code prefix | `APP-` |
| Code registry | `app/core/errors/codes.py` |
| Public map and fallback | `app/core/errors/public.py` |
| Envelope | `{"error": {"code", "message", "request_id", "recovery"}}` |
| Boundary handlers | `app/core/errors/handlers.py` |
| Recorder | `app/core/errors/recorder.py`, structured log to stdout |
| Sanitizer | `app/core/errors/sanitize.py` |
| Emergency path | `emergency_log` in `recorder.py` |
| Error tracker | None. Add it inside `record_failure` when the project picks one. |

## Deviations

| Rule | Deviation | Reason | Evidence |
|---|---|---|---|
| EH-08 | Centralized logging is stdout only until a tracker is chosen | Platform collects stdout | None yet; decide before first production release |
| EH-07 | `VALIDATION_FAILED` responses add `error.details` with field, Indonesian message, and type | Clients need to know which field to fix | Messages come from `field_message`, so submitted values and validator text are never echoed; `test_validation_error_lists_fields_without_values` |

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
| EH-07 | `VALIDATION_FAILED`, import failures, and `SCOPE_CONFLICT` add `error.details` with location, Indonesian message, and type | Clients need to know which field to fix, which part of an uploaded file, and which owned assets conflict. A catalog message cannot name more than one structural problem | Validation messages come from `field_message`, which keeps submitted values and validator text out of responses. See `test_validation_error_lists_fields_without_values`. Import details hold only alias headers, line numbers and sizes. The failure record omits those details, as pinned in `tests/unit/imports/test_import_errors.py`. Scope details hold sanitized owned names, and diagnostics omit those details, as pinned in `tests/integration/test_isolation.py`. |

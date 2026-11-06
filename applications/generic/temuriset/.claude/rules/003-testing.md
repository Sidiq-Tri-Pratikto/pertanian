---
description: pytest standards and the Condition/Expected docstring format. Use when writing tests.
globs: "**/tests/**/*.py"
alwaysApply: false
trigger: glob
paths:
  - "**/tests/**/*.py"
---
# Testing Standards

## Structure

- `tests/unit/`: no network, no database. Fake repositories and clients.
- `tests/integration/`: real Postgres through the app's HTTP interface; external services still faked. Marked `@pytest.mark.integration`.
- Mirror the source tree: `app/items/service/service.py` tests live in `tests/unit/items/test_service.py`.
- Shared fixtures go in `conftest.py`.

## Writing tests

- Name: `test_` plus a concise description of the behavior.
- Every test has this docstring:

```python
"""
Condition:
- The assumptions and conditions of the test.

Expected:
- The expected behavior under this condition.
"""
```

- Type-hint test parameters and fixtures.
- Use `pytest.mark.parametrize` for input variations.
- `asyncio_mode = "auto"`: async tests need no marker.
- Assert behavior, not implementation.
- Test the failure path as well as the happy path.

## Failure paths

`pytest.raises(Exception)` alone proves nothing. Failure tests assert message, code, response, `request_id`, the recorded failure, recovery, and that injected fake secret values appear nowhere (see `008-error-handling`).

## Coverage

- `make test-coverage` fails below 80% line coverage.
- Do not write low-value tests to reach the gate; exclude only with a stated reason.

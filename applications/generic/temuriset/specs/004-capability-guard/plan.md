# Implementation Plan: Capability guard and configuration validation

**Branch**: `004-capability-guard` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Summary

Add `require_capability`, the `CAPABILITY_UNAVAILABLE` error, a `validate_configuration(settings)` step run by `create_app`, and a web helper that reads the manifest server-side.

## Project Structure

```text
app/capabilities/
├── service/guard.py              # require_capability(id) -> Depends; raises CapabilityUnavailableError
├── service/configuration.py      # dependencies between capabilities, secret patterns, unsafe adapters
app/core/errors/codes.py, public.py   # CAPABILITY_UNAVAILABLE, 403, not retryable
app/main.py                       # validate_configuration before routers
docs/error-handling/catalog.md
applications/temuriset-web/src/api/server.ts    # serverGet(path) forwarding cookies to API_URL
applications/temuriset-web/src/features/capabilities.ts  # hasCapability(manifest, id)
```

## Contract

```json
{"error": {"code": "CAPABILITY_UNAVAILABLE",
           "message": "Fitur ini tidak tersedia pada layanan ini. Hubungi pengelola layanan bila Anda memerlukannya.",
           "request_id": "...", "recovery": {"retryable": false}}}
```

## Test Plan

Guard pass and refusal with a test-only router; capability dependency rejection; secret-looking values rejected and absent from captured logs; production refuses `development-accept`; web helper hides an entry for an absent capability.

## Out of Scope

Real guarded routes (014, 033), composition migration with pending items (033).

## Task Outline

1. Error code and catalog row, failing tests.
2. Guard dependency.
3. Configuration validation and startup wiring.
4. Web server fetch helper and capability check.

# Implementation Plan: Performance benchmarks

**Branch**: `039-benchmarks` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-api/benchmarks/{generate.py, run.py, README.md}
docs/roadmap/benchmarks.md
```

## Measurement design

- Reuse locked HTTPX and asyncio for a bounded, headless driver with one ordinary authenticated session per virtual user. It needs no additional load-testing dependency. Generate the catalog through domain services and use the application API for measurements.
- Use a dedicated disposable database and explicitly selected benchmark target. Seed visibly labelled synthetic accounts and records. Verify 1,000 published inventions, 100 active opportunities, 20 valid sessions and a complete discovery projection before timing. Keep private session data outside the source tree.
- Use signed-in `GET /api/v1/me` and authorized invention list and detail requests for standard reads, and `GET /api/v1/discovery?type=inventions&limit=20` for discovery. Record endpoint-specific p95 and counts, and measure permissions separately. Warm the application and database through controlled reads. Label first-pass conditions precisely where caches cannot be cleared. Discovery has no application response cache on the M7 baseline.
- Measure one fresh match request against all 100 opportunities using a support source held by an unrelated inventor. Use the ranked plus excluded result count and a monotonic wall clock. Compare against a declared two-second benchmark budget for this path. The budget is an experiment input. A miss invokes the job fallback condition and is recorded with an explicit disposition.
- Run first on the integrated synthetic stack and report the exact local topology. Repeat on an approved, isolated synthetic staging target when available and report the results separately.

## Validation

Use a small reproducible run to verify the dataset counts, visible projection and report calculations before executing the full-scale benchmark. Record errors and target misses with the relevant follow-up scope.

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
- Run first on the integrated synthetic stack and report the exact local topology. Keep handoff reads and writes outside the async event loop and keep credential values out of CLI diagnostics. Keep synthetic staging blocked until the operator supplies an approved isolated HTTPS deployment, its disposable database, session provisioning, a ready projection worker and hardware inventory.

## Validation

Run the smoke and full 1,000/100/20 workloads on separate fresh disposable local databases using the synchronized build. Keep the initial results and record the synchronized source revision, environment, workload results and exit status in the report. Apply latency targets to the first-pass and warmed measurements. Report warmup timings for context and count request failures in every phase. Run the project-level `make check` and record its result. Route performance misses to the relevant follow-up.

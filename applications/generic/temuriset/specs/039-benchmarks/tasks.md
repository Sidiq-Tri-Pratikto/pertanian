# Tasks for performance benchmarks

**Input** [spec.md](spec.md), [plan.md](plan.md), and PRD section 18. Paths are relative to the TemuRiset project.

## Phase 1. Setup

- [X] T001 Identify the integrated build and composition, the deployment topology from 037, and the demo conventions in `applications/temuriset-api/app/demo/service/fixtures.py`. Establish a dedicated synthetic target and document the initial failing or missing validation path in `applications/temuriset-api/benchmarks/README.md`.

## Phase 2. Foundation

- [X] T002 Define the benchmark target guard, seed/readiness assertions, request workload, run duration, percentile method, and result schema in `applications/temuriset-api/benchmarks/README.md`. Require an explicitly selected disposable environment with synthetic data and trusted authentication. Define a small smoke run and prove the driver rejects a wrong target, incomplete seed, absent sessions, empty samples and miscounted candidates.

## Phase 3. User Story 1, Measure before optimizing (P1)

**Independent test.** Seed an isolated database through domain services and verify exactly 1,000 published inventions and 100 active opportunities. Run standard API reads and authorized discovery with 20 concurrent users. Make a fresh match request and verify that the total evaluated candidates are 100. Record p95, failure counts, hardware, build, topology and cache state. Demonstrate the untimed visibility check separately.

- [X] T003 [P] [US1] Create the labelled synthetic dataset through the existing identity, portfolio, intake and support services in `applications/temuriset-api/benchmarks/generate.py`. Build 1,000 published inventions, 100 simultaneously active opportunities and 20 authenticated synthetic actors. Reuse existing demo data conventions and services for identity and versions. Require the expected isolated database and origin before writing; never expand the application's demo sign-in API to accept arbitrary account keys. Verify projection readiness and counts before timing, and restrict credentials and any handoff file to the disposable run.
- [X] T004 [P] [US1] Implement the locked HTTPX-based load runner in `applications/temuriset-api/benchmarks/run.py`. Reuse authorized cookie sessions and the normal API. Measure `GET /api/v1/me` and authorized invention list and detail reads and the authorized first discovery page in separate 20-user phases. Count unexpected HTTP responses, timeout and invalid payload separately from successful latency, and capture nearest-rank p95 and sample/error counts per endpoint, request mix and actual duration. Separate initial and warmed phases, report cache controls and process/DB/network conditions, and avoid treating an unflushed cache as cold.
- [X] T005 [US1] Add an untimed discovery visibility control and the fresh matching measurement to `applications/temuriset-api/benchmarks/run.py`. Check an unauthenticated or otherwise unauthorized discovery outcome, and verify that a synthetic record withdrawn from public visibility disappears after the production projection refresh. Run the match against 100 active opportunities held by other parties with a new idempotency key, count ranked and excluded candidates, time the request, and compare with the two-second benchmark budget. If exceeded, implement and validate the authorized job path through the existing job and operation infrastructure in `applications/temuriset-api/app/matching/` and `applications/temuriset-api/app/platform/`, or leave the fallback acceptance open with the measured evidence and a bounded follow-up spec. Preserve acting-party authorization, idempotency and version semantics.
- [X] T006 [US1] Execute the full-scale workload against the integrated local synthetic target and record the hardware, OS and architecture, versions, composition, dataset, concurrency, sample sizes, timings, failures and cache conditions in `docs/roadmap/benchmarks.md`. Record target misses alongside follow-up work and keep synthetic development measurements separate from a staging baseline.
- [ ] T007 [US1] Repeat against the authorized, dedicated synthetic staging target and add its own result rows to `docs/roadmap/benchmarks.md`. Keep the staging rows BLOCKED until an approved endpoint, fixture isolation, credentials and hardware inventory are supplied.

## Phase 4. Polish

- [X] T008 Re-run workload validation and the applicable repository checks from `Makefile`. Link the commands and evidence in `docs/roadmap/benchmarks.md` and update `specs/039-benchmarks/spec.md` with the status supported by the results.

## Dependencies and execution order

- T001 and T002 precede the generator and runner. T003 and T004 can be developed in parallel against the agreed input contract.
- T005 follows T004. T006 requires T003–T005. T007 can follow independently after the harness works and staging is approved.
- T008 follows local validation. A measured local baseline is the MVP. The staging benchmark has its own gate.

## Requirements coverage

| Requirement | Tasks |
|---|---|
| FR-001, dataset and synthetic label | T001–T003, T006–T007 |
| FR-002, hardware, scale, concurrency and cache state | T002, T004, T006–T007 |
| Acceptance 1, standard reads p95 ≤500 ms | T004, T006–T007 |
| Acceptance 2, authorized first discovery page p95 ≤2 s | T004–T007 |
| Acceptance 3, catalog count, time and request budget | T005–T007 |
| SC-001, benchmark report | T006–T008 |

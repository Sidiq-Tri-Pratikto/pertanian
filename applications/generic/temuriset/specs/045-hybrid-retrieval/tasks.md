# Tasks for gated hybrid retrieval and reranking

**Input** [Specification](spec.md), [plan](plan.md) and PRD §§10, 14 and 20.

## Phase 1 · Setup

- [X] T001 Verify the shipped keyword-overlap engine, owned matching paths, and existing rule and timing evidence in `applications/temuriset-api/app/matching/engine/evaluate.py`, `applications/temuriset-api/app/matching/service/service.py`, `applications/temuriset-api/tests/unit/matching/test_engine.py`, and `docs/roadmap/benchmarks.md` (FR-003, FR-005).

## Phase 2 · Foundations and failing tests

- [ ] T002 Define the versioned synthetic corpus, source/catalog selectors, grouped dev/held-out judgments and cohort/grounding fields in `applications/temuriset-api/benchmarks/fixtures/retrieval.json`. Add leakage, label and metric-contract tests in `applications/temuriset-api/tests/unit/test_retrieval_benchmark.py` (FR-002, FR-005).
- [ ] T003 [P] Cover actual BM25, normalized dense scoring, bounded RRF and rerank, separate admission thresholds, no-evidence abstention, deterministic ties and unchanged fit and rule semantics in `applications/temuriset-api/tests/unit/matching/test_retrieval.py` and `applications/temuriset-api/tests/unit/matching/test_engine.py` (FR-001, FR-003).
- [ ] T004 [P] Cover the literal-loopback relay contract, model pinning, malformed/nonfinite/oversize data, total timeout, unavailable output and diagnostics privacy in `applications/temuriset-api/tests/unit/matching/test_retrieval_adapter.py`. Cover the default-off/development-and-demo guard and contradictory capability selections in `applications/temuriset-api/tests/unit/capabilities/test_configuration.py` (FR-002, FR-004).
- [ ] T005 [P] Specify synthetic success, mandatory FAIL, UNKNOWN, capped and empty result lists, unsupported or stale input, missing/invalid artifact, no relay traffic from the route, legacy runs, exact replay and existing cross-party isolation in `applications/temuriset-api/tests/integration/matching/test_matches.py` (FR-001–FR-004, SC-002).

## Phase 3 · US1 (P1) · Better candidates without weaker rules

**Independent test.** Install a validated synthetic artifact produced against a local loopback model double. Run matching on the seeded authorized corpus and read the same owned run back. Then rerun with model output unavailable and assert the existing lexical result, an explicit fallback, and identical safety and access semantics. Compare all four modes on the frozen synthetic corpus.

- [ ] T006 [US1] Implement Unicode BM25, exact normalized dense scoring, one-based RRF, bounded reranking and versioned per-mode admission in `applications/temuriset-api/app/matching/engine/retrieval.py`. Accept only bounded experimental relevance evidence in `applications/temuriset-api/app/matching/engine/evaluate.py` while preserving fit, rule outcomes and the default rank path (FR-001, FR-003).
- [ ] T007 [US1] Implement the synthetic loopback producer contract and bounded startup artifact loader/validator in `applications/temuriset-api/app/matching/service/retrieval_adapter.py`. Validate explicit development/demo selection and default off in `applications/temuriset-api/app/core/settings.py`, `applications/temuriset-api/app/capabilities/service/configuration.py` and `applications/temuriset-api/.env.example`. Keep default and deployed capability and registry states unchanged (FR-002, FR-004, FR-006).
- [ ] T008 [US1] Integrate authorized fixture selection, conservative display and safe provenance/fallback in `applications/temuriset-api/app/matching/service/service.py` and `applications/temuriset-api/app/matching/model/schema.py`. Reuse the existing input snapshot, persisted result ownership and transactional idempotency (FR-001–FR-004, SC-002).
- [ ] T009 [US1] Add the offline producer/evaluation command in `applications/temuriset-api/benchmarks/retrieval.py` and document its use in `applications/temuriset-api/benchmarks/README.md`. Reuse pure retrieval and rule functions, freeze calibration on dev and compute every agreed denominator, per-mode metric and result count (FR-001, FR-002, FR-005, SC-002).
- [ ] T010 [US1] Render the localized fallback and preserve ordinary S08 results in `applications/temuriset-web/src/views/discovery/MatchesView.tsx` and `applications/temuriset-web/tests/discovery.test.tsx`; refresh `contracts/openapi.json` and `applications/temuriset-web/src/api/schema.generated.ts` (FR-002, FR-004, SC-002).

## Phase 4 · Local verification and separately gated deployment

- [ ] T011 Run targeted API and web tests, a real loopback synthetic contract smoke, the reproducible four-mode comparison, existing matching goldens and project gates in `Makefile`. Record exact local evidence and limitations in `docs/roadmap/benchmarks.md` and run `docs/roadmap/check_traceability.py` (FR-001–FR-005, SC-002).
- [ ] T012 Obtain permissioned real cases and independently reviewed/adjudicated judgments with grouped splits. Record real lexical baseline, mode-by-mode gain, safety/exposure and the approved multilingual model, tokenizer, transport and consent in `docs/roadmap/benchmarks.md` (FR-005, FR-006, SC-001).
- [ ] T013 Validate an approved persistent pgvector design with authorization, freshness, parity and performance, and confirm provider outage, cost and staging behavior in `docs/roadmap/benchmarks.md` (FR-003, FR-004, FR-006, SC-001).
- [ ] T014 Promote only qualified capabilities and manifest adapters after T012–T013 in `applications/temuriset-api/app/capabilities/service/service.py`, `applications/temuriset-api/app/capabilities/service/configuration.py`, and `applications/temuriset-web/src/features/registry.ts` (FR-006, SC-001).

## Dependencies and parallel work

T002 establishes the fixture and metric contract. T003–T005 can run independently using that contract. T006–T007 precede the runtime and command integration. T010 consumes the response schema from T008. T011 closes the local experiment. T012–T014 require a separately approved provider, data, reviewers and deployment.

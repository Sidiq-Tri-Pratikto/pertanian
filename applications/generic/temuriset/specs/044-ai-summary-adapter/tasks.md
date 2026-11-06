# Tasks for the gated AI brief summary adapter

**Input**: [Specification](spec.md), [implementation plan](plan.md), TemuRiset constitution and PRD FR12/AC35/AC68.

**Execution gate**: The local port, validation and synthetic evaluation can be built against 022. The approved provider, its processing terms and evaluation review remain outstanding.

## Phase 1 · Setup

- [X] T001 Confirm the shipped 022 summary endpoint and its off-mode test in `applications/temuriset-api/app/briefs/router.py` and `applications/temuriset-api/tests/integration/pitches/test_preflight.py`; record the external provider, processing terms and evaluation-review gate in `specs/044-ai-summary-adapter/spec.md`.

## Phase 2 · Foundations

- [X] T002 Define an extractive, provider-neutral output contract with request-local source IDs and trusted provenance (FR-002, FR-003) in `specs/044-ai-summary-adapter/plan.md`.

## Phase 3 · US1 (P1) · Shorter brief with traceable claims

**Independent test**. Ask for a shorter editable brief with a fake provider. A proper subset uses original text and references; invented IDs and claims are refused, missing access is enforced and a failed dependency falls back after at most one retry. Manual editing and the off-mode journey remain usable.

- [X] T003 [P] [US1] Replace the word-overlap cases with a synthetic evaluation set for valid selection, recombined known words/numbers, fabricated facts, adversarial text and malformed responses (FR-003, SC-001) in `applications/temuriset-api/tests/unit/briefs/test_template.py`.
- [X] T004 [P] [US1] Exercise the live summary route with an injected fake provider, a lost dependency before and during delivery, unavailable dependency and safe retry diagnostics (FR-001, SC-001) in `applications/temuriset-api/tests/integration/pitches/test_preflight.py`.
- [X] T005 [US1] Implement structured validation and preserve original text and references through `applications/temuriset-api/app/briefs/service/summarizer_service.py` and `applications/temuriset-api/app/briefs/model/schema.py`; return model identity, model version and prompt template version from trusted configuration with accepted output (FR-002, FR-003).
- [X] T006 [US1] Wire the structured result into `applications/temuriset-api/app/briefs/service/service.py` and `applications/temuriset-api/app/briefs/router.py`; verify live access before each attempt and before returning results. Cap transient retries at one, record typed terminal failure through `applications/temuriset-api/app/core/errors/recorder.py` and retain the deterministic brief with live redaction on refusal or failure (FR-001). Document mapped errors in `docs/error-handling/catalog.md`.
- [ ] T007 [US1] Once the external gate passes (FR-004), implement the approved async provider and one resolver in `applications/temuriset-api/app/briefs/service/summarizer_service.py`; validate secret settings in `applications/temuriset-api/app/core/settings.py` and `applications/temuriset-api/app/capabilities/service/configuration.py`.
- [ ] T008 [US1] Drive an optional S11 button by the live adapter status in `applications/temuriset-web/src/views/pitches/PreflightView.tsx` and `applications/temuriset-web/src/features/capabilities.ts`; test Indonesian fallback copy and preservation of the editable draft (FR-004) in `applications/temuriset-web/tests/pitches.test.tsx`.

## Phase 4 · Verification and activation

- [ ] T009 Regenerate `contracts/openapi.json` and `applications/temuriset-web/src/api/schema.generated.ts`; run the evaluation set, targeted tests and the check in `Makefile`.
- [ ] T010 Only after the approved provider, processing terms and reviewed evaluation set are evidenced and verified, make the validated adapter available in `applications/temuriset-api/app/capabilities/service/service.py` and update only the AI-summary entry in `applications/temuriset-web/src/features/registry.ts`; record gate evidence in `specs/044-ai-summary-adapter/spec.md`.

## Dependencies and parallel work

T001 verifies the existing product seam. T003 and T004 can run in parallel after T002. T005 precedes T006. The provider-neutral MVP is T003–T006 with a fake provider and default off mode. T009 runs for the provider-neutral MVP and again after real transport and UI work. T007 waits for external approvals. T008 depends on a validated adapter status. T010 requires T007–T009 and the external review.

T007, T008 and T010 wait for provider approval, processing terms and an independently reviewed evaluation set.

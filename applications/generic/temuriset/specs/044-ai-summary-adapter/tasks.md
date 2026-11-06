# Tasks for the gated AI brief summary adapter

**Input**: [Specification](spec.md), [implementation plan](plan.md), TemuRiset constitution and PRD FR12/AC35/AC68.

**Execution gate**: The existing extractive selection is verified against 022. Local transport and UI work use synthetic data. Provider selection, processing terms, independent evaluation review and activation remain outstanding.

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
- [X] T007 Regenerate the provider-neutral `contracts/openapi.json` and `applications/temuriset-web/src/api/schema.generated.ts`; run the evaluation set and checks in `Makefile`.
- [ ] T008 [P] [US1] Add local relay contract cases for candidate-only input, malformed responses, bounded transient failures and trusted provenance (FR-001–FR-003, SC-001) in `applications/temuriset-api/tests/integration/pitches/test_preflight.py`.
- [ ] T009 [P] [US1] Add S11 coverage for default-off and available status, explicit application, failures and a newer edited or refreshed draft (FR-004, SC-001) in `applications/temuriset-web/tests/pitches.test.tsx`.
- [ ] T010 [US1] Add the development-only loopback relay to `applications/temuriset-api/app/briefs/service/summarizer_service.py` and select it through `applications/temuriset-api/app/briefs/router.py`. Validate and document the default-off settings in `applications/temuriset-api/app/core/settings.py`, `applications/temuriset-api/app/capabilities/service/configuration.py`, `applications/temuriset-api/.env.example` and `applications/temuriset-api/README.md` (FR-001–FR-004).
- [ ] T011 [US1] Add default-off and validated local adapter statuses to `applications/temuriset-api/app/capabilities/router.py` and `applications/temuriset-api/app/capabilities/service/service.py`, with coverage in `applications/temuriset-api/tests/unit/capabilities/test_configuration.py`. Wire S11 through `applications/temuriset-web/src/app/pitches/new/page.tsx`, `applications/temuriset-web/src/features/capabilities.ts`, `applications/temuriset-web/src/features/pitches/api.ts` and `applications/temuriset-web/src/views/pitches/PreflightView.tsx` (FR-004).

## Phase 4 · Verification and activation

- [ ] T012 Recheck generated files `contracts/openapi.json` and `applications/temuriset-web/src/api/schema.generated.ts`; run the targeted and full checks in `Makefile`. Record local relay, evaluation and web evidence in `specs/044-ai-summary-adapter/tasks.md` (SC-001).
- [ ] T013 Select and verify the approved provider, data processing terms, prompt/schema contract and independently reviewed evaluation. Record the evidence in `specs/044-ai-summary-adapter/spec.md` (FR-004, SC-001).
- [ ] T014 After T013, enable the approved deployment profile through `applications/temuriset-api/app/capabilities/service/configuration.py` and promote only the AI-summary feature in `applications/temuriset-web/src/features/registry.ts` after deployment verification (FR-004).

## Dependencies and parallel work

T001–T007 establish the provider-neutral baseline. T008 and T009 can run in parallel. T010 and T011 complete the local MVP, followed by T012. T013 and T014 require external approval and evidence after local verification.

The original provider-neutral verification ran on schema `0015` with a fake provider. The scoped suite passed 62 tests. Both application checks passed on that historical stack, including 835 API tests and 257 web tests. Regenerated OpenAPI and TypeScript matched that stack's contracts. T012 verifies the current stack.

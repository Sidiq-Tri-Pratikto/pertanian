# Feature Specification: Explainable matching engine

**Feature Branch**: `019-matching-engine`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M5 Discovery and matching
**Depends on**: 013, 014, 016
**Size**: L
**Covers**: FR11, AC18, AC20, AC25, AC27, AC31, AC32, AC33
**Flips**: manifest adapter `lexical-rules` → `available`

## User Scenarios & Testing

### User Story 1 - One need against one mandate, with reasons and gaps (Priority: P1)

The engine evaluates a selected source (support request or funding request, at a version) against each active opportunity version and returns requirement rows, eligibility, readiness, relevance, conservative fit bounds, coverage, three reasons, the first blocking gap and later-stage work.

**Why this priority**: FR11; preflight and the match screen depend on it.

**Independent Test**: Golden responses for F01–F06 against A1–D1.

**Acceptance Scenarios**:

1. **Given** F01 with USD 20000–30000 over six months and A1 with USD 15000–40000 on the same scope, **When** evaluated, **Then** stage, file presence and budget pass, readiness is `READY_TO_SUBMIT`, and the commercialization certificate is later work that does not block.
2. **Given** F01-GAP (null range), **When** evaluated against A1, **Then** budget is `UNKNOWN`, readiness `NEEDS_INFORMATION`, label "Perlu konfirmasi", and the gap says "Kisaran biaya pilot untuk kebutuhan ini belum diisi".
3. **Given** F02 against A2, **When** evaluated, **Then** reviewed authority is `UNKNOWN` with "Ini bukan berarti wewenang tidak ada", and no money or ownership is invented (AC32).
4. **Given** F03 with PLANNED SSO against D1 requiring CURRENT SSO, **When** evaluated, **Then** the requirement is `FAIL`, eligibility `INCOMPATIBLE`, and the result is excluded from the positive list despite topic similarity (AC31).
5. **Given** FRaise01 against B1, **When** evaluated, **Then** the investor's USD 50000–150000 check is compared with the desired USD 50000–100000 contribution, not the USD 500000 target, and passes (AC20).
6. **Given** F06 against A3 and B1, **When** evaluated, **Then** mentoring passes and the incorporated-entity requirement is `UNKNOWN`.
7. **Given** A = 0.80 and B with known 0.65 and unknown weight 0.15, **When** bounds are computed, **Then** they are 71.72–80.00, and a mandatory `UNKNOWN` keeps the label "Perlu konfirmasi" (AC33).

### User Story 2 - The engine never invents a match (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a monthly and a six-month amount in one currency, **When** compared, **Then** the result is `UNKNOWN` with reason "periode berbeda" (AC18).
2. **Given** EUR and USD, **When** compared, **Then** the result is `UNKNOWN`; no conversion happens.
3. **Given** project funding against an equity-only mandate, **When** evaluated, **Then** the relationship form is `FAIL`.
4. **Given** A1, A2 and A3 from one partner, **When** evaluated, **Then** each is evaluated separately before grouping, and favourable fields never merge (AC25).
5. **Given** a narrative requirement without mapping, **When** evaluated, **Then** it is `UNKNOWN` for manual review and never a hidden failure (AC27).
6. **Given** a target with no lexical relevance signal, **When** all its rules pass, **Then** it abstains with "Belum ada sinyal relevansi" and is not shown as a positive match.

### Edge Cases

- A known CURRENT requirement is never satisfied by a PLANNED fact.
- Later-stage requirements keep their real result but never block submission.
- With no checklist, the response says "Belum ada checklist" instead of a percentage.
- Evaluation is limited to the acting party's authorized source and active opportunities.

## Requirements

### Functional Requirements

- **FR-001**: The engine MUST be pure, deterministic Python with no I/O, versioned by policy ids.
- **FR-002**: Eligibility (`ELIGIBLE`, `NEEDS_VERIFICATION`, `INCOMPATIBLE`) and readiness (`READY_TO_SUBMIT`, `NEEDS_INFORMATION`, `BLOCKED_FOR_THIS_TARGET`) MUST be separate outputs.
- **FR-003**: Fit MUST use the PRD section 10 weights and harmonic bounds; coverage below 0.40 MUST read "Informasi belum cukup".
- **FR-004**: Financial compatibility MUST compare only same subject, basis, currency and period; overlap 1, non-overlap with partial support 0.5, non-overlap with full support required 0.
- **FR-005**: Each run MUST be persisted with input versions, engine and policy versions, so it can be reproduced.
- **FR-006**: Golden JSON for F01–F06 MUST live in `contracts/golden/` and pass byte for byte.

### Key Entities

- **MatchRun**, **MatchResult**, **RequirementResult**, **FitBounds**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every matching oracle in `docs/generic/temuriset/app-prototype/tools/domain.test.mjs` is ported and passes against the API.

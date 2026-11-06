# Implementation Plan: Explainable matching engine

**Branch**: `019-matching-engine` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/matching/
├── router.py                     # POST /matches {source_type, source_id}; GET /match-runs/{id}
├── engine/
│   ├── requirements.py           # evaluate(requirement, source, opportunity) -> PASS | FAIL | UNKNOWN | NOT_APPLICABLE + reason
│   ├── money.py                  # compare(source_money, target_money) on Decimal from strings
│   ├── fit.py                    # side(features, weights), harmonic bounds, coverage
│   ├── relevance.py              # keyword overlap; abstain at zero
│   └── evaluate.py               # rows, eligibility, readiness, label, reasons, gap, later work
├── model/{models.py, schema.py}
├── repository/sqlalchemy/{models.py, repository.py}   # match_runs, match_results
└── service/service.py            # load authorized projections, run engine, persist, order results
contracts/golden/match-f01-a1.json, match-f01gap-a1.json, match-f02-a2.json, match-f03-d1.json,
                 match-fraise01-b1.json, match-f06-a3.json
migrations/versions/0010_matching.py
```

## Weights and Labels

Direction A: problem relevance .45, accepted stage .15, sector .15, financial .15, timing .10. Direction B: support coverage .40, relationship form .30, geography .15, availability .15. Unknown features add their weight to the upper bound only. Strong: lower ≥ 70, coverage ≥ .70, eligible. Potential: lower ≥ 50, coverage ≥ .50. Ordering: eligibility group, lower bound, relevance, stable id.

## API Contract

`POST /api/v1/matches` → run with results:

```json
{"run_id": "...", "source": {"type": "SUPPORT_REQUEST", "id": "...", "version": 2},
 "results": [{"opportunity_version_id": "...", "partner": "Mitra A", "eligibility": "ELIGIBLE",
   "readiness": "READY_TO_SUBMIT", "relevant": true, "label": "Kecocokan kuat",
   "fit": {"lower": "80.00", "upper": "88.57", "coverage": "0.93"},
   "reasons": ["Tahap inovasi diterima mandat ini.", "Berkas tersedia. Isinya belum diperiksa.", "Kisaran biaya beririsan pada cakupan dan periode yang sama."],
   "gap": null, "later": [{"label": "Sertifikat komersialisasi", "applies_at": "COMMERCIALIZATION", "result": "UNKNOWN"}],
   "rows": [...], "evidence": {"provided": 3, "reviewed": 0, "applicable": 4}}],
 "excluded": [...]}
```

Golden files fix exact numbers; the example values above are illustrative until the goldens are generated from the oracles.

## Prototype Reference

`evaluate`, `evalReq`, `compareBudget`, `compareContribution`, `side`, `fitBounds`, `harmonic` in `domain.js`; oracles F01–F06, AC31, AC33, EUR and period, relationship form, abstain.

## Test Plan

Engine unit tests per operator and per oracle; property test that a mandatory FAIL never yields a positive label; golden JSON through the HTTP layer; persistence and reproducibility; isolation.

## Out of Scope

Dense retrieval and reranking (045), web (020).

## Task Outline

1. Port the prototype oracles as failing engine tests.
2. Requirement evaluation and money comparison.
3. Fit, relevance, labels, ordering.
4. Service with authorized projections; persistence.
5. Golden files and contract.

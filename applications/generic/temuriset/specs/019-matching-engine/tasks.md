# Tasks: Explainable matching engine

**Input**: `specs/019-matching-engine/spec.md`, `plan.md`, built on `main` after M4 (`c90da37`)
**Branch**: `f/m5-discovery-matching`

All tasks are done; this file records the decisions the spec left open and how the prototype's fixture data maps to the contract. The binding summary is in `docs/roadmap/architecture.md` ("Discovery and matching (M5)").

## Decisions resolved against the code

| ID | Decision | Why |
|---|---|---|
| M1 | `document:<key>` is met by a fact with that key whose `document_version_id` names a file the source's owner owns; `evidence_status` decides per verification mode. | Documents link to inventions only through facts (spec 012). A link to another party's file must prove nothing. |
| M2 | The engine reads requirement fields, not only operators, as the prototype's `evalReq` does; `minimum` and `maximum` compare the applicant's own amount, and any other unmapped pair is `UNKNOWN` for manual review. | AC27: an unmapped requirement is never a hidden failure. |
| M3 | Budgets compare currency, basis and months (not period text), and scope when both state one. Contributions compare only with an `investorCheck` range. | FR-004 and D13 of spec 016. |
| M4 | `results` holds relevant, non-incompatible targets; `excluded` holds incompatible and abstaining ones, ordered the same way. | AC31 and the abstain oracle: neither may appear as a positive match. |
| M5 | Fit uses `Decimal` with half-up rounding to two places. `timing` is unknown, and `support` and `geography` are fixed at 1, as in the prototype. | Byte-for-byte goldens; the prototype rounds with `Math.round`. |
| M6 | `POST /matches` takes an `Idempotency-Key` and stores every run with the source projection, so it can be reproduced. A raise needs `company_funding`. | FR-005; capability guard of spec 014. |

## Prototype data mapped to the contract

| Prototype | Fixture (`app/demo/service/data.py`) | Why |
|---|---|---|
| `docs: ['doc-f01']` with `kind: 'function'` | A fact keyed `function` linked to an uploaded PDF | M1 |
| F02 `authority: 'UNCONFIRMED'` | An authority claim with status `asserted` | Claims carry authority (spec 009) |
| F02, F04, F05, F06 with no facts | One `CURRENT` fact each | Publication needs a current fact (spec 009) |
| Budget `period: '6 bulan'` | Also `basis: total_period` and request `months: 6` | M3 |
| FRaise01 `stage: 'Pre-seed'`, `form: 'Ekuitas'` | `financing_stage: pre_seed`, `financing_form: equity` | Spec 014 enums |
| Support request forms such as `'Pendanaan proyek'` | `project_funding`, `facilities`, `technical_partner`, `mentoring` | Spec 013 enums |

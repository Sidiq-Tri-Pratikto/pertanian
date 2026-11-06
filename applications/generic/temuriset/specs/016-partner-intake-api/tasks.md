# Tasks: Partner profiles, opportunities and typed requirements

**Input**: `specs/016-partner-intake-api/spec.md`, `plan.md`, generated against commit `92d8c4b` (end of M3) and revised against `e340d15` (idempotency fix)
**Branch**: `f/m4-partner-intake`, stacked on `f/m3-needs-funding`
**Tests**: Required. The roadmap says test first, and the plan has a test plan. Tests in each story are written first and must fail.

**Paths** start at `applications/generic/temuriset/`. The reference modules are `app/needs/` and `app/funding/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1 or US2 from `spec.md`

## Decisions resolved against the code

The spec and plan leave these open or disagree with a binding source. Each task below assumes the decision shown. T038 and T039 record them in `architecture.md`, `spec.md` and `plan.md`.

| ID | Decision | Why |
|---|---|---|
| D1 | Saving an `ACTIVE` or `PAUSED` opportunity creates the next version and makes it current at once, with the status unchanged. Earlier versions stay frozen. A `DRAFT` opportunity is edited in place as version 1. `CLOSED` and `EXPIRED` refuse edits. `closes_at` belongs to the opportunity and changes with the save. A save on `ACTIVE` or `PAUSED` must pass the same readiness check as activation: `title`, `outcome`, `included`, `excluded`, `support`, `accepted_stages`, `relationship_forms`, `timing` and `financial` are filled, every blocking requirement has a reason, and the partner has a saved profile. In 017, the review step is client-side and "Aktifkan versi N" is this save. | The spec says an edit "creates a new version". The PRD's state rules give Opportunity the same states as SupportRequest, `app/needs/` saves this way, and so does the prototype's `saveOpportunity`. The draft-successor sentence at `architecture.md:128` fits published inventions, and T038 narrows it to them. Without the check, a save could publish what activation would refuse. The fields are FR-002's, and all seven prototype opportunities have them. The profile holds the contact route that `target_availability` reads, so an active target always has one. |
| D2 | Mutations require `Capability.EDIT_PORTFOLIO`. **Worth reviewing:** in an organization that is both inventor and partner, an invention editor can also publish a mandate. | 007 FR-002 fixes the capability list and has no intake entry. The prototype uses `can(actor, partner, 'edit')`, and all 14 current uses are `EDIT_PORTFOLIO`. The PRD authorization table has no row for this. |
| D3 | The handoff route is `POST /partners/{party_id}/handoffs`. It records the partner only, and needs a signed-in party and `Idempotency-Key`, with no capability. | The contact route lives on the profile. A click is not a pitch, so `submit_pitch` does not apply. AC24 needs no opportunity, and an optional id would need its own visibility rule so a draft's existence does not leak (principle 6). |
| D4 | A profile has no draft state: it is readable by others once saved. A party with no profile is `NOT_FOUND`. Others get `NOT_FOUND` for a `DRAFT` opportunity and can read every other status. | The `partner_profiles` row in `architecture.md` has no status column. A closed target must still explain itself (AC26). The isolation owner holds a draft opportunity and no profile, as it holds an unpublished invention for `/inventions/{id}/public`. |
| D5 | Use `PUT` rather than the PRD's `PATCH`, and plain lists rather than `Page`. | M3 used `PUT` against the same PRD table. The isolation harness accepts only `404` or `[]`. |
| D6 | `SOURCE_REPORTED` profiles are written only through a service method, with no route. An owner's save is always `OWNER_CONFIRMED` and may set only `OPEN` or `CLOSED`. | An owner must not be able to claim a source. 021 seeds through services, and 036 imports. |
| D7 | Add `opportunities.kind` (`SPECIFIC`, `GENERAL_INTAKE`), at most one open general intake per partner. Activating it, or saving it while active, sets `partner_profiles.general_intake_version_id`. | Drafts need a kind before the pointer exists. |
| D8 | AC23 is proven at `IntakeService.target_availability`, not at a pitch route. Each opportunity read and list item exposes the result as `target_availability: {available, reason}`. 023 must call this method. | Pitches do not exist until 023, so "a general direct pitch is attempted" cannot run in this PR. Integration tests go through HTTP (rule 003), and 017 must show the result without re-implementing the rule (principle 12). |
| D9 | `visibility` is `PUBLIC` or `PARTNER_ONLY`, and a mandatory requirement must be `PUBLIC`. A requirement's `version` is its parent version's `number`, with no column of its own. The PRD's unit/basis, source and accountable reviewer are left out. | FR-003 needs both fields but defines no values. The PRD says no secret criterion may reject a pitch. FR-003 and `architecture.md` omit the other three. |
| D10 | Reads compute `EXPIRED` from `closes_at` and never write. The worker persists it. A mutation under lock treats a passed `closes_at` as `EXPIRED`. | `architecture.md` requires a job and a lazy check. A `GET` should not bump versions or race the worker. |
| D11 | No new public error code: `VALIDATION_FAILED`, `INVALID_TRANSITION`, `CONFLICT`, `STALE_VERSION`, `STALE_CONTEXT` and `FORBIDDEN` cover this spec. `TARGET_CLOSED` stays with 023. | Avoids a code with no route to raise it. |
| D12 | Outbox topics are `partner.changed` and `opportunity.changed`. | 018 plans consumers for `partner.*` and `opportunity.*`. |
| D13 | `financial` and the profile's range state subject, basis and period. `FinancialBasis` is `Basis` from `app/needs/model/schema.py` plus `per_investment`. A cash range without a basis or period is refused. A `per_investment` range states `period: "per investasi"`. A `total_period` range also states `months`, as `support_requests` does, and other bases leave it null. Non-cash support and license terms carry none. | Constitution principle 8. 019 FR-004 compares only the same subject, basis, currency and period. `Basis` has no value for one investor's check. `directly_comparable` in `app/needs/service/budget.py` compares months, not period text. |
| D14 | `POST /opportunities/{id}/activate`, `/pause` and `/close` are three routes, each with its own `idempotent(...)` operation and an `operation_id` in the response. | Constitution principle 11. This is the pattern in `app/needs/router.py`. |
| D15 | A requirement with no operator is stored as `field: "narrative"`, `operator: "manual_review"`, `value: null`, `mandatory: false`. `narrative` with a typed operator is refused. | US2 scenario 2. The prototype's `addReq` does this, and a non-mandatory row cannot block submission. |
| D16 | `target_availability` follows the table below and returns `available` with a `reason`. **Route `EXTERNAL` blocks in-app pitching**, including for a specific opportunity, and offers the handoff instead. | PRD FR08: contact preferences govern whether the product offers in-app pitching, an external route or no new approaches. AC23 keeps specific opportunities independent of direct intake. |
| D17 | A first profile save sends `expected_version: null`. Any later save must send the current version, and null is `STALE_VERSION` once a profile exists. A number before any profile exists is also `STALE_VERSION`. Two first saves race on the unique `party_id`, and the loser gets `STALE_VERSION`. | `PUT` both creates and changes, so `check_expected` has no version to compare on the first save. Stale intent never overwrites current state (principle 11). |

### Target availability

Checks run in this order, and the first one that fails gives the `reason`.

| Check | Specific opportunity | General intake | `reason` when it fails |
|---|---|---|---|
| Effective status is `ACTIVE` | Required | Required | `TARGET_NOT_ACTIVE` |
| Route is not `EXTERNAL` | Required | Required | `EXTERNAL_ROUTE` |
| Route is not `NONE` | Required | Required | `NO_NEW_APPROACHES` |
| `intake_status` is not `CLOSED` | Ignored | Required | `DIRECT_INTAKE_CLOSED` |
| `intake_status` is not `UNCONFIRMED`, and `intake_until` has not passed | Ignored | Required | `INTAKE_UNCONFIRMED` |

### Prototype data mapped to the contract

`domain.js` is evidence, not a contract. Recipient data in `tests/factories/recipients.py` differs from it in these ways:

| Prototype | Factory | Why |
|---|---|---|
| D1-sso operator `current` | Field `feature:sso`, operator `equals`, value `"CURRENT"` | `current` is outside the eight allowed operators. `CURRENT` is the `invention_facts.timing` value, and 019 can read it the same way. |
| Field `doc:function`, `doc:certificate` | `document:function`, `document:certificate` | The plan's API contract. |
| `why` | `reason` | The plan's API contract. |
| No reason on A2-stage, A3-stage, B2-form, B2-check, D1-form | New Indonesian reason text, to be checked in review | US2 scenario 3 requires a reason on every blocking requirement. |
| `range_overlap` with `value: null` on `budget`, `contribution` | Unchanged. The range comes from the version's `financial`. | 019 compares against `opp.financial`. Saving needs a comparable range there. |
| Money `"15000"` | `"15000.0000"` | The wire format renders four places. |
| Partner `stages`: `"Ide, prototipe, pilot"` (A), `"Pre-seed dengan prototipe"` (B), `"Siap pasar"` (C), `"Sudah berfungsi"` (D) | `["IDEA", "PROTOTYPE", "PILOT"]`, `["PROTOTYPE"]`, `["MARKET"]`, `["WORKING"]` | `Stage` values only. |
| E's `stages` and `regions`: `"Belum diketahui"` | Empty lists | Unknown is never stored as a value (principle 7). |
| Partner `regions` and `forms` as one string | Lists, such as `regions: ["Indonesia"]` | The `architecture.md` columns are lists. |
| Opportunity `relationship: "PROJECT"` | `relationship_forms: ["PROJECT"]` | The plan's API contract. |
| D1's `terms: "Belum ditentukan"` | `unknown_reason: "not_determined"` with no terms | Unknown is never stored as a value (principle 7). |
| `financial` with no basis, and B's `check` with no period | A1 `total_period`, keeping `period: "6 bulan"` and adding `months: 6`. B1, B2 and B's profile range `per_investment`, with subject `investorCheck` and `period: "per investasi"`. A2, A3, C1 and D1 carry none. | D13. The period follows from the basis, so no fact is invented. |

---

## Phase 1: Setup

**Purpose**: Module skeleton and the test import path

- [X] T001 Create the empty package per rule 005 and the M3 layout, with no `base_repository.py`: `applications/temuriset-api/app/intake/__init__.py`, `model/__init__.py`, `repository/__init__.py`, `repository/sqlalchemy/__init__.py`, `service/__init__.py`
- [X] T002 [P] Add `pythonpath = ["."]` to `[tool.pytest.ini_options]` in `applications/temuriset-api/pyproject.toml`, because no test imports `tests.*` today and `--import-mode=importlib` does not add the root to the path

---

## Phase 2: Foundational

**Purpose**: Tables, schemas, repository and recipient data that both stories use

**⚠️ CRITICAL**: No story work starts until this phase is complete

- [X] T003 Define `IntakeStatus`, `ProfileSource`, `ContactRoute`, `OpportunityKind`, `OpportunityStatus`, `Operator`, `AppliesAt`, `VerificationMode`, `Visibility` and `AvailabilityReason` in `applications/temuriset-api/app/intake/model/models.py`, reusing `Stage` from `app/portfolio/model/schema.py`
- [X] T004 Create `PartnerProfileRecord`, `OpportunityRecord`, `OpportunityVersionRecord`, `RequirementRecord` and `ExternalHandoffRecord` in `applications/temuriset-api/app/intake/repository/sqlalchemy/models.py`, with the `architecture.md` columns plus `review_expectations`, `relationship_forms`, `intake_from`, `intake_until`, `range_subject`, `range_basis`, `range_period`, `range_months` and the `unknown_reason` for a range on profiles, `kind` on opportunities, and `visibility` and `position` on requirements. `ExternalHandoffRecord` has `partner_party_id`, `actor_party_id` and `external_url`, keeps the URL as it was followed, and is append-only
- [X] T005 Write `applications/temuriset-api/migrations/versions/0008_intake.py` with `down_revision = "0007"`: enum `CHECK`s, unique `party_id`, unique (`opportunity_id`, `number`), `check_min >= 0`, `check_max >= check_min`, `EXTERNAL` needs `external_url`, a mandatory requirement must be `PUBLIC`, the partial unique index from D7, and `use_alter` foreign keys for the version pointers. Run upgrade, downgrade one step, then upgrade again
- [X] T006 [P] Import the ORM module in `applications/temuriset-api/migrations/env.py`, and add the five tables to `TABLES` in `applications/temuriset-api/tests/integration/conftest.py`
- [X] T007 Write request and response schemas in `applications/temuriset-api/app/intake/model/schema.py` per the plan's contract and `architecture.md`. The plan's example omits several fields, so include all of them: `support`, `timing`, `sectors` and `keywords` on a version, `kind` and `closes_at` on an opportunity, `basis` and `months` in `financial` (D13), `target_availability` and a `general_intake_label` that is null for a specific opportunity on an opportunity response (D8), an `expected_version` that may be null on a profile save (D17), and `visibility` and `version` on requirements. Use `extra="forbid"` on inputs so assets under management, capacity and credentials are refused, `Money` and `CurrencyCode` for amounts, `external_url` limited to `http` and `https`, and `operator` optional so a narrative requirement can omit it
- [X] T008 Implement `SqlAlchemyIntakeRepository` in `applications/temuriset-api/app/intake/repository/sqlalchemy/repository.py`: find with optional lock, write and read versions with their requirements in `position` order, list by partner, insert a first profile with `ON CONFLICT DO NOTHING` so the loser of a race can be told (D17), append handoffs. Never commit
- [X] T009 [P] Write Recipients A1, A2, A3, B1, B2, C1, D1 and E as plain data in `applications/temuriset-api/tests/factories/recipients.py`, per the mapping table above and including `support`, `timing`, `sectors` and `keywords` from `domain.js`, with no database import so 019's engine tests can reuse it
- [X] T010 [P] Write `applications/temuriset-api/tests/unit/intake/test_recipients_data.py`: eight targets, unique ids, A has three opportunities, B has a USD 50000–150000 check, E is `SOURCE_REPORTED`, `EXTERNAL`, `UNCONFIRMED` with no opportunity, every stage is a `Stage` value, no field holds "Belum diketahui", every cash range has a basis and a period, every `total_period` range has `months`

**Checkpoint**: Migration applies, `make test-unit` imports the factory, no route exists yet

---

## Phase 3: User Story 1 - A partner states its mandate honestly (Priority: P1) 🎯 MVP

**Goal**: Profiles and versioned opportunities that say only what is known, with states and external handoffs

**Independent Test**: Load Recipients A–E. Each opportunity reads back with its own version, intake and requirements. Recipient E is labelled source-reported and claims no active intake.

### Tests for User Story 1 ⚠️

> Write these first and confirm they fail.

- [X] T011 [P] [US1] Write `applications/temuriset-api/tests/integration/intake/test_partner_profiles.py`: Investor B as a personal party with no organization and amounts `"50000.0000"`–`"150000.0000"` that read back with subject, `per_investment` basis and `period: "per investasi"` (scenario 1); invented fields refused; unknown range stays `null` with a reason; maximum below minimum, amounts without a basis or period, and `total_period` without `months`, refused per field; owner cannot set `SOURCE_REPORTED` or `UNCONFIRMED`; a stranger's save is `NOT_FOUND`; a member without `edit_portfolio` gets `FORBIDDEN`; a first save with `expected_version: null` creates version 1; null once a profile exists, a number before one exists, and the loser of two parallel first saves are each `STALE_VERSION` and overwrite nothing (D17); stale version; stale context; replay and key conflict
- [X] T012 [P] [US1] Write `applications/temuriset-api/tests/integration/intake/test_intake_availability.py`: E reads "Dilaporkan sumber" and "Ketersediaan belum dikonfirmasi" with no active intake (AC22); after a partner closes intake, the general target's `target_availability` is unavailable while A1's stays available (AC23, D8); every row of the availability table, read over HTTP and parametrized over both target kinds, with its `reason` (D16); a list item carries the same result as its read; a general target is labelled "berdasarkan profil umum mitra" (FR-004); a passed `intake_until` is not shown as open; thesis and availability are separate response fields (FR-001)
- [X] T013 [P] [US1] Write `applications/temuriset-api/tests/integration/intake/test_opportunities.py`: A1, A2, A3 keep separate versions, statuses and requirements, and nothing merges (AC25); saving an active opportunity makes version 2 current at once with the status still `ACTIVE`, and a paused one stays `PAUSED` (D1); editing a draft keeps version 1; the owner's `GET /versions/1` still returns the old content and others get `NOT_FOUND` for it; others get `NOT_FOUND` for a draft, and `?partner_party_id=` never lists another party's draft; a cash range without a basis or period, or `total_period` without `months`, is refused per field (D13); stale version; replay and key conflict on create and save
- [X] T014 [P] [US1] Write `applications/temuriset-api/tests/integration/intake/test_opportunity_states.py`: every allowed and refused move; for each of activate, pause and close, a retry with the same key replays and changes once, the key at a later version is `IDEMPOTENCY_CONFLICT`, no key is `BAD_REQUEST`, and the response carries `operation_id` (D14); activation refused without the D1 readiness fields, without a saved partner profile (`VALIDATION_FAILED` naming `partner_profile`), or with a past `closes_at`; a save on `ACTIVE` or `PAUSED` without those fields is refused per field and the current version stays; a save on `DRAFT` may leave them empty; a read after `closes_at` shows `EXPIRED` with no write (D10); `run_jobs` persists `EXPIRED`, audits it and publishes `opportunity.changed`; a job for a moved `closes_at` does nothing; a mutation after `closes_at` is `INVALID_TRANSITION`
- [X] T015 [P] [US1] Write `applications/temuriset-api/tests/integration/intake/test_handoffs.py`: following an `EXTERNAL` route records one event and returns the URL with `submitted: false` (AC24); a retried key records one event; `IN_APP` and `NONE` routes are `CONFLICT`; no profile is `NOT_FOUND`; `javascript:` as `external_url` is refused on save; `opportunity_id` in the handoff body is refused (D3)
- [X] T016 [P] [US1] Write `applications/temuriset-api/tests/unit/intake/test_states.py` for `TRANSITIONS` and `effective_status` at, before and after `closes_at`, using a fixed time

### Implementation for User Story 1

- [X] T017 [US1] Implement profile save and read in `applications/temuriset-api/app/intake/service/service.py`: `check_context`, `require`, the first-save rule from D17, `check_expected`, always `OWNER_CONFIRMED`, labels and an `availability` block separate from `thesis`, audit and `partner.changed` in one transaction
- [X] T018 [US1] Add `IntakeService.record_directory_profile` in `applications/temuriset-api/app/intake/service/service.py` for `SOURCE_REPORTED` with `UNCONFIRMED` intake, with no route (D6)
- [X] T019 [US1] Add `GET` and `PUT /partners/{party_id}` to `applications/temuriset-api/app/intake/router.py`, with `idempotent("partners.save")` and an `operation_id` in the save response, and register the router in `applications/temuriset-api/app/main.py`
- [X] T020 [US1] Implement opportunity create and save in `applications/temuriset-api/app/intake/service/service.py`: version 1 as draft, a `_require_ready` check for the D1 fields and the saved profile that runs before any save on `ACTIVE` or `PAUSED`, next version per D1 with `current_version_id` moved in the same transaction, requirements written with their version, `financial` validated (subject, basis, period, `months` from 1 to 120 for `total_period`, currency, `min >= 0`, `max >= min`, non-cash and terms text, amounts as strings)
- [X] T021 [US1] Implement `TRANSITIONS`, `effective_status` and activate, pause and close in `applications/temuriset-api/app/intake/service/service.py`: activate moves `DRAFT` or `PAUSED` to `ACTIVE` after `_require_ready`; `operation_id` reaches the response (D14); audit and `opportunity.changed` commit with the change
- [X] T022 [US1] Implement read, version read and list in `applications/temuriset-api/app/intake/service/service.py`: own list by default, `partner_party_id` for another partner's non-draft opportunities, computed status, and others reading the current version only
- [X] T023 [US1] Add `POST` and `GET /opportunities`, `GET` and `PUT /opportunities/{opportunity_id}`, `GET /opportunities/{opportunity_id}/versions/{number}`, and `POST /opportunities/{opportunity_id}/activate`, `/pause` and `/close` to `applications/temuriset-api/app/intake/router.py`, with an `idempotent(...)` operation of its own on create, save and each status change, as in `app/needs/router.py` (D14)
- [X] T024 [US1] Implement `kind`, the `general_intake_version_id` pointer, the label and `IntakeService.target_availability` per the availability table in `applications/temuriset-api/app/intake/service/service.py`, with a docstring saying 019 and 023 call it. Expose it as `target_availability` and `general_intake_label` in the reads from T022, reading the profile once per list to avoid N+1 queries (D7, D8, D16)
- [X] T025 [US1] Register job `intake.expire_opportunity` in `applications/temuriset-api/app/intake/service/jobs.py`, enqueue it at activation and when `closes_at` moves, and import the module in `applications/temuriset-api/app/worker/__main__.py`
- [X] T026 [US1] Implement handoff recording in `applications/temuriset-api/app/intake/service/service.py` and `POST /partners/{party_id}/handoffs` in `applications/temuriset-api/app/intake/router.py`, append-only and with an audit event (D3)
- [X] T027 [US1] Add `load_recipients` to `applications/temuriset-api/tests/factories/recipients.py`, creating A–D through the API, which calls `IntakeService`, saving each profile before activating its opportunities, and E through `record_directory_profile` with an organization owned by a test operator account

**Checkpoint**: AC22–AC25 pass, except that AC23's pitch attempt waits for 023 (D8)

---

## Phase 4: User Story 2 - Requirements are typed and visible (Priority: P1)

**Goal**: Every saved requirement has a known operator and value shape, and an applicant can read every one that may block submission

**Independent Test**: Save one requirement per operator, an unknown operator and a narrative text. Then read the active opportunity as another party.

**Depends on**: T020 and T022 for the save and read paths. T028 and T030 can start earlier.

### Tests for User Story 2 ⚠️

- [X] T028 [P] [US2] Write `applications/temuriset-api/tests/unit/intake/test_requirements.py`, parametrized over the eight operators with valid and invalid value shapes: `equals` scalar, `in_set` and `intersects` non-empty lists, `minimum` and `maximum` decimal strings, `range_overlap` needing a comparable `financial`, `exists` true, `manual_review` no value; an unknown field prefix with a typed operator is refused; no operator normalizes to `narrative`, `manual_review`, `value: null`, `mandatory: false`; `narrative` with a typed operator is refused (D15)
- [X] T029 [P] [US2] Write `applications/temuriset-api/tests/integration/intake/test_requirements_api.py`: an unknown operator is refused and nothing is written (scenario 1); a narrative requirement is stored per D15 (scenario 2); another party reading an active opportunity sees label, reason, `applies_at`, `verification_mode`, `visibility` and `version` on every blocking requirement (scenario 3); mandatory with `PARTNER_ONLY` is refused (D9); `PARTNER_ONLY` rows reach the owner only, on read and through `?partner_party_id=`; activation, or a save on an active opportunity, without a reason on a blocking requirement is refused and the current version stays (D1)
- [X] T030 [US2] Extend `applications/temuriset-api/tests/unit/intake/test_recipients_data.py` so every recipient requirement passes validation, A1's certificate applies at `COMMERCIALIZATION`, C1's at `SUBMISSION`, and no `current` operator or `doc:` field remains (SC-001)

### Implementation for User Story 2

- [X] T031 [US2] Implement operator, value-shape and per-field rules in `applications/temuriset-api/app/intake/service/requirements.py`, returning per-field errors in the `FieldsInvalidError` shape, with fields `stage`, `relationship`, `budget`, `contribution`, `authority`, `entity`, `document:*`, `feature:*`, `narrative`, and the D15 normalization
- [X] T032 [US2] Call the validator from save and activation in `applications/temuriset-api/app/intake/service/service.py`: refuse on save, and add the reason on blocking requirements to `_require_ready`, so it applies at activation and on any save on `ACTIVE` or `PAUSED`
- [X] T033 [US2] Add the applicant projection in `applications/temuriset-api/app/intake/service/service.py`: drop `PARTNER_ONLY` rows for others, and derive `version` from the parent

**Checkpoint**: Both stories pass independently

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T034 Add `POST /opportunities` to `NOT_DATA_ROUTES` in `applications/temuriset-api/tests/integration/test_isolation.py`, because a stranger creates their own record and gets `201`. Add every other new route to `ROUTES`, with an `Idempotency-Key` where the route needs one, add `opportunity_id` to `Owner`, create a draft opportunity and no profile in the `owner` fixture (D4), and add the id to the secret list
- [X] T035 [P] Write `applications/temuriset-api/tests/integration/intake/test_failure_paths.py`, per rules 003 and 008: for a refused requirement, an invalid transition and a handoff conflict, assert message, code, `request_id`, the recorded failure, recovery, and that a fake secret in the input appears nowhere
- [X] T036 Run `make openapi` in `applications/temuriset-api/` to refresh `contracts/openapi.json`, then `make generate-api` in `applications/temuriset-web/`, and commit the drift. Change no manifest capability or registry entry (Flips: none)
- [X] T037 [P] Confirm `docs/error-handling/catalog.md` needs no row (D11), and add one only if implementation introduced a code
- [X] T038 [P] Update `docs/roadmap/architecture.md`: extend the `partner_profiles`, `opportunities` and `requirements` rows, add `external_handoffs`, narrow the draft-successor sentence at line 128 to published inventions, and record D1, D2, D9, D13 and D16
- [X] T039 Update `specs/016-partner-intake-api/spec.md` and `plan.md`: the contract's full field list with `basis` and `months` in `financial` and `target_availability`, the three status routes, the operator mapping, the handoff route, `service/jobs.py`, and **Status** to `Built, awaiting review`
- [X] T040 [P] Add `tests/integration/intake/` and `tests/unit/intake/` rows to the test table in `applications/temuriset-api/README.md`
- [X] T041 From this project folder, run `python3 docs/roadmap/check_traceability.py`, then `make check`, read the output, and name the runtime exercised in the PR description

---

## Requirement coverage

| Requirement | Tests | Implementation |
|---|---|---|
| AC22, FR-001 | T012 | T017, T018 |
| AC23, FR-004 | T012 | T024 |
| AC24 | T015 | T026 |
| AC25, FR-002 | T013 | T020–T023 |
| FR-003, US2 scenarios 1–3 | T028, T029 | T031–T033 |
| Personal-party investor, no invented facts | T011 | T007, T017 |
| States, expiry, versions on edit | T013, T014, T016 | T020, T021, T025 |
| SC-001 factories | T010, T030 | T009, T027 |
| Isolation, failure paths, contract | T034, T035 | T036 |

---

## Dependencies & Execution Order

- **Setup → Foundational → US1 → US2 → Polish.**
- **US2 depends on US1** for T020 and T022, because requirements are saved and read with opportunities. Only T028 and T030 can start earlier.
- **T019 and T023 break `test_every_route_is_covered`** until T034 lands. This is intended, so T034 must land in the same PR.
- **T027 needs T017, T018, T020 and T021.** T025 needs T021. T024 needs T017 and T022.
- **Within a story**: tests, then service, then routes.
- **Later specs**: 017 needs the routes and D1. 018 consumes D12's topics. 019 and 021 reuse T009 and T027. 023 calls `target_availability`.

### Parallel Opportunities

- T002 with T001
- T006, T009 and T010 after T005
- T011–T016, all separate test files
- T028 and T029
- T035, T037, T038 and T040

`service.py` and `router.py` are shared, so their tasks run in order.

## Parallel Example: User Story 1

```text
Task: "Write tests/integration/intake/test_partner_profiles.py"
Task: "Write tests/integration/intake/test_intake_availability.py"
Task: "Write tests/integration/intake/test_opportunities.py"
Task: "Write tests/integration/intake/test_opportunity_states.py"
Task: "Write tests/integration/intake/test_handoffs.py"
Task: "Write tests/unit/intake/test_states.py"
```

## Implementation Strategy

1. Finish Setup and Foundational, and check that the migration runs both ways.
2. Finish US1, then stop and run its independent test. This is the smallest slice that 017 can build on.
3. Finish US2. Requirements stay unvalidated until T032, so **do not open the PR before this point**: both stories are P1, and the plan treats them as one PR.
4. Finish Polish and land one commit for this spec, as M3 did: `feat(temuriset): add partner intake API (spec 016)`.

## Notes

- Test docstrings use the Condition/Expected format from rule 003. Integration tests go through HTTP, except the service-only path in T018.
- Authorize through `app/access/service/policy.py` only.
- Other parties' reads follow `PortfolioService.public_view`: an explicit public projection, never the owner's response.
- `.specify/scripts/bash/check-prerequisites.sh` fails here for two reasons: it refuses this branch name ("Not on a feature branch"), and with `SPECIFY_FEATURE` set it looks for `specs/` at the git root (`pertanian/`) and reports "Feature directory not found". `speckit-implement` runs the same check, so give it this feature folder by hand or fix the script in a separate change.

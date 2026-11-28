# Tasks: TKT foundation (data, contract, Toggletip, split dictionary)

**Input**: Design documents from `applications/generic/temuriset/specs/055-tkt-foundation/` (`spec.md`, `plan.md`), `docs/roadmap/revamp-2-demo-feedback.md`, `docs/roadmap/architecture.md`, and `.specify/memory/constitution.md`.
**Branch**: `f/055-tkt-foundation` | **Track**: B, day 1 | **Unblocks**: 056, 057

**Tests**: Included per `plan.md` Tasks & Constitution Principle 2 (Test-first reliability).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Exact file paths relative to repository root (`applications/generic/temuriset/...` and `docs/generic/temuriset/...`)

---

## Phase 1: Foundational Schema & Migration (Blocking Prerequisites)

**Purpose**: Expand-only database schema and ORM models required by all backend stories.

- [X] T001 Create Alembic migration `0026_tkt_readiness.py` (`revision = "0026"`, `down_revision = "0025"`) in `applications/generic/temuriset/applications/temuriset-api/migrations/versions/0026_tkt_readiness.py` adding new table `invention_readiness` (`id`, `created_at`, `updated_at`, `version`, `version_id` FK `invention_versions.id` `ON DELETE CASCADE` unique, `tkt_level` smallint `CHECK (tkt_level BETWEEN 1 AND 9)`, `note` text `CHECK (length(note) <= 500)`, `evidence_version_id` FK `document_versions.id` `ON DELETE SET NULL` nullable) and nullable smallint column `opportunity_versions.min_tkt` with NO check constraint on `opportunity_versions`
- [X] T002 [P] Add `InventionReadinessRecord(MutableRow, Base)` to `applications/generic/temuriset/applications/temuriset-api/app/portfolio/repository/sqlalchemy/models.py` matching migration 0026
- [X] T003 [P] Add `min_tkt: Mapped[int | None] = mapped_column(SmallInteger)` to `OpportunityVersionRecord` in `applications/generic/temuriset/applications/temuriset-api/app/intake/repository/sqlalchemy/models.py`
- [X] T004 Verify migration upgrade -> downgrade -> upgrade and `alembic check` clean against local Postgres 16

**Checkpoint**: Schema expanded safely without adding constraints to any existing table.

---

## Phase 2: User Story 1 - TKT travels with the invention version (Priority: P1) 🎯 MVP

**Goal**: Owners can save optional TKT 1–9, note (<= 500 chars), and owned AVAILABLE evidence file on an invention draft; publishing freezes it; starting a successor draft copies it; non-owners and public/discovery/teaser projections see level, note, `SELF_DECLARED`, and `has_evidence` only, never `evidence`.

**Independent Test**: `pytest tests/integration/portfolio/test_readiness.py` verifies save, validation errors (`tkt_level` 0/10, note > 500, unowned/unavailable evidence -> `FILE_NOT_AVAILABLE`), publish freeze, copy to successor draft, clearing with `null`, erased evidence -> `null`, and privacy across owner view, public view, discovery card, and teaser.

### Tests for User Story 1 (Write FIRST)

- [X] T005 [P] [US1] Write unit & integration tests covering readiness schema validation, save, publish freeze, copy on new draft, evidence ownership/availability check, erased evidence handling, and non-owner/public/discovery/teaser projection privacy in `applications/generic/temuriset/applications/temuriset-api/tests/integration/portfolio/test_readiness.py`

### Implementation for User Story 1

- [X] T006 [P] [US1] Add `owned_document_version(session, owner_party_id, document_id, number) -> UUID` (accepting any AVAILABLE file owned by `owner_party_id`, raising `FileNotAvailableError` otherwise) and `available_document_version_number(session, version_id) -> tuple[UUID, int] | None` (returns None if missing or not AVAILABLE) in `applications/generic/temuriset/applications/temuriset-api/app/documents/service/service.py`
- [X] T007 [P] [US1] Add `DocumentVersionChoice`, `ReadinessInput` (`extra="forbid"`, `tkt_level: int = Field(ge=1, le=9)`, `note: str = Field(default="", max_length=500)`, `evidence: DocumentVersionChoice | None = None`), `ReadinessResponse` (`tkt_level`, `note`, `provenance: Literal["SELF_DECLARED"] = "SELF_DECLARED"`, `has_evidence: bool`, `evidence: DocumentVersionChoice | None = None`), `DraftRequest.readiness: ReadinessInput | None = None`, `InventionVersionResponse.readiness: ReadinessResponse | None = None`, and `PublicInventionResponse.readiness: ReadinessResponse | None = None` in `applications/generic/temuriset/applications/temuriset-api/app/portfolio/model/schema.py`
- [X] T008 [US1] Update `SqlAlchemyPortfolioRepository` (`version`, readiness read/upsert/delete/copy helpers) in `applications/generic/temuriset/applications/temuriset-api/app/portfolio/repository/sqlalchemy/repository.py` and `PortfolioService` (`save_draft` saving/clearing/copying readiness on successor draft, `public_view` stripping `evidence` while preserving `has_evidence`) in `applications/generic/temuriset/applications/temuriset-api/app/portfolio/service/service.py`
- [X] T009 [P] [US1] Expose `"tkt_level": view.readiness.tkt_level if view.readiness else None` in discovery invention card projection in `applications/generic/temuriset/applications/temuriset-api/app/discovery/service/projection.py`
- [X] T010 [P] [US1] Add `tkt_level: int | None = None` to `TeaserResponse` in `applications/generic/temuriset/applications/temuriset-api/app/subscriptions/model/schema.py` and populate it in `SubscriptionService._public` / `teaser` in `applications/generic/temuriset/applications/temuriset-api/app/subscriptions/service/service.py`

**Checkpoint**: User Story 1 API paths and `test_readiness.py` pass completely.

---

## Phase 3: User Story 2 - Mandates may ask for a minimum TKT (Priority: P2)

**Goal**: Partners can optionally save `min_tkt` (1–9 or null) on a mandate draft or live version; every reader of the mandate and its versions sees it; values outside 1–9 fail with `VALIDATION_FAILED` on `min_tkt`.

**Independent Test**: `pytest tests/integration/intake/test_min_tkt.py` verifies create/save with `min_tkt: 5`, clearing with `null`, versioning across live updates, reading by applicants, and rejecting `0` and `10`.

### Tests for User Story 2 (Write FIRST)

- [X] T011 [P] [US2] Write integration tests for mandate `min_tkt` create, save, version history, applicant read, and 0/10 validation rejection in `applications/generic/temuriset/applications/temuriset-api/tests/integration/intake/test_min_tkt.py`

### Implementation for User Story 2

- [X] T012 [US2] Add `min_tkt: int | None = Field(default=None, ge=1, le=9)` to `OpportunityContent` and `min_tkt: int | None = None` to `OpportunityVersionContent` (inherited by `OpportunityResponse` and `OpportunityVersionResponse`) in `applications/generic/temuriset/applications/temuriset-api/app/intake/model/schema.py`
- [X] T013 [US2] Include `"min_tkt"` in `_VERSION_FIELDS` in `applications/generic/temuriset/applications/temuriset-api/app/intake/service/service.py` so create, save, and read paths persist and echo `min_tkt`

**Checkpoint**: User Story 2 API paths and `test_min_tkt.py` pass completely.

---

## Phase 4: User Story 3 - The engine can read TKT (Priority: P1)

**Goal**: Matching engine dataclasses carry `Source.tkt: int | None = None` (lowest stated TKT across linked inventions, or None if none stated) and `Target.min_tkt: int | None = None`; scoring remains unchanged in 055.

**Independent Test**: `pytest tests/unit/matching/test_inputs_tkt.py` verifies `Source.tkt` for single invention, multiple inventions (lowest stated wins, ignoring None), no TKT (`None`), `Target.min_tkt`, and unchanged scoring outputs.

### Tests for User Story 3 (Write FIRST)

- [X] T014 [P] [US3] Write unit tests for `Source.tkt`, `Target.min_tkt`, multi-invention lowest-TKT aggregation, and unchanged `evaluate()` scores in `applications/generic/temuriset/applications/temuriset-api/tests/unit/matching/test_inputs_tkt.py`

### Implementation for User Story 3

- [X] T015 [US3] Add `tkt: int | None = None` to `Source` and `min_tkt: int | None = None` to `Target` in `applications/generic/temuriset/applications/temuriset-api/app/matching/engine/inputs.py`
- [X] T016 [US3] Populate `tkt` in `_invention_fields(versions)` (minimum stated `version.readiness.tkt_level`, or `None`) and `min_tkt=opportunity.min_tkt` in `target_of(...)` in `applications/generic/temuriset/applications/temuriset-api/app/matching/service/service.py`

**Checkpoint**: User Story 3 passes with zero changes to existing matching golden files.

---

## Phase 5: Shared Web & Design System Foundations (FR-004, FR-005, FR-006, FR-007)

**Purpose**: Deliver the shared TKT metadata module, accessible `Toggletip` component (design system + web port), per-area English dictionary split, and stable deep-link element IDs that unblock Track A (057–059) and Track B (056, 060).

- [X] T017 [P] Create `applications/generic/temuriset/applications/temuriset-web/src/features/portfolio/tkt.ts` defining `TKT_LEVELS` (levels 1–9 with Indonesian & English names, meanings, example evidence, and group), `TKT_GROUPS`, `TKT_DEFINITION`, and `tktLabel(level, stageLabel?)`
- [X] T018 [P] Write unit tests for `TKT_LEVELS`, `TKT_GROUPS`, and `tktLabel()` in `applications/generic/temuriset/applications/temuriset-web/tests/tkt-levels.test.ts`
- [X] T019 Add `.tr-tip` styles (using design tokens only, zero raw hex/rgb) to `docs/generic/temuriset/design-system/project/components/bundle.css`, `TR.Toggletip` to `docs/generic/temuriset/design-system/project/components/bundle.js` (including `@ds-bundle` header), type declarations to `docs/generic/temuriset/design-system/project/components/index.d.ts`, and docs/demo entry to `docs/generic/temuriset/design-system/tools/catalog.mjs`; run `node tools/build.mjs` in `docs/generic/temuriset/design-system` and `make design` in `applications/generic/temuriset/applications/temuriset-web`
- [X] T020 Implement web port `Toggletip` (`{ label: string; children: ReactNode; id?: string }`, 24 px info button with `aria-expanded`, `aria-controls`, accessible name `"Penjelasan: {label}"`, `role="status"` content region, opens on click/Enter, closes on Escape/outside click) in `applications/generic/temuriset/applications/temuriset-web/src/components/tr/Toggletip.tsx`
- [X] T021 [P] Write unit & axe accessibility tests for `Toggletip` in `applications/generic/temuriset/applications/temuriset-web/tests/toggletip.test.tsx`
- [X] T022 Split `applications/generic/temuriset/applications/temuriset-web/src/features/i18n/app-en.ts` into `src/features/i18n/app-en/{core,tkt,matching,finder,mail}.ts` merged by `app-en.ts` (adding `"Penjelasan: {label}"` and TKT strings to `tkt.ts`), keeping `tests/app-i18n.test.tsx` passing unchanged
- [X] T023 [P] Add missing stable deep-link element IDs (`#tkt`, `#fakta`, `#dokumen` in `src/views/portfolio/EditorView.tsx`; `#kisaran`, `#bentuk` in `src/features/needs/SupportForm.tsx`; `#baru` in `src/views/needs/NeedsViews.tsx`, verifying existing `#kata-kunci`, `#sektor`, `#tahap` in `EditorView.tsx`) and assert all nine IDs exist in `applications/generic/temuriset/applications/temuriset-web/tests/deep-link-ids.test.tsx`

---

## Phase 6: Contracts, Verification & Spec Status

**Purpose**: Regenerate OpenAPI & TypeScript contracts, run full checks, and update spec status.

- [X] T024 Regenerate `applications/generic/temuriset/contracts/openapi.json` (`make openapi`) and `applications/generic/temuriset/applications/temuriset-web/src/api/schema.generated.ts` (`make generate-api`)
- [X] T025 Run full API validation (`DEMO_MODE=false make check`), migration round-trip (`alembic upgrade head && alembic downgrade -1 && alembic upgrade head && alembic check`), and migration compatibility test (`deployment/temuriset/tests/migration_compat.sh`)
- [X] T026 Run full web validation (`make check`, `make build`) and traceability check (`python3 applications/generic/temuriset/docs/roadmap/check_traceability.py`)
- [X] T027 Update `**Status**` in `applications/generic/temuriset/specs/055-tkt-foundation/spec.md` to `Built, awaiting review` and generate offline Neon migration SQL (`0025:0026`) for deployment readiness

---

## Dependencies & Execution Order

- **Phase 1 (T001–T004)** blocks Phases 2, 3, and 4.
- **Phase 2 (US1)**, **Phase 3 (US2)**, **Phase 4 (US3)**, and **Phase 5 (Web/Design System)** can largely proceed in parallel once Phase 1 finishes (US3 depends on T007/T012 schemas).
- **Phase 6 (T024–T027)** depends on all earlier phases completing.

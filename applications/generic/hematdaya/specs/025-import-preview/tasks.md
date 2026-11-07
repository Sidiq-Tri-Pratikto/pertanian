# Tasks: Import preview

**Input**: `specs/025-import-preview/spec.md`, `plan.md`, generated against `origin/main` at `a952723`
**Branch**: `m5/csv-parser`, stacked on 024 (D1)
**Lane**: P2, roadmap round 2, internal MVP. P1 reviews the contract and the two read methods added to `app/measurements/`.
**Prerequisites**: 024's T039 passes in this branch. 004, 005, 006, 008 and 021 are merged.
**Tests**: Required and first (constitution principle 2, roadmap step 4). Each phase writes its tests, then a checkpoint task runs them and records the failure, and only then writes the code. Tests follow rule 003. Failure paths assert message, code, response, `request_id`, the record, recovery and fake secrets (rule 008).

**Paths** start at `applications/generic/hematdaya/`. Commands run from `applications/hematdaya-api/`. `domain.js` means `docs/reference/prototype/hematdaya-domain.js` and `domain.test.js` means `docs/reference/prototype/domain.test.js`. Line numbers refer to those files at `a952723`. The DDL, API shape and handoff to 026 are in [plan.md](plan.md).

## Decisions resolved against the code

| ID | Decision | Why |
|---|---|---|
| D1 | 025 stacks on 024 in this branch. Land both in one PR with one commit per spec, merged with a merge commit. T001 checks 024 is complete before anything starts. | `docs/roadmap/README.md` forbids building on the partner's unmerged branch, and round 2 assigns both specs to one person, to merge before round 3. PR #25 (004–011) and PR #26 (020–021) did the same, one commit per spec. A squash merge, which the constitution names, would collapse the two commits, so the owner should choose that knowingly. |
| D2 | The seven parser modules stay free of M1 (024's D1). Everything else in `app/imports/` calls other modules through services and models only: `SiteService`, `AssetService.snapshot`, `IngestService` and the pure functions in `app/measurements/service/normalize.py`. `dependencies.py` wires them with `SiteServiceDep`, `AssetServiceDep` and `build_ingest_service(session)`. T007 fails on any import of another module's `repository`. | `docs/roadmap/architecture.md`: a module imports another module's service interface, never its repository. |
| D3 | Add two read methods to `IngestService`, backed by the existing `MeasurementRepository`: `current_rows(source_id, identity_keys)` and a new `stored_intervals(source_id, start, end)`. The SQL reads `current_measurements`, where `energy_mwh IS NOT NULL AND interval_start < :end AND interval_end > :start`, ordered by `interval_start`. | Classification needs stored rows, and D2 forbids the repository. `IngestService` has no read method today. P1 owns the module, so this diff goes to P1's review. |
| D4 | 006 is the classification authority. Every `parsed` row becomes `ReadingInput(value=row.value, unit=row.unit, interval_start=..., interval_end=..., measured_at=...)` with `source_record_id=None`, then `normalize(reading, MeasurementKind(row.kind.value))`. Identity is the returned `identity_key`, and "same" is `MeasurementRow.same_observation`. `energy_mwh` above `2**63 - 1` makes the row invalid with `value_too_large`. A `ReadingRejectedError` means 024 and 006 disagree, so it propagates to `APP-UNKNOWN`. | The prototype compares mWh only, but `same_observation` also compares `raw_value` and `raw_unit`, so a preview "duplicate" could become a revision at commit. Storage is integer mWh in BIGINT, and `normalize` has no bound for W × seconds. |
| D5 | The preview is the only guard against overlap, so it must be exact. `measurements` has `UNIQUE (source_id, identity_key, revision)` and no exclusion constraint. Two overlapping intervals have different identities and would both be stored and summed. Precedence per row group: invalid, then in-file changed value, then in-file overlap, then stored changed value, then stored overlap, then stored exact repeat, then accepted first and duplicates after. Adjacent half-open intervals do not overlap. Only interval kinds take part in overlap. | 006's `ingest` turns a changed value at one identity into a new revision, which the spec forbids here: it must be a blocking conflict. So nothing the preview accepts may reach that path. |
| D6 | A file stream resolves to a stored source through its asset, with a fixed label: `source_label(stream_key) = f"Impor CSV · {stream_key}"`. A source matches when it is bound to the target asset, `origin == import`, `measurement_kind` equals the row kind and `label` matches. Any other source whose binding overlaps the file's period for that stream is `other_source`, so the user must choose. Closed bindings before the period do not count. A `new` target has no stored source. Stream and asset must be one to one: a stream with two names, or two streams on one asset, is a blocking question. | `sources` has no stream identity column and labels have no update path, so the label is stable. It stays within `char_length(label) BETWEEN 1 AND 120` (12 + 60). Time-awareness matches `bindings_one_authority`, which 026 must also respect when it ends a binding (plan.md, Handoff). |
| D7 | The preview reads revisions first: `owned_site` returns the site, then `snapshot`, then stored rows. It takes no site lock. | One request runs at READ COMMITTED, so reads do not share a snapshot. Reading revisions first means a write landing mid-preview makes the stored revision older, and 026's revalidation refuses it, which is the safe direction. Reading them last could hide that write. The seeded plan's "same snapshot" is not achievable without a lock held across parsing. |
| D8 | `POST /sites/{site_id}/imports/preview` takes `request: Request`, not `UploadFile` or `Form`. Its order is `service.owned_site`, then `Request(scope, counting_receive)`, then `await limited.form(max_part_size=BODY_LIMIT)`. `BODY_LIMIT` is 10 MiB + 64 KiB, and exceeding it raises `ImportTooLargeError` with no further reading. OpenAPI comes from `openapi_extra`. `file` part or `text` field, plus `mapping` as JSON text validated with `ImportMappingRequest.model_validate_json`. A `ValidationError` becomes `RequestValidationError`, giving the normal 422. Pasted text is encoded as UTF-8. Both parts together is `RequestInvalidError`, and neither is `empty_input`. Files arrive as seekable temp files, so the parser's own check gives the exact size message. | FastAPI parses declared form bodies before dependencies (`fastapi/routing.py` L455 before L511), so a declared `File` would read a foreign user's whole upload, and a JSON-less call would answer 422 instead of 404, which `FOREIGN_ROUTES` forbids. Starlette has no total body limit, and `max_part_size` defaults to 1 MiB, which would reject large pastes. |
| D9 | `python-multipart` is a new runtime dependency. | `request.form()` needs it, and it is absent from `pyproject.toml` and `uv.lock`. Declaring a form route without it fails at definition time. The constitution requires this to be justified in the PR. |
| D10 | Parsing, row staging and classification run through `asyncio.to_thread`. The session stays open but idle during that time. There is no separate parsing timeout. | Rule 006: never block the event loop. A 150,000-row file is seconds of CPU work. PRD §10.2 asks for parsing timeouts, but a thread cannot be cancelled. The byte and row caps bound the work, and T043 measures it. |
| D11 | Register `APP-IMPORT-TOO-LARGE` (413), `APP-IMPORT-STRUCTURE` (400) and `APP-IMPORT-BLOCKED` (409) in `codes.py`, `public.py` and `docs/error-handling/catalog.md`, with typed errors in `app/imports/service/errors.py`. Specific messages travel in `error.details` as `{"loc": ["file"] or ["file", "line", n], "msg": message, "type": reason}`. Add an optional `details` attribute to `AppError`, and let `handle_app_error` pass it. Record the widened EH-07 deviation in `docs/error-handling/deviation.md`. A blocked preview is a 201 with `blocked: true`, not an error. `ImportPreviewService.require_committable` raises `ImportBlockedError`, is unit-tested here and is called from a route in 026. | `handle_app_error` renders the public default and ignores `error.message` (Notes), and passes no details, so the seeded plan's "each with an Indonesian correction" cannot work today. `details` also carries more than one structural problem and needs no change to how messages render. Those messages hold only alias headers, line numbers and sizes, so no CSV value reaches an error response. |
| D12 | Foreign `site_id` or `import_id` gives `NOT_FOUND`, before any body is read. `GET` routes load the import by ID, then call `sites.get_owned(import.site_id, principal)`. An `asset_map` UUID that is not an active asset of this site also gives `NOT_FOUND`. All three routes join `FOREIGN_ROUTES` in `tests/integration/test_isolation.py`. | `architecture.md`: a resource owned by someone else returns `NOT_FOUND`. That table's own rule: every data route joins it in the spec that adds it. |
| D13 | Import is core, so no route calls `CapabilityGuard`. It must work under `COMPOSITION=core-only`, proved by adding the import tests to the core-only CI step. The manifest's `csv` adapter stays `planned` until 026. | 011's plan: "Demo/CSV and core rules must remain independent of the optional guard" and later CSV specs provide the core-only evidence. 025's **Flips** is none. |
| D14 | `make openapi` from the API, then `make generate-api` from `applications/hematdaya-mobile/`, and commit `contracts/openapi.json` and `src/api/schema.generated.ts`. | CI drift-checks both files. No mobile screen changes here. |
| D15 | Migration file `migrations/versions/0008_create_imports.py`, `revision = "0008"`, `down_revision = "0007"`, using the raw-SQL `_execute` helper, so no `;` inside any SQL string. Import the ORM module in `migrations/env.py`. If P1 merges a migration first, take the next number and re-point `down_revision`. | The seeded plan's `0009` is stale: the head is `0006_create_insights.py`. `tests/unit/core/test_migrations.py::test_single_migration_head` asserts at most one Alembic head and fails until the later migration is re-pointed. It does not check numbering or downgrade, so T005 and T049 check those. |
| D16 | Counts are `accepted + invalid + duplicate + conflict + pending = total`, and a `CHECK` enforces it. `pending` must be 0 unless `blocked`. `pending` rows are not staged. Threshold: `invalid * 5 <= total`, an integer. `needs_acknowledgment` is `invalid > 0 and not blocked`. | L800 uses a float with an epsilon. The seeded spec's four-term sum ignored rows waiting on an answer, and 024 yields those. |
| D17 | Previews expire after 24 hours by `wall_now()`, never `site_clock`. `GET` on an expired `previewed` import returns `status: "expired"`. Each new preview deletes up to 20 expired uncommitted imports anywhere and keeps at most 5 uncommitted per site, deleting the oldest. Committed imports are never purged by this. These are product rules, so they are constants, not settings. | `architecture.md`, two clocks: TTL uses the wall clock. No background worker exists. A demo session is an anonymous write, so a principal could otherwise store 150,000 rows per request without limit. |
| D18 | Per-principal rate limits stay with 036. | 036 FR-005 owns "import preview per principal". PRD §17's rate limit is therefore not met until 036, and D17's cap is the interim bound. |
| D19 | `imports.site_id` is `ON DELETE CASCADE`, so demo end and purge remove imports. Demo reset needs no code: it advances both revisions, so an open preview goes stale at commit, and D6 finds no deleted source. | `DemoSessionService.end` and `_purge` call `sites.delete`. |
| D20 | Add an assumption, not a block, when accepted rows end after `site_clock(site)`: `{n} baris berakhir setelah waktu ruang kerja {date time}; baris itu belum dihitung pada ringkasan.` | The MVP's "Mulai" path uses the `empty` demo scenario with `virtual_now` fixed at 2026-10-26 00.00 WIB, and every energy read has `interval_end <= :now`. A real CSV after that date would commit and then show nothing. See Open questions. |
| D21 | Timestamp-only streams with jitter stay blocked by the overlap rule, with the `interval_overlap` message. | 024 infers cadence within ±1 second, so `[t, t + cadence)` can overlap the next row by up to a second (Notes). Blocking is the safe default. See Open questions. |
| D22 | Error pages use `limit` (1–100, default 50) and an opaque base64 cursor holding the last `data_row`. A bad cursor raises `RequestInvalidError`. `errors[]` holds `invalid` and `conflict` rows, ordered by `data_row`. | `architecture.md` list rules, and the cursor style in `app/assets/service/service.py`. Conflicts get a row message because UX-20 links errors to rows. |
| D23 | `file_name` is the upload's name, reduced to its last path segment, stripped of control characters and cut to 255, or `tempelan.csv` for a paste, as L647 does. `content_sha256` hashes the file bytes. The raw file is never stored or logged. Only row results are staged. | PRD §17. 026 needs the hash and the mapping, not the bytes. The name is display text, so cutting it hides nothing. |
| D24 | For `other_source` the only resolution is `new`, as L731 says. Source authority is then chosen in 028. PRD §10.2 item 8's "replace/skip" is not offered here. | Replacing a source needs an atomic authority change, which 028 owns. Excluding a stream is achieved by editing the file. |
| D25 | A one-row counter file is accepted with its first-reading assumption, where L803 would block it. | The prototype blocks only because its accepted list holds deltas. PRD §10.3: the first reading is an anchor, and 006 stores it. |

## Messages

Text is exact. `new` means no prototype text exists.

### Errors

| Internal code | Public code | HTTP | Default message | Trigger | retryable |
|---|---|---|---|---|---|
| `APP-IMPORT-TOO-LARGE` | `IMPORT_TOO_LARGE` | 413 | `Berkas melebihi batas impor. Perkecil menjadi paling besar 10 MiB dan 150.000 baris data lalu coba lagi.` | Body over `BODY_LIMIT`, or 024 reasons `too_large`, `too_many_rows`. `details` names the limit | false |
| `APP-IMPORT-STRUCTURE` | `IMPORT_INVALID` | 400 | `Struktur berkas belum dapat dibaca. Perbaiki hal yang disebutkan lalu coba lagi.` | Any other 024 structural reason. `details` lists them | false |
| `APP-IMPORT-BLOCKED` | `IMPORT_BLOCKED` | 409 | `Impor ini masih diblokir. Selesaikan alasan pada pratinjau lalu coba lagi.` | Commit of a blocked preview, raised from `require_committable` in 026 | false |

Over `BODY_LIMIT`, where the size is unknown, `details[0].msg` is `Ukuran berkas melebihi batas 10 MiB.` (new). Otherwise it is 024's message.

### Questions

These join 024's meaning questions in `questions[]`.

| Kind | Message | Source |
|---|---|---|
| `scope` | `Pilih apakah beban perangkat dalam berkas ini terukur terpisah.` | L722 |
| `asset_choice` | `Ada lebih dari satu perangkat bernama "{name}". Pilih perangkat yang dimaksud atau buat baru.` | L726 |
| `other_source` | `{asset} sudah memiliki sumber lain. Sumber ganda untuk satu beban tidak dijumlahkan; pilih "Buat perangkat baru" lalu tentukan sumber acuan di Cakupan & sumber.` | L731 |
| `stream_assets` | `Sumber "{stream}" dipakai oleh lebih dari satu perangkat: {names}. Pisahkan sumbernya atau samakan nama perangkatnya.` | new |
| `asset_streams` | `Perangkat "{asset}" menerima lebih dari satu sumber dalam berkas ini. Sumber ganda tidak dijumlahkan; pilih "Buat perangkat baru" lalu tentukan sumber acuan di Cakupan & sumber.` | new |

### Block reasons, in this order

| When | Text | Source |
|---|---|---|
| Any open question or `pending` row | `Lengkapi pemetaan terlebih dahulu.` | L799 |
| `invalid * 5 > total` | `Impor diblokir: {invalid} dari {total} baris tidak valid.` | L801 |
| `conflict > 0` | `Nilai berbeda ditemukan untuk sumber dan interval yang sama. Pilih sumber atau perbaiki data sebelum melanjutkan.` | L802 |
| No accepted and no duplicate rows, and nothing above | `Tidak ada baris valid yang dapat diimpor.` | L803 |

### Conflict rows

Same `Baris data {n}{ (baris file {line})}, {field}: {text}` form as 024. `field` is the value header for `conflict` and the start or timestamp header for `interval_overlap`.

| Reason | Text | Source |
|---|---|---|
| `conflict` | `nilai berbeda untuk sumber dan interval yang sama.` | new |
| `interval_overlap` | `interval bertumpang tindih dengan data lain pada sumber yang sama.` | new |

### Assumptions, in this order

| When | Text | Source |
|---|---|---|
| Timestamp-only, not counter | `Timestamp adalah awal interval; setiap baris mencakup interval yang disimpulkan per sumber, termasuk baris terakhir. Jeda panjang tetap menjadi data kosong.` If any stream declared a duration, `interval yang disimpulkan atau diisi per sumber` replaces that phrase | L806, 024's D20 |
| Naive times | `Waktu tanpa offset dibaca sebagai {timezone}.` | L807 |
| Average power | `Daya rata-rata interval × durasi = energi (100 W selama 30 menit = 50 Wh).` | L808 |
| BOM | `BOM UTF-8 dilewati.` | L809 |
| Delimiter | `Pemisah kolom: titik koma; koma sebagai desimal.` or `Pemisah kolom: koma; titik sebagai desimal, koma desimal hanya dalam tanda kutip.` | L810 |
| Ignored columns | `Kolom tidak dipakai: {names joined by ", "}.` | L811 |
| Blank lines | `{n} baris kosong tidak dihitung sebagai baris data.` | L812 |
| Counter decrease | `Penghitung {name} kembali ke nilai lebih kecil pada {date time}: interval {gap} tidak diketahui (segmen baru).` | L778 |
| Counter first reading | `Pembacaan pertama {name} menjadi titik awal penghitung, bukan energi.` | L781 |
| Rows after product time | D20's text | new |

`{date time}` and `{gap}` port `fmtDateTime` and `fmtGap` (L61–L66) in the site timezone: `20 Oktober 2026 02.00`, and `20 Oktober 2026 01.00–02.00`.

## Prototype assertions: what moves where

| Assertion | `domain.test.js` | Here | Elsewhere |
|---|---|---|---|
| AT-27a `blocked` until confirmed | L129 | `blocked: true` from the question | Question text in 024 |
| AT-27b `tidak diketahui` | L140 | Assumption text | Points in 024, delta in 006 |
| AT-30 all counts, ack, threshold | L220–L226 | Everything, including `Impor diblokir: 3 dari 10 baris tidak valid.` | First-error text in 024 |
| AT-32 `invalid === 1` | L260 | `invalid_rows == 1` | Message and limits in 024 |
| AT-33/34 duplicates, conflict | L276–L280 | `duplicate_rows == 10`, `accepted_rows == 0`; `conflict_rows == 1`, `blocked` | Commit, replay and interruption (L268–L275) in 026 |

---

## Phase 1: Setup

**Purpose**: Confirm the stack and add the one new dependency.

- [X] T001 Confirm `applications/hematdaya-api/app/imports/service/parser.py` exists and `uv run pytest tests/unit/imports -q` passes (024's T039). Run `make run-dependencies`, `make migrate` and `uv run alembic heads`, and record that the head is `0006` in this file's Notes section. If it is not `0006`, apply D15
- [X] T002 Run `uv add python-multipart` in `applications/hematdaya-api/` (changes `pyproject.toml` and `uv.lock`), and record the version and D9's justification in Notes for the PR

## Phase 2: Foundational

**Purpose**: Errors, storage and stored-data reads that every story uses.

### Tests first

- [X] T003 [P] Add to `applications/hematdaya-api/tests/unit/core/test_errors.py`: a typed error with `details` renders them in the envelope with its public code and message, and exactly one record shares the `request_id`; a typed error without `details` still has no `details` key
- [X] T004 [P] Write `applications/hematdaya-api/tests/unit/imports/test_import_errors.py`. For each code in the Errors table, parametrized: the typed error from `app/imports/service/errors.py` renders the exact public code, status and message, `recovery == {"retryable": False}`, one record whose `reference_id` equals `request_id`, and fake `Bearer RAHASIA-PALSU-123` and `fake@example.com` in the cause appear in no response or record. Each code has a row in `docs/error-handling/catalog.md` (read it from the test, `Path(__file__).resolve().parents[5]`). `require_committable` raises `ImportBlockedError` for a blocked preview, and returns for one that is not
- [X] T005 [P] Write `applications/hematdaya-api/tests/integration/test_import_storage.py` against `SqlAlchemyImportRepository`: round trip of an import and its rows; `CHECK` refuses counts that do not reconcile, an unknown status and a conflict row with no message; deleting the site removes imports and rows; `idempotency_key` is unique per site and repeatable across sites; error rows page in `data_row` order; purge removes expired `previewed` imports and never `committed` ones; the per-site cap keeps the newest 5. Also run a downgrade and upgrade of `0007` once with `alembic downgrade 0006` and `alembic upgrade head` through `subprocess`, as `conftest.py` does
- [X] T006 [P] Add to `applications/hematdaya-api/tests/integration/test_measurements.py`: `IngestService.current_rows` returns current revisions by identity through the service; `stored_intervals` returns only intervals overlapping the half-open window, excludes adjacent ones, excludes `energy_mwh IS NULL` points, uses the current revision only, and is scoped to one source
- [X] T007 [P] Add to `applications/hematdaya-api/tests/unit/imports/test_module_boundary.py`, leaving 024's purity test unchanged: walk every `app/imports/**/*.py` and fail on an import of any module path containing `.repository` whose root is not `app.imports` (D2). Parametrized samples prove it flags `from app.measurements.repository.base_repository import MeasurementRepository` and allows `from app.imports.repository.base_repository import ImportRepository`. This is a guard: its samples prove it can fail, and it passes from the start
- [X] T008 Run T003–T006 and confirm each fails on missing behavior. Record it in Notes for `applications/hematdaya-api/tests/`

### Code

- [X] T009 Read `.specify/memory/error-handling.md` (a boundary changes here), then add `details: list[dict] | None = None` to `AppError` in `applications/hematdaya-api/app/core/errors/base.py` and pass `details=error.details` in `handle_app_error` in `app/core/errors/handlers.py`. Do not change how `message` renders (Open questions, item 3). T003 passes
- [X] T010 Add the three codes to `applications/hematdaya-api/app/core/errors/codes.py` and their rows to `PUBLIC_ERROR_BY_CODE` in `public.py`, exactly as in the Errors table. Write `ImportTooLargeError`, `ImportStructureError` and `ImportBlockedError` in `app/imports/service/errors.py`, taking `details`. Add three rows to `docs/error-handling/catalog.md`. Widen the EH-07 row in `docs/error-handling/deviation.md` to cover import failures, citing T004 as evidence. T004's code and catalog checks pass
- [X] T011 Write `applications/hematdaya-api/migrations/versions/0008_create_imports.py` with the DDL in plan.md's Data Model, `revision = "0008"`, `down_revision = "0007"`, and a working `downgrade`, using `_execute` as `0006_create_insights.py` does. Confirm `uv run alembic heads` shows one head and `uv run pytest tests/unit/core/test_migrations.py` passes
- [X] T012 Write `ImportRecord` and `ImportRowRecord` in `applications/hematdaya-api/app/imports/repository/sqlalchemy/models.py`. Add `ImportStatus`, `ImportModel` and `ImportRowModel`, plain Pydantic with no M1 import, to `app/imports/model/models.py`. Import the ORM module in `migrations/env.py` as the others are
- [X] T013 Write `ImportRepository` in `applications/hematdaya-api/app/imports/repository/base_repository.py` and `SqlAlchemyImportRepository` in `app/imports/repository/sqlalchemy/repository.py`: `add_import`, `add_rows` (bulk `insert`, 5,000 per batch, as `SqlAlchemyMeasurementRepository.insert` does), `get_import`, `error_page(import_id, after_row, limit)`, `delete_expired(now, limit)`, `keep_newest_uncommitted(site_id, keep)`. It flushes and never commits. T005 passes
- [X] T014 Add `stored_intervals` to `MeasurementRepository` in `applications/hematdaya-api/app/measurements/repository/base_repository.py` and `app/measurements/repository/sqlalchemy/repository.py` with D3's SQL, and add `current_rows` and `stored_intervals` to `IngestService` in `app/measurements/service/service.py`, each with a Google-style docstring stating it takes no lock. T006 passes
- [X] T015 Add `make_import(site, *, status="previewed", expires_at=None) -> UUID` to `applications/hematdaya-api/tests/integration/conftest.py`, inserting one import with reconciled counts and one invalid row

## Phase 3: User Story 1 - See the result before anything is saved (Priority: P1) MVP

**Goal**: A preview is stored and readable, with reconciled counts, thresholds and assumptions, and nothing else changes.

**Independent Test**: `uv run pytest tests/unit/imports/test_classify.py -k counts tests/integration/test_import_preview.py -k saved`. Preview leaves `measurements` unchanged.

### Tests first

- [X] T016 [P] [US1] Write `applications/hematdaya-api/tests/unit/imports/test_classify.py`, counts tests for pure `summarize(counts, *, open_questions) -> PreviewSummary`. Port AT-30 (`domain.test.js` L218–L227, `CSV10`): 2 of 10 invalid gives 8 accepted, `needs_acknowledgment`, not blocked; 3 of 10 gives `Impor diblokir: 3 dari 10 baris tidak valid.`; the sum reconciles. Boundaries: 1 of 5 passes, and 1 of 4 blocks with `invalid * 5 <= total` in integers; an open question gives `Lengkapi pemetaan terlebih dahulu.`; pending rows block; 2 of 10 invalid with an open question is blocked with `needs_acknowledgment` false, so skipped rows waive nothing; no accepted and no duplicates gives `Tidak ada baris valid yang dapat diimpor.`; duplicate-only is not blocked; reasons come in the Block reasons order
- [X] T017 [P] [US1] Write `applications/hematdaya-api/tests/unit/imports/test_assumptions.py` for `build_assumptions(parsed, staged, *, now, timezone) -> list[str]`, asserting every row of the Assumptions table with exact text and order. Counter: AT-27b's 100, 130, 5 in `Asia/Jakarta` gives the decrease text with `tidak diketahui` and the first-reading text. D20: rows ending after `now` add its text. `fmtGap`: same-day, midnight-to-midnight and cross-day forms match `domain.js` L62–L66
- [X] T018 [P] [US1] Write `applications/hematdaya-api/tests/unit/imports/test_contract.py` on `app.openapi()`: the three paths exist; `POST /api/v1/sites/{site_id}/imports/preview` has a `multipart/form-data` request body with `file` (binary), `text` and `mapping`, and a 201 response of `ImportPreviewResponse`; `limit` and `cursor` are documented; every operation has the `ErrorEnvelope` default
- [X] T019 [US1] Write `applications/hematdaya-api/tests/integration/test_import_preview.py`, saved tests, posting multipart through `client`. Acting principal on an `empty` demo session (`start_demo(client, "empty")`) and on `make_site`. 201 with stored counts, and `GET /api/v1/imports/{id}` returns the same counts, errors and assumptions from a new session (survives a restart). FR-004: `measurements`, `sources`, `assets`, `bindings`, `asset_relations` and `audit_events` counts and both site revisions are unchanged. Paste via `text` gives `file_name` `tempelan.csv`, and a paste over 1 MiB is accepted (D8). Offset CSV with `scope` answered is not blocked. Naive unanswered returns `questions` with 024's message, `blocked` and `pending_rows`; answered gives accepted rows and times in UTC. 2 of 10 and 3 of 10 (`CSV10`) match AT-30. A 61-character name gives `invalid_rows == 1` (AT-32). `mapping.columns` holds the asset, time and value headers with units. Formula names are stored and returned verbatim
- [X] T020 [US1] Add failure tests to `applications/hematdaya-api/tests/integration/test_import_preview.py`, each asserting status, public code, message, `details`, `request_id`, one record, recovery, that fake `Bearer RAHASIA-PALSU-123` in the CSV is absent from logs and records, and that nothing is stored. A 10,485,761-byte file gives 413 with detail `Ukuran 10,1 MiB melebihi batas 10 MiB.`; 150,001 rows gives 413 with `150001 baris data melebihi batas 150.000 baris.`; a 20 MiB body gives 413 with `Ukuran berkas melebihi batas 10 MiB.` and is not fully read; `foo,bar` gives 400 with three details in order; invalid UTF-8 gives 400 `not_utf8`; no file and no text gives 400 `empty_input`; `file` and `text` together gives 400; bad `mapping` JSON gives 422 `VALIDATION_FAILED`. Exactly 10,485,760 bytes is accepted
- [X] T021 [US1] Add lifecycle tests to `applications/hematdaya-api/tests/integration/test_import_preview.py`. Errors: 60 invalid rows in 400 give 50 inline, `next_error_cursor`, and `GET /imports/{id}/errors` returns the rest in order; `limit=101` gives 422; a bad cursor gives 400. Expiry: past `expires_at` gives `status: "expired"`; a new preview purges it; the sixth preview removes the oldest; `committed` stays. Demo: ending the session removes imports; reset then `GET` still answers. D20's assumption on rows after `virtual_now`
- [X] T022 [US1] Add to `FOREIGN_ROUTES` in `applications/hematdaya-api/tests/integration/test_isolation.py`: `POST /api/v1/sites/{site}/imports/preview`, `GET /api/v1/imports/{import}` and `GET /api/v1/imports/{import}/errors`. Add `import` to `ids` with `make_import(site)`, and assert no new import row exists for the site after the foreign POST
- [X] T023 [US1] Write `applications/hematdaya-api/tests/integration/test_import_performance.py`, `pytestmark = pytest.mark.integration`, skipped unless `IMPORT_BENCH=1` so CI does not carry it. Post a 150,000-row file within 10 MiB through the route: assert 201 and `total_rows`, and print elapsed seconds. A second run under `tracemalloc` asserts peak under 256 MiB. No time assertion: PRD §18's target belongs to 041's benchmark server, and T043 records the number
- [X] T024 [US1] Run T016–T022, and T023 with `IMPORT_BENCH=1`, and confirm each fails on missing behavior. Record it in Notes for `applications/hematdaya-api/tests/`

### Code

- [X] T025 [US1] Write `ImportMappingRequest`, `ImportPreviewResponse`, `ImportQuestionResponse`, `AssetCandidateResponse`, `ImportRowErrorResponse`, `ImportErrorPageResponse` and `ImportPeriodResponse` in `applications/hematdaya-api/app/imports/model/schema.py`, with the fields in plan.md's API Contract and `Field()` bounds on `interval_minutes`
- [X] T026 [US1] In `applications/hematdaya-api/app/imports/service/classify.py`, write `StagedRow` (frozen, slots: positions, names, the normalized `MeasurementRow`, value and time headers) and `stage_row(row: RowResult) -> StagedRow | RowError` per D4, and `summarize` per D16 and the Block reasons table. T016 passes
- [X] T027 [US1] Write `build_assumptions` in `applications/hematdaya-api/app/imports/service/assumptions.py` with its own local-time helpers (rule 001: a second small copy of the format is fine, not a third). T017 passes
- [X] T028 [US1] Write `ImportPreviewService` in `applications/hematdaya-api/app/imports/service/preview.py`: `owned_site(site_id, principal)`, `preview(site, file, file_name, mapping)`, `get(import_id, principal)`, `errors(import_id, principal, cursor, limit)`, `require_committable(model)`. Order per D7: the site from `owned_site`, then `assets.snapshot`, then `asyncio.to_thread(parse)`. A structural error raises per the reason map in 024's Notes, with `details`. Then stage rows in a thread, then purge per D17, then store. Hash per D23, TTL by `wall_now()`, and revisions from the site read first. For now, `asset_map` values pass through and unnamed assets are `new`, with `scope` required
- [X] T029 [US1] Write `applications/hematdaya-api/app/imports/dependencies.py` and `app/imports/router.py` with the three routes per D8 and D12, `summary`, response models and `openapi_extra`, and include the router in `app/main.py` under `API_PREFIX`. T018–T023 pass
- [X] T030 [US1] Run `uv run pytest tests/unit/imports tests/integration/test_import_preview.py tests/integration/test_isolation.py -q` and `make lint`, and fix what they find in `applications/hematdaya-api/app/imports/`

## Phase 4: User Story 2 - Conflicts and duplicates (Priority: P1) MVP

**Goal**: The same interval with different values, and overlapping intervals, are never picked silently. Repeats are counted once.

**Independent Test**: `uv run pytest tests/unit/imports/test_classify.py -k rows tests/integration/test_import_preview.py -k conflicts`.

### Tests first

- [X] T031 [US2] Add rows tests to `applications/hematdaya-api/tests/unit/imports/test_classify.py` for pure `classify(staged, stored) -> list[Classified]`, built with real `normalize`. In-file: identical repeats give one accepted and the rest duplicate; `10` and `10.0` are duplicates; different values at one identity make every row in the group a conflict with the exact `conflict` message; `[00:00, 02:00)` and `[01:00, 03:00)` are both `interval_overlap`; adjacent intervals are accepted; chain `[0,10) [5,6) [8,12)` flags all three; streams do not interact; a duplicated row overlapping a third flags the whole group. Stored: same identity and `same_observation` gives duplicate; same identity with changed value or changed `raw_value` gives conflict; overlap with a stored interval gives `interval_overlap`; adjacency to stored is accepted. Counter: repeated point duplicates, changed point conflicts, points never overlap. Each row is classified once, and a precedence test covers D5's order. `energy_mwh` above `2**63 - 1` is invalid `value_too_large`. Jitter: D21's example is `interval_overlap`
- [X] T032 [US2] Add conflicts tests to `applications/hematdaya-api/tests/integration/test_import_preview.py`. Seed stored data with a helper that creates an asset, a source with `origin = import` and `source_label(stream)`, a binding and `build_ingest_service(session).ingest(...)`, committing. Reimport of the same file with `asset_map` naming that asset gives AT-33's `duplicate_rows == 10`, `accepted_rows == 0`, not blocked, and no asset, source or binding created. `CSV10` with one changed value gives `conflict_rows == 1` and `blocked`, even with zero invalid. A file overlapping a stored interval is blocked. Conflict rows appear in `errors[]`. Counts reconcile in every case
- [X] T033 [US2] Run T031 and T032 and confirm they fail on missing behavior. Record it in Notes for `applications/hematdaya-api/tests/`

### Code

- [X] T034 [US2] In `applications/hematdaya-api/app/imports/service/classify.py`, implement `classify` per D5: group by stream and identity, sort-and-sweep clusters per stream with `start < cluster_end` (O(n log n), half-open), then stored identity, then stored overlap skipping the same identity. T031 passes
- [X] T035 [US2] In `applications/hematdaya-api/app/imports/service/mapping.py` write `source_label` and `resolve_source(asset_id, stream_key, kind, snapshot)` per D6. In `preview.py`, for each stream with a resolved source, call `ingest.current_rows` and `ingest.stored_intervals`, bounded to the stream's period, then `classify`, and store statuses, messages and `parsed` for accepted rows. T032 passes
- [X] T036 [US2] Run `uv run pytest tests/unit/imports tests/integration/test_import_preview.py -q` and `make lint`, and fix what they find in `applications/hematdaya-api/app/imports/`

## Phase 5: User Story 3 - Map by identity, not name (Priority: P1) MVP

**Goal**: Names never decide identity. The user picks where it is ambiguous, and two sources are never added.

**Independent Test**: `uv run pytest tests/unit/imports/test_mapping.py tests/integration/test_import_preview.py -k identity`.

### Tests first

- [X] T037 [P] [US3] Write `applications/hematdaya-api/tests/unit/imports/test_mapping.py` for `resolve_streams(streams, request, snapshot) -> ResolvedMapping`, the port of `defaultMapping` (L701) and L722–L733. One active same-name asset, compared with `.lower()`, is the default target; none gives `new`; two give `asset_choice` with candidates carrying `id`, `name`, `location`, `category` and `scope_kind`; archived assets are never matched. Unanswered `scope` gives its question; `disjoint` and `unknown_overlap` are accepted. `other_source` exact text when a binding overlaps the stream's period, none when it closed before; an existing import source with the matching label resolves with no question; a matching label with a different kind is `other_source`. `stream_assets` and `asset_streams` exact text, including two names mapped to one asset ID. Oversized and invalid names raise no question (L725). An unknown UUID raises `NotFoundError`
- [X] T038 [US3] Add identity tests to `applications/hematdaya-api/tests/integration/test_import_preview.py`. Two `Kulkas` give `asset_choice` with both candidates and `blocked`; choosing one by ID clears it. A target with a demo-seeded source gives `other_source`; `new` clears it. Mapping to another owner's asset gives `NOT_FOUND`, with nothing stored. `scope=unknown_overlap` confirmed gives `blocked: false`, and the stored `mapping.scope` holds it. A reimport with the default mapping resolves to the earlier source and gives all duplicates. `mapping.streams` holds every field in plan.md's Data Model
- [X] T039 [US3] Run T037 and T038 and confirm they fail on missing behavior. Record it in Notes for `applications/hematdaya-api/tests/`

### Code

- [X] T040 [P] [US3] Implement `resolve_streams` in `applications/hematdaya-api/app/imports/service/mapping.py` per D6, D12, D24 and the Questions table, computing `cadence_seconds` as the rounded whole seconds of `ParsedFile.cadences`, at least 1, or `None` for counters. T037 passes
- [X] T041 [US3] In `applications/hematdaya-api/app/imports/service/preview.py`, resolve streams after staging rows and before classification, append their questions after 024's, store the `mapping` JSON and return candidates. T038 passes
- [X] T042 [US3] Run `uv run pytest tests/unit/imports tests/integration/test_import_preview.py tests/integration/test_isolation.py -q` and `make lint`, and fix what they find in `applications/hematdaya-api/app/imports/`

## Phase 6: Polish

- [X] T043 Run `IMPORT_BENCH=1 uv run pytest tests/integration/test_import_performance.py -s -q`, record elapsed seconds, peak memory, bytes and machine in this file's Notes and on the Performance line of `specs/025-import-preview/plan.md`, and compare against PRD §18's 60 seconds. If it is over, report that: the formal benchmark stays with 041, and 026's plan makes a worker its own spec
- [X] T044 Run `COMPOSITION=core-only uv run pytest tests/unit/imports tests/integration/test_import_preview.py`, then add those paths to the core-only step in `.github/workflows/hematdaya-api.yml` at the pertanian repository root, naming the step for core journeys (D13)
- [X] T045 Run `make openapi` in `applications/hematdaya-api/`, then `make generate-api` and `make check` in `applications/hematdaya-mobile/` on the Node version in `.nvmrc`, and confirm only `contracts/openapi.json` and `applications/hematdaya-mobile/src/api/schema.generated.ts` changed (D14)
- [X] T046 [P] In `applications/hematdaya-api/README.md`, add the three routes to the endpoint table and `tests/integration/test_import_preview.py` to the test table
- [X] T047 Confirm nothing flipped: `AdapterResponse(id="csv", status=CapabilityStatus.PLANNED)` is unchanged in `applications/hematdaya-api/app/capabilities/service/service.py`, `git diff --name-only origin/main` holds no 026 or 027 path, and `measurements` has no new write path
- [X] T048 [P] Set **Status** in `specs/025-import-preview/spec.md` to `Built, awaiting review`
- [X] T049 Run `python3 docs/roadmap/check_traceability.py`, then `make check` in `applications/hematdaya-api/`, `uv run alembic heads` (one head) and `SKIP=no-commit-to-branch uv run pre-commit run -c ../../.pre-commit-config.yaml --all-files`, and read the output. State which runtime was exercised: this is API only
- [X] T050 Only when the owner asks: commit as `feat(api): add the stored CSV import preview (spec 025)`, staging explicit paths, on top of 024's commit. Sync with `origin/main`, re-check T049's Alembic head, push and open one PR with `pr-generate-description` filling `.github/pull_request_template.md`. State in it D9's justification, the widened EH-07 deviation, the methods added to `app/measurements/`, and that it covers 024 and 025

## Requirement coverage

| Requirement | Tasks |
|---|---|
| FR-001 | T005, T013, T019, T028, T038 |
| FR-002 | T016, T019, T026 |
| FR-003 | T020, T029 |
| FR-004 | T019, T047 |
| FR-005 | T017, T019, T027 |
| FR-006 overlap and identity | T006, T014, T031, T034, T035 |
| FR-006 inline limit and cursor | T005, T013, T021, T028 |
| FR-007 ownership | T022, T029, T038 |
| FR-007 composition | T044 |
| FR-008 errors | T003, T004, T009, T010, T020 |
| FR-009 contract | T018, T045 |
| US1 scenarios 1–3 | T016, T019, T028 |
| US2 scenarios 1, 2 | T031, T032, T034 |
| US2 scenario 3 | T006, T014, T031, T032, T034, T035 |
| US2 scenario 4 | T016, T032, T035 |
| US3 scenario 1 | T037, T038, T040 |
| US3 scenario 2 | T037, T038, T040 |
| US3 scenario 3 | T037, T038. Refused totals are 026's, on the rule `scope_issues` already tests |
| Edge: survives a restart | T019 |
| Edge: skipped rows cannot waive | T016 |
| Edge: stale preview at commit | 026. T028 stores both revisions (D7) |
| Edge: expiry and per-site cap | T005, T021, T028 |
| Edge: one stream, one asset | T037, T040 |
| Edge: rows after product time | T017, T021 |
| Edge: demo end | T005, T021 |
| Migration and single head | T005, T011, T049 |
| SC-001, SC-002 | T016, T019, T032 |

## Dependencies & Execution Order

- **024 complete → Setup (T001–T002) → Foundational (T003–T015) → US1 (T016–T030) → US2 (T031–T036) → US3 (T037–T042) → Polish (T043–T050).**
- T011 before T012 and T013. T014 needs the existing `IngestService`. T028 needs T013, T014 and T026.
- US2 and US3 extend `classify.py`, `mapping.py` and `preview.py`, so they run in order. US2's tests name the target asset by ID, so they do not need US3's default mapping.
- T045 after T029 and any later schema change. T049 last before T050.

### Parallel example

T003, T004, T005, T006 and T007 touch different test files and can run together. So can T016, T017 and T018. T037 and T040 touch files nothing else in their phase changes, and T046 and T048 can run any time after T042.

## Implementation Strategy

All three stories are P1, and round 3's 026 needs all of them, so the MVP for this spec is the whole spec. US1 is the first review point: a stored preview for a file with no stored data. Keep to one PR with 024 (D1). Stop after each checkpoint task and read the failure before writing code.

## Notes

Record baseline results, failing-test checkpoints and the measurement here as tasks finish. The handoff to 026 is in plan.md.

### Baseline (T001, T002)

- `uv run pytest tests/unit/imports -q` at `a6451b4`: 440 passed. `make run-dependencies`, `make migrate`, `uv run alembic heads`: `0006 (head)`, and `origin/main` (`a952723`) also ends at `0006`, so D15 stands as written.
- `uv add python-multipart`: version 0.0.33. Justification for the PR is D9: `request.form()` needs it, and a form route without it fails at definition time. The lock's only new package is this one. The running `uv` also rewrote the lock's `revision` from 3 to 5 and moved the `hematdaya-api` entry into sort order.

### Failing-test checkpoints (T008, T024, T033, T039)

Each set was run and read before the code it covers was written.

| Phase | Result before the code | Passing from the start, as guards |
|---|---|---|
| Foundational | 8 failed, 24 passed, 2 collection errors. `TypeError: AppError.__init__() got an unexpected keyword argument 'details'`, `AttributeError: 'IngestService' object has no attribute 'stored_intervals'` and `current_rows`, `No module named 'app.imports.service.errors'`, `cannot import name 'ImportModel'` | T007's 30 tests, by design. `test_typed_error_without_details_has_no_details_key` |
| US1 | `test_contract.py`: 7 failed, `KeyError` on each path. `test_import_preview.py`: route tests failed on 404 and `KeyError: 'id'`. `test_classify.py` and `test_assumptions.py`: collection errors, no such names. T023: 2 failed on 404. My output filter cut the overall total line | Foreign-route rows in `test_isolation.py` that a missing route also answers with 404 |
| US2 | `test_classify.py -k rows`: 25 failed, on `no attribute 'classify'` and `'StoredStream'`. `-k conflicts`, with only `source_label` written so the file imports: 7 failed, 1 passed, on wrong counts such as `(0, 10, False) == (10, 0, False)` | `test_conflicts_adjacent_to_a_stored_interval_is_accepted` |
| US3 | `test_mapping.py`: collection error, `no attribute 'ResolvedMapping'`. `-k identity`: 7 failed, 1 passed, on `assert False is True`, `201 == 404`, `400 == 404` and wrong counts | `test_identity_unknown_overlap_is_stored_and_not_blocked` |

T023's first run also hid a test bug: it posted as one principal to another's site, so it would have answered 404 with the route present. After fixing that, I took the route out of `app/main.py`, saw both tests fail on 404 again, and restored it.

### Measurement (T023, T043)

Through the route with Postgres 17 in local Docker, on an Apple M3 with 16 GiB, Darwin 27.2.0, Python 3.13.16, for 150,000 explicit-interval rows in 9,450,044 bytes: **8.72 s**, and a `tracemalloc` peak of **156.6 MiB** (31.82 s under tracing). That is under PRD §18's 60 seconds, which also covers commit and belongs to 041, and under the 256 MiB bound. The first version of `StagedRow` held one `MeasurementRow` per row and peaked at 324.2 MiB, failing T023. See the first row below.

### Where the work differs from the text above

| Item | What changed | Why |
|---|---|---|
| T026 `StagedRow` | Holds 006's normalized fields, with `observation` rebuilding the `MeasurementRow` on request, instead of holding one per row. "Same" is still `same_observation` | Measured: a retained Pydantic row took a 150,000-row preview to 324.2 MiB against T023's 256 MiB |
| T026 `stage_row` | Takes `columns: FileColumns` as well as the row | A row message needs the value header and the header line, and a `RowResult` has neither |
| T025 `interval_minutes` | `Field()` bounds its size, key length and a 32-bit range, not 1–1440 | A 422 would swallow 024's exact question, which must still open, including for a stream absent from the file |
| D8 `mapping` part | Optional; absent means no answers yet | A first preview has none. Invalid JSON still gives the 422 |
| Assumptions table | The average-power assumption appears only once the meaning is confirmed as average | The prototype states it whenever the kind is power, which would assert what the user may have just denied |
| T040 `cadence_seconds` | A declared in-range duration decides it, ahead of the inferred cadence | The rows use the declared one (024's `_duration`), so the source must declare the same |
| D12 asset check | Also runs before parsing, as well as in `resolve_streams` | FR-007 wants it early, and it is cheap. The mapping is only known once the form is read, so it cannot precede the body |
| D17 purge | Covers `previewed` only, which is what the partial index holds. `rejected` rows are left for 026 to decide | 025 writes only `previewed` |
| Notes row on `inferCadence` | 024 returns no cadence for exactly ten rows of `0, 3601, 7199, 10800, …`, because 8 of 9 gaps agree. D21's tests use twenty rows, and there rows 2 and 3 overlap | Found running T031. D21 itself still holds |

### A defect the suite caught late

`delete_expired` first used `DELETE ... WHERE id IN (SELECT ... LIMIT n FOR UPDATE SKIP LOCKED)`. Postgres may run that subquery more than once, and `test_purge_stops_at_its_limit` then removed 3 rows against a limit of 2, in 2 of 8 repeated runs. Rows are now chosen in one statement and deleted in the next. After the fix: 0 of 20 runs failed.

### Choices the task left open

- **Echoed cells.** 024's `value_too_large`, and its other cell-echoing messages, can hold a 128 KiB cell. Rule 008 and the plan allow echoing a user's own cell in their own preview, and those messages never reach logs. So the text is kept, and `bound_text` cuts the middle of any message over 500 characters when it is stored and returned: the row prefix, the start of the cell, an ellipsis, and the correction at the end. The same bound covers question text and the ignored-columns assumption, which can also grow with the file.
- **Blocking.** Instantaneous rows stay `pending` with kind `average_power`, so the preview blocks on the open question and pending count and never looks at kind for this. A stream whose rows are all invalid still raises its questions, with no period, so it raises no `other_source`. An out-of-range duration keyed to an absent stream opens the question and is stored as given.

### For 026 (found here, not fixed here)

- **Label length.** D6 says `source_label` fits `char_length(label) <= 120`. `lower()` can lengthen text: 60 × `İ` becomes a 120-character stream key and a 132-character label, which the `sources` CHECK would refuse at commit. 025 creates no source, so nothing fails yet.
- **Counter assumptions on append.** `build_assumptions` sees accepted rows only, because reading a source's whole counter series would need a third read method. When a file appends to a stored counter, it still says "first reading" and cannot see a decrease against stored points. 006 derives the right deltas regardless.
- **Streams with no period.** `mapping.streams` includes a stream whose rows are all invalid, with `period_start` null. It has nothing to commit, so it should create no asset.
- **Purge and commit.** Both deletes recheck `status = 'previewed'`, so a preview that a commit just moved is kept. 026 still has to refuse an expired preview itself.

### Evidence behind the decisions (2026-11-07, read-only)

| Check | Result | Decision |
|---|---|---|
| A route raising `RequestInvalidError("Pesan khusus…")`, through `register_exception_handlers` | Wire message is the catalog default `Permintaan belum dapat diproses. Periksa isian Anda lalu coba lagi.` | D11 |
| Declaring `UploadFile = File(...)` in this `.venv` | `RuntimeError: Form data requires "python-multipart"` at route definition | D9 |
| `grep -c python-multipart uv.lock` | 0 | D9 |
| `fastapi/routing.py` (0.162.0) | `await request.form()` at L455, `solve_dependencies` at L511 | D8 |
| `starlette/requests.py` (1.10.0) | `max_part_size` defaults to 1 MiB, with no total limit | D8 |
| `tests/unit/core/test_migrations.py` | Asserts `len(ScriptDirectory.get_heads()) <= 1` | D15 |
| `grep -rn invalidat app/insights` | No matches | Plan, Handoff |
| Prototype `inferCadence` on 0, 3601, 7199, 10800, … seconds | Cadence 3600, and 3 of 10 neighbouring intervals overlap | D21 |
| `app/scope/service/validity.py` | Missing relation gives `UNCONFIRMED`, so a total is refused | Plan, Handoff |

### Merge with PR #29 (2026-11-07)

PR #29 merged `0007_create_insight_feedback.py` first, so D15 applied: this migration became `0008_create_imports.py` with `down_revision = "0007"`, and the downgrade test now targets `0007`. Earlier Notes that say `0007` or `0006 (head)` record what was true when they were written. A local database that ran the old `0007` must drop `imports` and `import_rows` and set `alembic_version` back to `0006` before migrating. After merging `origin/main` (`fd50a7a`): API `make check` 896 passed, 2 skipped, coverage 99.01%; mobile `make check` 102 tests; `COMPOSITION=core-only` 656 passed; one head, `0008`; a downgrade to `0007` removes `imports` and keeps `insight_feedback`; `make openapi` and `make generate-api` show no drift.

## Open questions

Each needs a decision outside this spec. The tasks implement the safe default, so none blocks 025.

1. **Clock of the `empty` workspace.** Real CSV dated after 2026-10-26 commits but never shows on a demo-kind site (D20). Should the `empty` scenario follow the wall clock, advance to the imported range, or stay fixed? Owner and P1, since 008 owns it.
2. **Jitter tolerance.** PRD §10.2 infers cadence within ±1 second, but the same jitter makes `[t, t + cadence)` overlap, and 025 blocks overlap (D21). Keep blocking, or end each inferred interval at the next timestamp? Owner.
3. **Custom error messages.** `handle_app_error` drops every custom `AppError.message` today, so `_BINDING_NOT_STARTED`, `_CURSOR_INVALID`, `_PERIOD_REQUIRED` and the capability name never reach clients, and the catalog row for `APP-CAPABILITY-DISABLED` is wrong. This is out of scope here, and 025 does not depend on it. P1.

# Tasks: Import commit

**Input**: `specs/026-import-commit/spec.md`, `plan.md`, generated against `origin/main` at `5ec2fba`
**Branch**: `m5/import-commit`, cut from `5ec2fba`. `check-prerequisites.sh` refuses this name, so run it as `SPECIFY_FEATURE=026-import-commit .specify/scripts/bash/check-prerequisites.sh --json`.
**Lane**: P2, roadmap round 3, internal MVP. P1 reviews the commit contract, the replay evidence and every change listed in D24.
**Prerequisites**: 021, 024 and 025 are merged in `5ec2fba`. The Alembic head is `0008`.
**Tests**: Required and first (constitution principle 2, roadmap step 4). Each phase writes its tests, then a checkpoint task runs them and records the failure, and only then writes the code. Tests follow rule 003. Failure paths assert message, code, response, `request_id`, the record, recovery and fake secrets (rule 008).

**Paths** start at `applications/generic/hematdaya/`. Commands run from `applications/hematdaya-api/`. `domain.js` means `docs/reference/prototype/hematdaya-domain.js` and `domain.test.js` means `docs/reference/prototype/domain.test.js`. Line numbers refer to those files at `5ec2fba`. The API shape and the handoff to 027 are in [plan.md](plan.md).

## Decisions resolved against the code

| ID | Decision | Why |
|---|---|---|
| D1 | No insight invalidation operation. A commit writes readings and advances `measurement_revision` in one transaction, and the next insight read does the rest. The commit calls nothing in `app/insights`. | `grep -rn invalidat app/insights` has no match. All three read paths (`site_insights`, `hidden_insights`, `get` without `revision`) call `InsightService.evaluate`, which takes the site lock, recomputes and publishes through `_publish`: a changed `evidence_hash` supersedes the old revision and adds a new one, and an observation that no longer qualifies is retired with its evidence kept. No stored observation is returned without that step, and the commit holds the site lock until it ends, so no read can see half a commit. A stored "invalid" flag would be read by nothing. |
| D2 | Imported sources keep `resolution_mwh = None`. So a period served only by imported data gives a `descriptive` comparison and never publishes an automatic observation. A late import changes `learning_count`, `comparable_count`, notices and the comparison. The revision path is proved separately on a stored import source with a known resolution. | `compare` returns `DESCRIPTIVE` when any resolution is `None`, and `direction` then returns `None`. PRD §12 and AT-20 require this, and `domain.js` L838 sets `resolutionMWh: null` too. A CSV cannot add rows beside a source of known resolution while that source's binding covers the file's period: it raises `other_source` and blocks (025's D6). Reporting a revision test alone would hide this. |
| D3 | Lock order is site row, then import row, then writes. `get_import(import_id)` reads `site_id` with no lock. `sites.lock_owned(site_id, principal)` takes the site lock, and a foreign site gives `NOT_FOUND` with no lock taken. Then `get_import_locked(import_id)` takes `FOR UPDATE` with `populate_existing=True`. `ingest` re-takes the site lock inside the same transaction, which is a no-op. | `architecture.md`: import commits acquire the site lock before the import row. Every other site-lock holder (`AssetService`, `IngestService`, `InsightService.evaluate`, `DemoService.reset`, `end`, `_purge`, `SiteRepository.delete`) takes no import row first. Measured (Notes): without `populate_existing`, a `FOR UPDATE` re-read still returns `previewed` from the session's identity map after another transaction committed, so a second concurrent commit would write everything again. `SqlAlchemySiteRepository.lock` refreshes for the same reason. |
| D4 | Fix 025's preview order: `add_import` runs before `delete_expired` and `keep_newest_uncommitted`, and `keep_newest_uncommitted` takes `excluding=model.id`. | Reproduced (Notes): today's order deadlocks with a commit. The preview deletes the commit's import row, then its `INSERT` waits on the site row, because a foreign key check takes `FOR KEY SHARE`, which conflicts with the site lock's `FOR UPDATE`. The commit holds the site row and waits on the import row. With the insert first, the preview holds nothing the commit wants while it waits, and the same replay finishes cleanly. `excluding` stops the preview purging its own new row when `created_at` ties or inverts. |
| D5 | `Idempotency-Key` is required, with the feedback route's pattern `^[A-Za-z0-9_-]{22,128}$`. A key is stored on `imports.idempotency_key` by the same `UPDATE` that sets `committed`, so a refused or failed attempt stores nothing and the key stays free. Under the locks, the decision follows the Idempotency cases table below. Ownership comes before any replay. | Same shape as `FeedbackService.apply` and `DemoService.create`: ownership first, the stored result replayed, a changed payload refused with a typed 409. No claim row is needed, because the site lock already serializes every commit on a site, and `ux_imports_site_idempotency` from `0008` backs it up. `architecture.md` fixes the key as unique per site, so keys in different sites never collide and a foreign site's key can never leak. |
| D6 | Revalidate under the lock by equality of `measurement_revision`, `binding_revision` and `mapping["timezone"] == site.timezone`. Rows are not classified again. The check is site-wide, so any data change on the site makes every open preview stale, including one over unrelated rows. | Every write that could change a classification advances a revision: `ingest`, `create_asset`, archive, `bind_source`, `unlink_source` and demo reset. So equal revisions mean the stored data is what the preview read. The seeded plan's "and the overlap classifications" therefore adds a second read of up to 150,000 rows and proves nothing further. `PATCH /sites/{id}` can change `timezone` and advances neither revision, and naive rows were read in the old zone, so it needs its own check. |
| D7 | New code `APP-IMPORT-STALE`, public `IMPORT_STALE`, 409, not retryable, for an expired preview or a failed D6 check. `details[0].type` is `expired`, `revision_changed` or `timezone_changed`. `imports.status` stays `previewed`. 026 never writes `rejected`. | The handoff asks for its own decision. `IMPORT_BLOCKED` tells the user to fix a reason in the preview, which is wrong here: the preview is gone or out of date and only a new one helps. A refusal raises, the route rolls back, so writing `rejected` would need a second transaction for something no client reads. The spec also says a failed commit leaves the preview usable. |
| D8 | New code `APP-IMPORT-ACK-REQUIRED`, public `IMPORT_ACK_REQUIRED`, 409, not retryable, when `needs_acknowledgment` is true and `acknowledge_skipped` is false. | 027's US2 scenario 2 links this failure to the checkbox, so clients need a code to branch on. A `BAD_REQUEST` would carry the generic message. |
| D9 | Migration `migrations/versions/0009_add_import_commit_result.py`, `revision = "0009"`, `down_revision = "0008"`, adding `commit_result jsonb` and two `NOT VALID` CHECKs (Data Model in plan.md). Nothing else from `0008` changes. | `alembic heads` at `5ec2fba` says `0008`, and none of the 24 branches on `origin` holds a `0009` or later. 028's plan already names `0010`. Checked in `0008`: `idempotency_key` and its unique index exist, `status` allows `committed`, `import_rows (import_id, data_row)` serves the row pages, and `ix_imports_expiry` covers only `previewed`, so a committed import leaves it. `NOT VALID` because `make_import(status="committed")` and `_import(status=COMMITTED)` leave committed rows with no result in the shared development database, so a plain constraint would stop `make migrate` there, and also a downgrade and upgrade. Merged migrations are never edited. |
| D10 | One `ingest` per 5,000 rows for interval kinds, and one `ingest` per stream for counters. Rows are read in pages of 5,000 by `data_row` and buffered per stream. Never one call per row. | Measured (Notes) on 150,000 rows: one call per 5,000 took 9.43 s, stalled the event loop at most 0.08 s and peaked at 36.1 MiB. One call for the whole file took 11.34 s, stalled 2.03 s and peaked at 788.2 MiB. A counter needs one call, because `_rederive_counter` rereads and replaces all of a source's deltas per call: 21.23 s, 2.00 s stall, 945.1 MiB. Each `ingest` advances `measurement_revision`, so a commit may advance it several times in one transaction. That is safe, because revisions are only compared for equality. |
| D11 | Only a stream with at least one accepted row creates anything. A stream with `period_start` null is dropped when `mapping` is read and never appears in the result. A duplicate-only commit creates no asset, source, binding or relation, and advances no revision. | 025's defect: `mapping.streams` includes streams whose rows are all invalid. FR-004 and the spec's duplicate-only rule forbid domain changes. |
| D12 | New assets use `AssetService.add_asset` with `ScopeKind.DEVICE` and `asset_name` as written. New sources use `AssetService.create_source` with `label` from `mapping`, `origin = import`, `transport_status = historical`, the stream's `measurement_kind` and `cadence_seconds`, and no `resolution_mwh`. Neither method writes its own audit event, so the commit writes exactly one (D21). | `domain.js` L831. 025's handoff. A historical source is never treated as a disconnected live meter: `notices` flags staleness only for `simulated_live`. |
| D13 | Bindings come from pure `uncovered_ranges(start, end, bindings)`, walking all of the asset's bindings over the accepted rows' span. Each uncovered range becomes one authoritative binding. A range ends at the next binding's `effective_from`, or stays open when none follows. A counter's `end` is its last point plus one microsecond. | `resolve_authority` counts a reading only inside a binding, so `effective_from` must not start after the earliest row, including a reimport with earlier rows. `bindings_one_authority` refuses two overlapping authoritative ranges, so an open range must end at any later binding's start. All bindings are walked, not only authoritative ones: an open authoritative range would otherwise silently overrule a later candidate. The span uses accepted rows only, so a duplicate row cannot re-attribute a range the user ended. |
| D14 | When `rows_added > 0`, `scope` writes one relation per pair of the file's assets: `disjoint` writes `RelationKind.DISJOINT` and `unknown_overlap` writes `RelationKind.UNKNOWN_OVERLAP`. The pairs come from `scope_issues(asset_ids, snapshot.containment, snapshot.relations, set())`, keeping those of type `UNCONFIRMED`, so an existing relation or containment is never contradicted. A pair of a file asset and an asset outside the file gets no relation. See Open questions, item 2. | `scope_issues` refuses any pair without a `disjoint` relation, so copying `domain.js` L842 would refuse every total. The question reads "beban perangkat dalam berkas ini", and it says nothing about other assets. Writing `disjoint` against a `site_total` meter outside the file would double count, which the constitution forbids. Unknown is never zero, and it is never disjoint. |
| D15 | A preview with more than `MAX_IMPORT_STREAMS = 100` streams holding staged rows is blocked, with its own reason. See Open questions, item 3. | Nothing bounds this today. A 150,000-row file could name 150,000 assets, and D14 would write about 10^10 relations. `relate` costs three round trips per pair, so 100 streams means 4,950 pairs and about 15,000 round trips under the site lock. `scope_issues` is quadratic on every read. PRD §18's working scale is 20 sources. Rule 006: bounded work. It belongs in the preview, so the user learns before confirming. |
| D16 | `source_label` keeps today's text whenever it fits 120 characters. Above that it becomes the first 103 characters, `·`, and the first 16 hex characters of the key's SHA-256. | 025's defect: 60 × `İ` lower-cases to a 120-character key and a 132-character label, which the `sources` CHECK refuses. Measured with Python, and `char_length` counts the same code points. Refusing a valid 60-character name would be wrong. No stored label can be over 120, so reimports of every existing source keep matching. The hash keeps two long keys distinct. |
| D17 | Leave the counter assumption text as it is. It still says "first reading" on an append and cannot see a decrease against stored points. T042 proves the totals and the reset interval stay correct, and Notes records the limit for 027's copy review. | 006 derives the right deltas whatever the assumption says, so no number is wrong. A fix needs a third read method on P1's `IngestService`, and it would change preview text that 026 does not own. It does not block commit. |
| D18 | Do not change spec 008. On an `empty` demo workspace, rows ending after `virtual_now` (2026-10-26 00.00 WIB) commit, are stored and appear in no read. The preview's D20 assumption still warns, and the result adds `rows_after_site_clock`, so the number is plain. T045 pins this. See Open questions, item 1. | Merged PR #28 sends "Mulai" and "Lewati" to `useDemoSession.start('empty')`, a demo site with that fixed clock, and every energy read has `interval_end <= :now`. Today is already past it. 008 is not this spec's to change, and the owner has not decided. Without the field, a commit whose rows appear nowhere would be the misleading success constitution prohibition 6 forbids. |
| D19 | `POST /imports/{id}/commit` answers 200 with `ImportCommitResponse`, the first result plus `replayed`. `GET /imports/{id}` gains `result`, null until committed. While a commit is in flight, `GET` answers immediately with the last confirmed state, `previewed`. | Spec US2 scenario 2 and FR-003. `GET` takes no lock, and READ COMMITTED hides the open transaction, so there is no separate `committing` status to keep honest. 200 on both, because the import already exists and feedback answers the same way. |
| D20 | `provenance` holds `import_id`, `file_name`, `timezone`, `timezone_confirmed` and the stream's `interval_basis`. `received_at` is one `wall_now()` per commit. | PRD §10.1 asks for the original timezone assumption. Architecture's two clocks: `received_at` uses the wall clock. |
| D21 | One audit event `import.committed`, `subject_type = import`, with `affected_from` and `affected_to` from the merged `IngestResult`s and `detail` of counts only. Duplicate-only writes it with both dates null. A replay writes none. | FR-004 and FR-19. Counts and an ID carry no secret, and the key is never written there. |
| D22 | `IngestResult` must agree with the preview: `rejected` empty, `revised` and `repeated` zero, and `added` summing to `accepted_rows`. Anything else raises `AppError(error=RuntimeError(...))`, giving `APP-UNKNOWN` and a full rollback. | Equal revisions make this unreachable, unless 024, 025 and 006 disagree, which is a bug. `ingest` would otherwise turn a changed value into a revision (025's D5), which is the very thing 025 exists to prevent. |
| D23 | New failures use the catalog message and `details`. Custom `message=` is never passed. | `handle_app_error` drops custom messages. That is P1's item (025's Open questions, item 3): 026 neither depends on it nor fixes it. `details` is already covered by the EH-07 deviation, and it holds fixed text and counts only. |
| D24 | Changes in P1's modules, all flagged for review: `add_binding` gains `effective_to` (`app/assets/service/service.py`, `app/assets/repository/base_repository.py`, `app/assets/repository/sqlalchemy/repository.py`, tested in `tests/integration/test_assets.py`); a new `app/audit/dependencies.py::build_audit_service`; and the flip in `app/capabilities/service/service.py`, tested in `tests/unit/capabilities/test_capabilities.py`. Shared: `codes.py`, `public.py`, `docs/error-handling/catalog.md`, `tests/integration/test_isolation.py`, `tests/integration/conftest.py`. No change to `IngestService`, `SiteService`, `InsightService` or `app/energy`. | `AssetService.add_binding` cannot express a bounded range and the repository has no way to shift one, so D13 needs the parameter. Default `None` leaves every existing caller as it is. `tests/unit/imports/test_module_boundary.py` forbids `app/imports/` from importing `SqlAlchemyAuditRepository`, so wiring the audit service needs a builder, the same shape as `build_ingest_service`. |
| D25 | Flip `AdapterResponse(id="csv")` to `CapabilityStatus.AVAILABLE`. No mobile source changes, apart from the regenerated `schema.generated.ts`. `impor-data` stays `coming_soon`: 027 flips it. | The spec's **Flips**. Outside the generated schema, `grep -rn adapters src` finds only the structural check in `client.ts` and a test fixture literal in `client.test.ts`, which is sample data. `ServiceStatus` and the registry do not read this value. |
| D26 | No route calls `CapabilityGuard`. The commit tests join the core-only CI step. | Import is core (025's D13, 011's plan). |
| D27 | No background worker. SC-003 is met by a measured duration plus a recoverable status: if a client gives up, the server still finishes, `GET` shows the outcome, and a retry with the same key waits on the lock and replays. Gated benchmarks record the number. PRD §18 and 041 own the formal target. | Plan's Design. Measured locally: about 19 s for preview plus commit on interval rows, and about 30 s on counters, against 60 s. The mobile client's `TIMEOUT_MS` is 10 s, so a large commit will look lost to it (Notes, For 027). |
| D28 | Staged rows stay after a commit. `GET /imports/{id}/errors` still pages invalid rows, and nothing reads `parsed` again. Retention belongs to 038. | Deleting 150,000 rows would add write work inside the commit, for a saving no target asks for yet. |
| D29 | D4 and D15 go beyond the seeded plan, and they are kept. Nothing else is added: no `committing` status, no `rejected` write, no stale flag on `GET`. | Constitution principle 3 asks for the smallest justified diff. D4 fixes a deadlock this spec's commit would introduce, and D15 bounds work this spec's commit would make real. Neither can wait for a later spec. |

## Idempotency cases

Checked in this order, under both locks. `K` is the request's key and `A` its `acknowledge_skipped`.

| Case | Outcome |
|---|---|
| `K` is stored on another import of this site | 409 `CONFLICT` (`APP-IMPORT-KEY-CONFLICT`), even if this import is committed |
| This import is committed with `K`, and the stored `acknowledge_skipped` differs from `A` | 409 `CONFLICT` (`APP-IMPORT-KEY-CONFLICT`) |
| This import is committed, with `K` and the same `A`, or with an unused key | 200, first result, `replayed: true`, nothing written. `architecture.md`: a repeated commit returns the first result |
| Blocked | 409 `IMPORT_BLOCKED` |
| Expired, then D6 | 409 `IMPORT_STALE` |
| `needs_acknowledgment` and not `A` | 409 `IMPORT_ACK_REQUIRED` |
| Otherwise | 200, first result, `replayed: false` |

A key used only by a refused or failed attempt stays free, so the same request can succeed later.

## Messages

Text is exact.

### Errors

| Internal code | Public code | HTTP | Default message | Trigger | retryable |
|---|---|---|---|---|---|
| `APP-IMPORT-STALE` | `IMPORT_STALE` | 409 | `Pratinjau ini sudah tidak berlaku. Buat pratinjau baru lalu coba lagi.` | Commit of an expired preview, or D6 fails. `details` names which | false |
| `APP-IMPORT-ACK-REQUIRED` | `IMPORT_ACK_REQUIRED` | 409 | `Ada baris yang akan dilewati dan belum disetujui. Setujui baris yang dilewati lalu coba lagi.` | D8. `details` gives the count | false |
| `APP-IMPORT-KEY-CONFLICT` | `CONFLICT` | 409 | `Permintaan ini sudah dipakai untuk impor lain. Konfirmasi impornya lagi untuk mengirim permintaan baru.` | The Idempotency cases table; nothing is applied | false |

`APP-IMPORT-BLOCKED` is registered by 025 and first reaches a route here.

### Details

Each is `{"loc": [...], "msg": ..., "type": ...}`, holding no submitted value.

| `type` | `loc` | `msg` |
|---|---|---|
| `expired` | `["import"]` | `Pratinjau sudah melewati batas 24 jam.` |
| `revision_changed` | `["import"]` | `Data pada ruang kerja ini berubah setelah pratinjau dibuat.` |
| `timezone_changed` | `["import"]` | `Zona waktu ruang kerja berubah setelah pratinjau dibuat.` |
| `acknowledgment_required` | `["body", "acknowledge_skipped"]` | `{n} baris tidak valid akan dilewati.` |

### Block reason

It goes after the `conflict` reason in 025's Block reasons order, and before `Tidak ada baris valid yang dapat diimpor.`

| When | Text |
|---|---|
| More than 100 streams with staged rows | `Berkas ini memuat {n} perangkat, melebihi batas 100 perangkat per impor. Pisahkan berkasnya lalu coba lagi.` |

## Prototype assertions: what moves where

| Assertion | `domain.test.js` | Here | Elsewhere |
|---|---|---|---|
| A rejected commit leaves no reading or asset | L269–L271 | T021, with a real failure inside the transaction | |
| An interrupted commit is found by a status lookup, and a retry replays | L272–L275 | T028: `GET` gives the result, and a retry gives `replayed: true` with 10 readings | Periksa status on screen in 027 |
| Reimport adds nothing | L276–L277 | T041: a commit of that preview adds 0 | The counts in 025 |
| A conflict is blocked | L278–L280 | T029: the commit is refused | The counts in 025 |

`applyImport` in `domain.js` differs from the plan here on purpose: L838 labels a source by file name (025's D6 uses the stream), L839 binds from `-Infinity` (D13), L842 writes relations only for `unknown` (D14), and L850 renames the workspace (not ported).

---

## Phase 1: Setup

**Purpose**: Confirm the stack and the migration number.

- [X] T001 Run `make run-dependencies`, `make migrate`, `uv run alembic heads` and `uv run pytest tests/unit/imports -q` in `applications/hematdaya-api/`, and record the head and pass count in this file's Notes section. If the head is not `0008`, apply D9 with the next free number and re-point `down_revision`

## Phase 2: Foundational

**Purpose**: Errors, storage, the P1 additions and the pure rules every story uses.

### Tests first

- [X] T002 [P] Add three rows to `ERRORS` in `applications/hematdaya-api/tests/unit/imports/test_import_errors.py` for `ImportStaleError`, `ImportAckRequiredError` and `ImportKeyConflictError`, with the exact code, public code, status and message from the Errors table. The existing parametrized tests then cover the response, the one record, `recovery == {"retryable": False}`, fake secrets and the row in `docs/error-handling/catalog.md`
- [X] T003 [P] Add to `applications/hematdaya-api/tests/integration/test_import_storage.py`: `mark_committed` round trip sets `status`, `idempotency_key` and `commit_result`, and returns False for a row that is not `previewed`; a raw `UPDATE imports SET status = 'committed'` with no result, or a result with no key, raises `IntegrityError`; a `previewed` row stores SQL NULL in `commit_result`, not JSON null; `get_import_locked`, in a session that already loaded the row through `get_import`, returns the status another session committed meanwhile (D3); `find_by_key` returns the ID within its site and None for the same key in another site; `accepted_page` returns only `accepted` rows with `parsed`, in `data_row` order, after a given row, up to the limit; `keep_newest_uncommitted(site, 4, excluding=new_id)` keeps `new_id` even when it sorts oldest. Add `test_the_commit_migration_downgrades_and_upgrades`, through `subprocess` as `test_the_migration_downgrades_and_upgrades` does: with a `committed` row present, `alembic downgrade 0008` removes `commit_result`, and `alembic upgrade head` succeeds and restores it (D9)
- [X] T004 [P] Add to `applications/hematdaya-api/tests/integration/test_assets.py`: `AssetService.add_binding` with `effective_to` stores the bounded range; an authoritative binding starting exactly at that end is accepted; one overlapping it raises `BindingOverlapError`; omitting `effective_to` leaves it open
- [X] T005 [P] Write `applications/hematdaya-api/tests/unit/imports/test_commit_plan.py` for `app/imports/service/commit_plan.py`. `committable_streams(mapping)`: a stream with `period_start` null is dropped, and the fields of the rest are typed (D11). `reading_from_parsed(parsed)`: with `raw_value "10,5"` and `value "10.500"`, `normalize` gives `identity_key == parsed["identity_key"]` and `raw_value == "10.500"`; a counter row has only `measured_at`; instants are UTC-aware. `row_bounds(parsed)`: an interval returns its bounds, a point returns itself and itself plus one microsecond. `uncovered_ranges`, parametrized: no bindings gives `(start, None)`; an open binding covering the span gives `[]`; earlier rows before an open binding give `(start, binding_start)`; a later binding of any source ends the range at its start; rows after a closed binding give `(start, None)`; a straddle gives `(closed_end, None)`; a hole between two bindings gives just that hole; a span fully inside a closed binding gives `[]`; a counter point exactly at a binding's `effective_to` is uncovered. `stale_reason(model, site, now)`: None when all match; `expired` at `expires_at <= now`, ahead of the others; `revision_changed` for either revision; `timezone_changed`. `affected_period(start, end, timezone)`: None for None; an exclusive end ending at local midnight belongs to the previous date; `start == end` gives that one date. `CommitTotals.add(result)` sums `added`, takes min and max of the affected range, ignores `None`, and raises `AppError` for any `rejected`, `revised` or `repeated` (D22)
- [X] T006 [P] Add to `applications/hematdaya-api/tests/unit/imports/test_mapping.py`: `source_label` returns `Impor CSV · {key}` unchanged at a key of 108 characters; 60 × `İ`, lower-cased, gives a label of at most 120 characters, the same on every call; two 120-character keys sharing their first 103 label characters give different labels; `resolve_source` still matches a stored source by the long label
- [X] T007 [P] Add to `applications/hematdaya-api/tests/unit/imports/test_classify.py`: `summarize(counts, open_questions=0, streams=101)` is blocked with the exact Block reason text, and `streams=100` is not; the reason sits after the conflict reason and before `Tidak ada baris valid yang dapat diimpor.`; omitting `streams` changes nothing. Add `test_streams_over_the_limit_are_blocked` to `applications/hematdaya-api/tests/integration/test_import_preview.py`: 101 names in one file, with `scope` answered, give 201 and `blocked`, and 100 names give not blocked
- [X] T008 [P] Add to `applications/hematdaya-api/tests/unit/imports/test_contract.py`: `POST /api/v1/imports/{import_id}/commit` has a required `Idempotency-Key` header with D5's pattern, a request body of `ImportCommitRequest` with `acknowledge_skipped`, a 200 response of `ImportCommitResponse` carrying `replayed`, and the `ErrorEnvelope` default; `ImportPreviewResponse` has a nullable `result`
- [X] T009 Run T002–T008 and confirm each fails on missing behavior. Record the result in Notes for `applications/hematdaya-api/tests/`

### Code

- [X] T010 Add `APP_IMPORT_STALE`, `APP_IMPORT_ACK_REQUIRED` and `APP_IMPORT_KEY_CONFLICT` to `applications/hematdaya-api/app/core/errors/codes.py` and their rows to `PUBLIC_ERROR_BY_CODE` in `app/core/errors/public.py`, exactly as in the Errors table. Add `ImportStaleError`, `ImportAckRequiredError` and `ImportKeyConflictError` to `app/imports/service/errors.py`. Add three rows to `docs/error-handling/catalog.md`. T002 passes
- [X] T011 Write `applications/hematdaya-api/migrations/versions/0009_add_import_commit_result.py` with plan.md's Data Model SQL, `revision = "0009"`, `down_revision = "0008"` and a working `downgrade`, using the `_execute` helper from `0008_create_imports.py`, so no `;` inside any SQL string. Keep `NOT VALID` on both CHECKs (D9). Confirm `uv run alembic upgrade head` succeeds on a database that ran 025's tests, `uv run alembic heads` shows one head and `uv run pytest tests/unit/core/test_migrations.py` passes
- [X] T012 Add `commit_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))` to `ImportRecord` in `applications/hematdaya-api/app/imports/repository/sqlalchemy/models.py`. `none_as_null` matters, because JSON null would pass the CHECK as a result. Add `commit_result: dict[str, Any] | None = None` to `ImportModel` in `app/imports/model/models.py`, and read it in `_import_model`. In `app/imports/model/schema.py`, add `ImportCommitRequest`, `ImportCommitAssetResponse`, `ImportCommitResultResponse` and `ImportCommitResponse` with plan.md's fields, and `result: ImportCommitResultResponse | None = None` on `ImportPreviewResponse`. Give the fields US3 fills defaults (`[]`, `None` or `0`), so T025's first result validates. `ImportCommitResponse` adds `replayed` to the result
- [X] T013 Update the test helpers the new CHECKs break: `make_import` in `applications/hematdaya-api/tests/integration/conftest.py`, and `_import` in `tests/integration/test_import_storage.py`. For `status="committed"`, set `idempotency_key` and a valid `commit_result` from one `COMMITTED_RESULT` constant in `conftest.py`. Run `uv run pytest tests/integration/test_import_preview.py tests/integration/test_import_storage.py -q`, and confirm the only failures are the new tests from T003 and T007
- [X] T014 Add `get_import_locked`, `find_by_key`, `accepted_page` and `mark_committed` to `ImportRepository` in `applications/hematdaya-api/app/imports/repository/base_repository.py` and `SqlAlchemyImportRepository` in `app/imports/repository/sqlalchemy/repository.py`, and add `excluding: UUID | None = None` to `keep_newest_uncommitted`. `get_import_locked` uses `.with_for_update().execution_options(populate_existing=True)`. `accepted_page` filters on `status = 'accepted'` and `data_row > :after`, ordered by `data_row`. `mark_committed` is `UPDATE ... WHERE id = :id AND status = 'previewed'`, returning whether one row changed. T003 passes
- [X] T015 In P1's module (D24), add `effective_to: datetime | None = None` to `AssetService.add_binding` in `applications/hematdaya-api/app/assets/service/service.py`, to `AssetRepository.add_binding` in `app/assets/repository/base_repository.py` and to `SqlAlchemyAssetRepository.add_binding` in `app/assets/repository/sqlalchemy/repository.py`, passing it to `BindingRecord`. Touch nothing else. T004 passes
- [X] T016 [P] In P1's module (D24), write `applications/hematdaya-api/app/audit/dependencies.py` with `build_audit_service(session: AsyncSession) -> AuditService`, the same shape as `build_ingest_service` in `app/measurements/dependencies.py`
- [X] T017 [P] Apply D16 to `source_label` in `applications/hematdaya-api/app/imports/service/mapping.py`, with a docstring saying why the format of short keys must not change. T006 passes
- [X] T018 Add `MAX_IMPORT_STREAMS = 100` and a `streams: int = 0` parameter to `summarize` in `applications/hematdaya-api/app/imports/service/classify.py`, emitting the Block reason in its place. In `app/imports/service/preview.py`, pass the count of `staged_file.streams` with `period_start` not None. T007 passes
- [X] T019 Write `applications/hematdaya-api/app/imports/service/commit_plan.py` with `CommitStream`, `committable_streams`, `reading_from_parsed`, `row_bounds`, `uncovered_ranges`, `stale_reason`, `affected_period` and `CommitTotals`, pure, with no SQL and no HTTP. `reading_from_parsed` reads `value` and never `raw_value`. T005 passes

## Phase 3: User Story 1 - All or nothing (Priority: P1) MVP

**Goal**: One commit writes all accepted rows, assets, sources, bindings and relations together, or nothing at all.

**Independent Test**: `uv run pytest tests/integration/test_import_commit.py -k atomic`. Fail mid-commit, and every table and both revisions match the moment before.

### Tests first

- [X] T020 [US1] Write `applications/hematdaya-api/tests/integration/test_import_commit.py`, `pytestmark = pytest.mark.integration`, with these helpers: `capture_app_logs`, `owner`, `_records`, `_assert_failure` and `TABLES` in the same form as `test_import_preview.py`; `_key()` as `secrets.token_urlsafe(16)`; `_preview(client, site, headers, text, mapping) -> dict`; `_commit(client, import_id, headers, *, key=None, acknowledge=False) -> Response`. Add atomic tests over `TWO_ASSETS_CSV`, explicit intervals on 2026-10-20 with Router 10 and 12 Wh and Kulkas 50 and 50 Wh, `scope=disjoint`. Commit gives 200 and `rows_added == 4`. Two assets with `scope_kind = device`. Two sources with `origin = import`, `transport_status = historical`, `resolution_mwh` null, `cadence_seconds` null (explicit intervals infer no cadence) and the `source_label` label. Two open authoritative bindings from the earliest row. A timestamp-only file with offsets stores `cadence_seconds = 3600`. One `disjoint` relation. `measurements.raw_value` is canonical (`10.000`) and `provenance` holds D20's keys. `GET /api/v1/sites/{site}/summary?start_date=2026-10-20&end_date=2026-10-20` gives `energy_kwh == "0.122"`, `scope.valid` true and `origins == ["import"]`. Both revisions advanced. Also: `unknown_overlap` writes `unknown_overlap` and the summary refuses the total with `scope_conflict` while per-asset values stay; one asset writes no relation and gives a valid total; a stream whose rows are all invalid, with `acknowledge`, creates no asset, source or binding (D11); a 60 × `İ` name commits with a label of at most 120 characters, and a reimport of it gives duplicates (D16)
- [X] T021 [US1] Add atomic failure tests to `applications/hematdaya-api/tests/integration/test_import_commit.py`. Parametrize the injected failure with `monkeypatch`: `IngestService.ingest` raising on the second stream, `AuditService.record` raising, and `IngestService.ingest` returning `revised=1` (D22). Each gives 500 `INTERNAL_ERROR`, asserted through `_assert_failure` with internal code `APP-UNKNOWN`, and fake `Bearer RAHASIA-PALSU-123` in an asset name and the key's value appear in no response or record. Every `TABLES` count and both revisions match the moment before, `imports.status` is `previewed`, `idempotency_key` is null, and `GET` still answers. Then, with the patch removed, a retry with the same key answers 200 with `replayed: false`, and the rows are there once
- [X] T022 [US1] Add atomic binding tests to `applications/hematdaya-api/tests/integration/test_import_commit.py`, each with a summary oracle proving the rows count. Earlier rows: file A on 2026-10-20, then file B on 2026-10-19 for the same asset gives a second binding `[B's first row, A's first row)`, and the summary of 2026-10-19 holds B's energy. Later binding: an asset with another source bound from 2026-10-25 (`make_source`, `make_binding`), and a file on 2026-10-20 mapped to it by ID gives `[first row, 2026-10-25)`, leaving the later binding unchanged. Closed binding: run `UPDATE bindings SET effective_to` first, then preview and commit rows beyond it, which opens a new binding from the first of them. Append inside an open binding: no new binding, and `binding_revision` does not move. Counter: earlier points before a stored stream give `[first point, stored first point)`
- [X] T023 [US1] Add atomic scope tests to `applications/hematdaya-api/tests/integration/test_import_commit.py`. A file mapping one existing and one new asset writes one relation between them. An existing `disjoint` or `unknown_overlap` pair, or a parent and child pair, is left unchanged, whatever `scope` says. A second file adding a new asset beside assets outside it writes no relation to them, and the summary refuses the total with `scope_conflict`, type `unconfirmed`, while per-asset values stay (D14, pinning the default)
- [X] T024 [US1] Run T020–T023 and confirm each fails on missing behavior, a 404 or 405 from the missing route. Record the result in Notes for `applications/hematdaya-api/tests/`

### Code

- [X] T025 [US1] Write `ImportCommitService` in `applications/hematdaya-api/app/imports/service/commit.py`, with constructor `(repository: ImportRepository, sites: SiteService, assets: AssetService, ingest: IngestService, audit: AuditService)` and `async commit(import_id, principal, key, acknowledge_skipped) -> CommitOutcome`, a frozen dataclass of `result: dict[str, Any]` and `replayed: bool`. Lock per D3. Then `assets.snapshot(site)`, and `committable_streams(model.mapping)` keyed by `stream_key`. Page with `accepted_page(model.id, after, 5000)`. On a stream's first row, resolve its target per D12: use `asset_id` or create the asset, use `source_id` from the snapshot or create the source. Append `reading_from_parsed` to that stream's buffer and track its span with `row_bounds`. Flush interval kinds at 5,000 and counters at the end (D10), through `ingest.ingest(site, source, readings, received_at=received_at, provenance=provenance)`, and add each result to `CommitTotals`. Then add bindings per D13 with `authoritative=True`, write relations per D14 through `assets.relate`, and call `sites.advance_binding_revision(site)` once when anything was created. Raise per D22 when `added != accepted_rows` or a row's stream is not in `mapping`. Write D21's event through `AuditService.record` with its action, subject, actor and affected range, leaving `detail` to T048. Build `result` with `import_id`, `status`, `rows_added`, `rows_skipped`, `rows_duplicate`, `acknowledge_skipped` and `committed_at`, and call `mark_committed`, raising per D22 on False. Google-style docstrings stating the lock order
- [X] T026 [US1] Add `get_import_commit_service` and `ImportCommitServiceDep` to `applications/hematdaya-api/app/imports/dependencies.py`, using `build_ingest_service(session)` and `build_audit_service(session)`. Add `POST /imports/{import_id}/commit` to `app/imports/router.py` with `summary`, `request: ImportCommitRequest` and `idempotency_key: Annotated[str, Header(alias="Idempotency-Key", pattern=r"^[A-Za-z0-9_-]{22,128}$")]`, returning `ImportCommitResponse`. T008 and T020–T023 pass
- [X] T027 [US1] Run `uv run pytest tests/unit/imports tests/integration/test_import_commit.py -q` and `make lint`, and fix what they find in `applications/hematdaya-api/app/imports/`

## Phase 4: User Story 2 - Retry is safe (Priority: P1) MVP

**Goal**: A repeat returns the first result, a lost response can be found again, and a refused preview changes nothing, including under real concurrency.

**Independent Test**: `uv run pytest tests/integration/test_import_commit.py -k "replay or refused or key or race"`.

### Tests first

- [X] T028 [US2] Add replay tests to `applications/hematdaya-api/tests/integration/test_import_commit.py`. AT-34 over `csv10`: commit, then repeat with the same key gives 200, `replayed: true` and the same result apart from that flag; `measurements` stays at 10, `audit_events` stays at 1, and revisions do not move. A lost response: ignoring the first answer, `GET /api/v1/imports/{id}` gives `status == "committed"` and a `result` equal to it, and a repeat gives `replayed: true`. A repeat with a new, unused key also replays. A replay after `expires_at` has passed still replays, and `GET` still says `committed`
- [X] T029 [US2] Add refused tests to `applications/hematdaya-api/tests/integration/test_import_commit.py`, each through `_assert_failure` with fake secrets, asserting every `TABLES` count and both revisions are unchanged, status is still `previewed`, and the key is free afterwards. Blocked (conflict and open question) gives `IMPORT_BLOCKED`. Expired (`UPDATE imports SET expires_at`) gives `IMPORT_STALE`, `details[0].type == "expired"`. Revision moved by `POST /api/v1/sites/{site}/assets`, or by a reading through `build_ingest_service`, gives `revision_changed`. `PATCH /api/v1/sites/{site}` changing `timezone` gives `timezone_changed`. `POST /api/v1/demo/sessions/current/reset` on an `empty` session gives `revision_changed`. 2 of 10 invalid (`csv10(2)`) without acknowledgment gives `IMPORT_ACK_REQUIRED`, `details[0].msg == "2 baris tidak valid akan dilewati."`, and with it gives 200, `rows_added == 8` and `rows_skipped == 2`. An expired preview purged by a new preview gives `NOT_FOUND`
- [X] T030 [US2] Add key tests to `applications/hematdaya-api/tests/integration/test_import_commit.py`, following the Idempotency cases table. A key used on import A, then sent for import B, gives 409 `CONFLICT` through `_assert_failure` with internal code `APP-IMPORT-KEY-CONFLICT`, and B is unchanged. The same key with a different `acknowledge_skipped` on the committed import gives the same 409. The same key in another site with its own preview succeeds. Parametrize a missing key and `{"Idempotency-Key": "short"}`: 422 `VALIDATION_FAILED`, nothing stored. A key refused by `IMPORT_STALE` commits a fresh preview afterwards
- [X] T031 [US2] Add race tests for one import to `applications/hematdaya-api/tests/integration/test_import_commit.py`, with helpers `_hold_site_lock(site)`, a session holding `SELECT id FROM sites WHERE id = :id FOR UPDATE` until released, and `_wait_blocked(count)`, polling `pg_stat_activity` for `wait_event_type = 'Lock'` up to 5 seconds. SC-001: under the held lock, start two commits with one key, see two blocked, release, and `asyncio.wait_for(gather, 30)`. Both answer 200, exactly one with `replayed: false`, results equal apart from that flag, 10 readings, one audit event. Repeat with two different keys: same outcome, and the stored key is the winner's. Also: under the held lock with a commit pending, `GET /api/v1/imports/{id}` answers `previewed` within 2 seconds, without blocking (D19)
- [X] T032 [US2] Add race tests for distinct previews to `applications/hematdaya-api/tests/integration/test_import_commit.py`, with the same helpers. SC-002, same source interval: two previews of `csv10` on an empty site, committed concurrently. One 200, one 409 `IMPORT_STALE` with `revision_changed`; `measurements`, `assets`, `sources`, `bindings` and `audit_events` hold one result; the loser is `previewed`, and a new preview of it is all duplicates. SC-002, same binding: two previews of different days mapped to one existing asset with no source. One wins and one is stale, with one binding. A preview over unrelated rows on the same site is also stale (D6, pinning the site-wide check)
- [X] T033 [US2] Add `test_race_commit_and_preview_purge_finish_together` to `applications/hematdaya-api/tests/integration/test_import_commit.py`, the deadlock of D4. Five previews on one site; take the oldest as X. Under the held lock, start the commit of X, wait for one blocked, start a sixth preview, wait for two blocked, release, and `asyncio.wait_for(gather, 30)`. Commit 200, preview 201, X is `committed` and present, and no response is 500
- [X] T034 [US2] In `applications/hematdaya-api/tests/integration/test_isolation.py`, add `("POST", "/api/v1/imports/{import}/commit", {"acknowledge_skipped": False})` to `FOREIGN_ROUTES`, and send a valid `Idempotency-Key` on every request of `test_foreign_resources_look_missing`, so the route reaches ownership. Assert the foreign import's `status` is unchanged. The header check runs first and answers the same for any import, so it leaks nothing
- [X] T035 [US2] Run T028–T034 and confirm T028–T033 fail on missing behavior. T033 must fail on today's preview order, with a deadlock answered as a 500. T034 passes already, because T025 uses `lock_owned`: to prove it can fail, temporarily call `sites.lock` in `applications/hematdaya-api/app/imports/service/commit.py`, see it fail, and restore it. Record both in Notes for `applications/hematdaya-api/tests/`

### Code

- [X] T036 [US2] Add the gate to `ImportCommitService.commit` in `applications/hematdaya-api/app/imports/service/commit.py`, after the locks and before any write, in the Idempotency cases order: `find_by_key`, replay of `commit_result` with `replayed=True`, `ImportPreviewService.require_committable`, `stale_reason` with `wall_now()`, then acknowledgment. Raise with Details text per D7 and D8. T029 and T030 pass, and T028 except its `GET` assertions
- [X] T037 [US2] Apply D4 in `ImportPreviewService.preview` in `applications/hematdaya-api/app/imports/service/preview.py`: `add_import`, then `delete_expired`, then `keep_newest_uncommitted(site.id, MAX_UNCOMMITTED_PER_SITE - 1, excluding=model.id)`, then `add_rows`, with a comment saying why the insert goes first. T033 passes, and `tests/integration/test_import_preview.py -k lifecycle` still passes
- [X] T038 [US2] Return `result` in `_to_response` in `applications/hematdaya-api/app/imports/router.py`, from `model.commit_result`, or null when there is none. T028, T031 and T032 pass
- [X] T039 [US2] Run `uv run pytest tests/unit/imports tests/integration/test_import_commit.py tests/integration/test_import_preview.py tests/integration/test_isolation.py -q`, three times for the race tests, and `make lint`, and fix what they find in `applications/hematdaya-api/app/imports/`

## Phase 5: User Story 3 - The result is exact (Priority: P1) MVP

**Goal**: The result names exactly what happened, the audit trail names the range, and the next read reflects the data with earlier evidence kept.

**Independent Test**: `uv run pytest tests/integration/test_import_commit.py -k "exact or insight"`. Counts equal database rows.

### Tests first

- [X] T040 [US3] Add exact tests to `applications/hematdaya-api/tests/integration/test_import_commit.py`. A file with one invalid row, in-file repeats and one mapped plus one new asset: `rows_added`, `rows_skipped` and `rows_duplicate` each equal the database or the preview's count; `rows_added` equals the count of `measurements` excluding `counter_delta`; `assets_created` and `assets_mapped` hold exactly `{id, name}` of what exists; `period` and `affected_from`, `affected_to` match the rows in the site zone, where a last row ending at local midnight belongs to the previous date; `committed_at` is the wall clock's, not `virtual_now`
- [X] T041 [US3] Add `test_exact_duplicate_only_reimport` to `applications/hematdaya-api/tests/integration/test_import_commit.py`, AT-33. Commit `csv10`, preview it again (`duplicate_rows == 10`), and commit that. 200, `rows_added == 0`, `rows_duplicate == 10`, `period` and both affected values null, `assets_created == []`, and `assets_mapped` names the asset. `TABLES` counts and both revisions are unchanged, apart from one more audit event with null dates. The second import is `committed`, and a replay adds no audit event
- [X] T042 [US3] Add counter tests to `applications/hematdaya-api/tests/integration/test_import_commit.py`, AT-37. Points 100, 130, 5, 20 Wh hourly give deltas 30 Wh and 15 Wh, no row over the reset interval, no negative energy, and a total of `"0.045"`. A one-row file stores its anchor and no energy, with `rows_added == 1`. Appending points 25, 10 to that first stream, whose last stored point is 20, adds a 5 Wh delta and treats the drop to 10 as a reset with no energy, and `affected_from` and `affected_to` cover only the change. The preview of that append still says the first-reading text (D17, recording the limit). A delta over two hours is `long_gap`. Replay of each leaves totals unchanged
- [X] T043 [US3] Add `test_exact_late_import_writes_one_audit_event` to `applications/hematdaya-api/tests/integration/test_import_commit.py`. Commit rows on 2026-10-20, then late rows filling 2026-10-18. The second import writes exactly one `audit_events` row: `action = import.committed`, `subject_type = import`, `subject_id` the import, the acting principal, `affected_from` and `affected_to` naming only the late rows' range, and `detail` equal to `{"rows_added", "rows_skipped", "rows_duplicate", "assets_created", "assets_mapped"}` as counts, with no key and no file content
- [X] T044 [US3] Add insight tests to `applications/hematdaya-api/tests/integration/test_import_commit.py`, D1 and D2. Descriptive path, reachable in production: on an `empty` session, commit 2026-10-19 to 2026-10-25, and `GET /api/v1/sites/{site}/insights?start_date=2026-10-19&end_date=2026-10-25` gives `learning_count == 1` and `comparable_count == 0`. Commit the three earlier weeks, and the same read gives `learning_count == 0`, `comparable_count == 1` and `observations == []` (AT-20), and `GET /api/v1/assets/{asset}/comparison` says `descriptive`. Revision path: seed through `AssetService` and `IngestService` a stored `origin = import` source with `resolution_mwh = 1000` and `source_label("tv")` on asset `TV`, four weeks long, with a change that qualifies and a gap in the current week. Read gives one observation at revision 1. Commit a CSV filling that gap through the route. The next read gives revision 2 as current, and `GET /api/v1/insights/{id}?revision=1` returns the first evidence unchanged, with `superseded: true` and `current_revision == 2`. A repeat of the commit makes no revision 3
- [X] T045 [US3] Add `test_exact_rows_after_site_clock_stay_invisible` to `applications/hematdaya-api/tests/integration/test_import_commit.py`, pinning D18. On an `empty` session, a file dated 2026-11-01 commits with `rows_added` equal to `rows_after_site_clock`, the readings are stored, and a summary of that date answers 200 with `energy_kwh` null and `energy_unavailable_reason == "no_data"`. A file ending exactly at 2026-10-26 00.00 WIB gives 0. Add `test_exact_imported_data_is_historical`: the source has `transport_status = historical`, and `GET /api/v1/sites/{site}/insights` holds no `stale` notice for it, however old its rows are
- [X] T046 [US3] Run T040–T045 and confirm T040–T043 and `test_exact_rows_after_site_clock_stay_invisible` fail on missing behavior. T044's two tests and `test_exact_imported_data_is_historical` pass already, because D1 adds no code and T025 sets the source's fields. To prove they can fail, temporarily skip the `ingest` calls for T044 and use `TransportStatus.SIMULATED_LIVE` for the last test, in `applications/hematdaya-api/app/imports/service/commit.py`, see them fail, and restore it. Record both in Notes

### Code

- [X] T047 [US3] Complete `result` in `applications/hematdaya-api/app/imports/service/commit.py`: `assets_created` and `assets_mapped` in stream order, `period` from `affected_period`, `affected_from`, `affected_to`, and `rows_after_site_clock` counted against `site_clock(site)` (`interval_end` or `measured_at` after it). T040, T041, T042 and T045 pass
- [X] T048 [US3] Add D21's `detail` to the audit event in `applications/hematdaya-api/app/imports/service/commit.py`: the counts of `rows_added`, `rows_skipped`, `rows_duplicate`, `assets_created` and `assets_mapped`, never the key or any file content. T043 passes
- [X] T049 [US3] Run `uv run pytest tests/unit/imports tests/integration/test_import_commit.py tests/integration/test_insights.py -q` and `make lint`, and fix what they find in `applications/hematdaya-api/app/imports/`

## Phase 6: Polish

- [X] T050 Change `test_nothing_claims_more_than_exists` in `applications/hematdaya-api/tests/unit/capabilities/test_capabilities.py`: pop `csv` and expect `available`, with the other adapters still `planned`, and do the same under `core-only`. Run it and see it fail
- [X] T051 Set `AdapterResponse(id="csv", status=CapabilityStatus.AVAILABLE)` in `applications/hematdaya-api/app/capabilities/service/service.py` (D25). T050 passes
- [X] T052 Add commit benchmarks to `applications/hematdaya-api/tests/integration/test_import_performance.py`, under its existing `IMPORT_BENCH=1` gate so CI does not carry them. Through the routes, on a fresh site: preview then commit for 150,000 interval rows, 150,000 counter rows, and 100 streams of 1,500 rows each, all within 10 MiB. Each asserts 200, `rows_added` and the stored count, and prints preview and commit seconds and the largest event-loop stall, from a 10 ms heartbeat task. A second run traces only the commit request under `tracemalloc`, started after the preview returns. It asserts a peak under 256 MiB for interval rows and prints the peak for the other two, with no bound: a counter commit measured 945.1 MiB, by D10. No time assertion: PRD §18's target belongs to 041's benchmark server
- [X] T053 Run `IMPORT_BENCH=1 uv run pytest tests/integration/test_import_performance.py -s -q`. Record elapsed seconds, stall, peak memory, bytes and machine in this file's Notes, on the Performance line of `specs/026-import-commit/plan.md` and in SC-003 of `specs/026-import-commit/spec.md`, and compare with PRD §18's 60 seconds, which also covers the preview. If it is over, report it: the formal benchmark stays with 041, and a worker is its own spec (D27)
- [X] T054 Run `COMPOSITION=core-only uv run pytest tests/unit/imports tests/integration/test_import_preview.py tests/integration/test_import_commit.py`, then add `tests/integration/test_import_commit.py` to the core-only step in `.github/workflows/hematdaya-api.yml` at the pertanian repository root (D26)
- [X] T055 Run `make openapi` in `applications/hematdaya-api/`, then `make generate-api` and `make check` in `applications/hematdaya-mobile/` on the Node version in `.nvmrc`, and confirm only `contracts/openapi.json` and `applications/hematdaya-mobile/src/api/schema.generated.ts` changed (D25)
- [X] T056 [P] In `applications/hematdaya-api/README.md`, add `POST /api/v1/imports/{import_id}/commit` to the endpoint table, note `result` on `GET /api/v1/imports/{import_id}`, and add `tests/integration/test_import_commit.py` to the test table
- [X] T057 [P] Set **Status** in `specs/026-import-commit/spec.md` to `Built, awaiting review`
- [X] T058 Confirm the flip and scope: `impor-data` is still `coming_soon` in `applications/hematdaya-mobile/src/features/registry.ts`, `git diff --name-only origin/main` holds no 027 path and no change to `IngestService` or `app/insights`, and the P1 diff is exactly D24's list
- [X] T059 Run `python3 docs/roadmap/check_traceability.py`, then `make check` in `applications/hematdaya-api/`, `uv run alembic heads` (one head, `0009`) and `SKIP=no-commit-to-branch uv run pre-commit run -c ../../.pre-commit-config.yaml --all-files`, and read the output. State which runtime was exercised: this is API only, with the mobile contract check from T055
- [X] T060 Left for the parent session, and only when the owner asks. Do not do this in a task-running agent. Commit as `feat(api): commit CSV imports atomically (spec 026)`, staging explicit paths under `applications/generic/hematdaya/` and `.github/workflows/hematdaya-api.yml`. Sync with `origin/main`, recheck that `uv run alembic heads` shows a single head and re-point `0009` if P1 merged a migration first, rerun T059, push `m5/import-commit`, and open the PR with `pr-generate-description` filling `.github/pull_request_template.md`. State in it D24's P1 changes, D4's fix to 025, and Open questions, and ask P1 to review the contract and replay evidence

## Requirement coverage

| Requirement | Tasks |
|---|---|
| FR-001 one transaction through `IngestService` | T020, T021, T025, T026 |
| FR-002 idempotent, key reuse refused | T028, T030, T031, T036 |
| FR-003 status with no lock | T028, T031, T038 |
| FR-004 audit, on-read evaluation, duplicate-only | T025, T041, T043, T044, T048 |
| FR-005 refusals under the lock | T029, T036 |
| FR-006 what a commit creates | T020, T022, T023, T025 |
| FR-007 stream limit | T007, T018 |
| FR-008 rows after the site clock | T045, T047 |
| FR-009 ownership, composition, errors | T002, T010, T021, T029, T030, T034, T054 |
| US1 scenario 1 | T020, T022, T023, T025 |
| US1 scenario 2 | T021, T025 |
| US2 scenario 1 | T028, T036 |
| US2 scenario 2 | T028, T031, T038 |
| US2 scenario 3 | T029, T036 |
| US2 scenario 4 | T029, T036 |
| US2 scenario 5 | T030, T036 |
| US3 scenario 1 | T040, T045, T047 |
| US3 scenario 2 | T025, T043, T044, T048 |
| US3 scenario 3 | T044 |
| Edge: stale preview, site-wide | T029, T032, T036 |
| Edge: counter deltas, reset | T042 |
| Edge: historical origin | T020, T045 |
| Edge: all-invalid stream | T005, T020, T025 |
| Edge: duplicate-only | T041 |
| Edge: long name | T006, T017, T020 |
| Edge: more than 100 streams | T007, T018, T052 |
| Edge: scope pairs outside the file | T023 |
| Edge: rows after the site clock | T045, T047 |
| Handoff: `parsed`, `value` not `raw_value` | T005, T019, T020 |
| Handoff: assets, sources, label | T006, T017, T020, T025 |
| Handoff: binding `effective_from`, later binding | T004, T005, T015, T019, T022, T025 |
| Handoff: `DISJOINT`, `UNKNOWN_OVERLAP` | T020, T023, T025 |
| Handoff: provenance | T020, T025 |
| Handoff: result column | T003, T011, T012, T014 |
| Handoff: stale error decision | T002, T005, T010, T029, T036 |
| 025 defect: long label | T006, T017, T020 |
| 025 defect: counter assumption | T042 |
| 025 defect: streams with no period | T005, T020, T025 |
| Lock order, no deadlock | T003, T031, T033, T037 |
| Reused key, different payload | T030, T036 |
| Ownership | T034 |
| Errors, catalog | T002, T010, T021, T029, T030 |
| Contract | T008, T026, T055 |
| Composition | T054 |
| Flip | T050, T051, T058 |
| Migration and single head | T003, T011, T059, T060 |
| SC-001 | T031 |
| SC-002 | T032 |
| SC-003 | T028, T052, T053 |
| SC-004 | T033, T037 |
| PRD AT-33, AT-34, AT-37 | T041, T028, T042 |
| PRD FR-06 §10.2 item 11 | T020, T021, T028, T040 |
| PRD FR-19 | T043, T044 |

T001, the checkpoints (T009, T024, T035, T046), the run tasks (T027, T039, T049), T013, T016, T056 and T057 serve the rows above without adding behavior of their own.

## Dependencies & Execution Order

- **Setup (T001) → Foundational (T002–T019) → US1 (T020–T027) → US2 (T028–T039) → US3 (T040–T049) → Polish (T050–T060).**
- T011 before T012, T012 before T013 and T014. T025 needs T014, T015, T016, T017 and T019.
- US2 and US3 extend `commit.py`, so they run in order. US1's first version stores a result with counts, because the CHECK requires one, and its audit event without `detail`.
- T037 changes 025's `preview.py`, so run `test_import_preview.py` after it.
- T053 after T047 and T048, so the number covers the finished commit. T055 after T038 and any later schema change. T059 last before T060.

### Parallel example

T002 to T008 touch different test files and can run together. So can T016 and T017. T056 and T057 can run any time after T049. Tasks inside a story share `test_import_commit.py` and `commit.py`, so they run in order.

## Implementation Strategy

All three stories are P1, and 027 needs all of them, so the MVP for this spec is the whole spec. US1 is the first review point: an import that commits whole or not at all, with no replay yet. US2 is the one to read closely, because it holds the locks. Stop after each checkpoint task and read the failure before writing code. Merge before round 4 starts, and do not begin 027 on this branch.

## Notes

Record the baseline, failing-test checkpoints and the measurement here as tasks finish.

### Evidence behind the decisions (2026-11-07, no repository file changed)

Run on merged code at `5ec2fba`, on a throwaway `postgres:17-alpine` container on port 55432, with scripts kept outside the repository and the container removed afterwards. Apple M3, 16 GiB, Darwin 27.2.0, Python 3.13.16.

| Check | Result | Decision |
|---|---|---|
| Replay of statements: commit `sites FOR UPDATE`, `imports FOR UPDATE`; preview `DELETE imports`, then `INSERT imports`, started in that order under a held site lock | `commit: DEADLOCK`, preview ok | D4 |
| The same, with the preview's `INSERT` first | commit ok, preview ok | D4 |
| `INSERT INTO imports` while another transaction holds `sites FOR UPDATE` | The insert waits | D4 |
| `select(ImportRecord).with_for_update()` after an earlier read in that session, once another session committed | Returns `previewed` without `populate_existing`, and `committed` with it | D3 |
| 150,000 interval rows, 5,000 per `ingest`, from staged rows to `COMMIT` | 9.43 s, largest stall 0.08 s, peak 36.1 MiB. 9,450,044 bytes, preview 9.75 s | D10 |
| 150,000 interval rows, one `ingest` | 11.34 s, stall 2.03 s, peak 788.2 MiB | D10 |
| 150,000 counter rows, one `ingest` (299,999 stored with deltas) | 21.23 s, stall 2.00 s, peak 945.1 MiB. 5,888,920 bytes, preview 9.01 s | D10, D27 |
| `len("Impor CSV · " + ("İ" * 60).lower())` | 132 | D16 |
| `alembic heads`, and `migrations/versions/` on all 24 `origin` branches | `0008`, no `0009` or later anywhere. `specs/028-scope-api/plan.md` names `0010` | D9 |
| `grep` for committed rows in tests | `make_import(status="committed")` in `test_import_preview.py` and `_import(status=COMMITTED)` in `test_import_storage.py` leave committed rows with no result, and `conftest.py` says tests share the development database | D9 |
| `parser.py` L242 | `cadences` comes from `scan.timestamps` only, so explicit-interval streams store `cadence_seconds` null | T020 |
| `grep -rn invalidat app/insights` | No matches | D1 |
| `grep -rn adapters src` in the mobile app, leaving out `schema.generated.ts` | Only `client.ts` and `client.test.ts` | D25 |
| `TIMEOUT_MS` in `src/api/client.ts` | 10,000 ms | D27 |

Elapsed seconds under `tracemalloc` are not comparable, and they are left out. These runs are a commit-shaped script, not the service, so T053 replaces them with the real numbers.

### Baseline (T001)

`make run-dependencies` and `make migrate` succeeded on the existing local database. `uv run alembic heads` said `0008 (head)`, and `uv run pytest tests/unit/imports -q` said 585 passed.

### Failing-test checkpoints (T009, T024, T035, T046)

Run on Postgres 17 in local Docker. Each line was read from a real run before the code it covers existed.

| Task | Observed before the code | Passing from the start, and why |
|---|---|---|
| T009 | `test_commit_plan.py` and `test_import_errors.py` failed at import, on the missing module and error classes. 13 of 14 integration tests failed (`commit_result` missing, `TypeError` on `effective_to`, the 101-stream file not blocked). 9 unit tests failed in `test_mapping`, `test_classify` and `test_contract` | `test_add_binding_without_an_end_stays_open`, `test_source_label_keeps_short_keys_unchanged` and `test_resolve_source_matches_a_stored_long_label` pin behavior that must not change |
| T024 | All 20 US1 tests failed with 404 from the missing route, on `assert 404 == 200` or `assert 404 == 500` | None |
| T035 | 22 of 46 selected tests failed. T033 failed on `deadlock detected` on `INSERT INTO imports`, answered as a 500. The stale and acknowledgment tests failed on writes past a missing gate, and key tests on `ux_imports_site_idempotency` | See the proofs below |
| T046 | `test_exact_counts_equal_the_database`, `test_exact_duplicate_only_reimport`, `test_exact_counter_append_to_a_stored_stream`, `test_exact_late_import_writes_one_audit_event` and `test_exact_rows_after_site_clock_stay_invisible` failed on the empty result fields | See the proofs below. T042's reset, anchor and long-gap tests also passed from the start, because T025 already stores counters through 006 |

Each test that passed from the start was proved able to fail with a temporary change, then restored:

| Temporary change | What failed |
|---|---|
| `sites.lock` in place of `lock_owned` in `commit.py` (T035) | `test_foreign_resources_look_missing[POST .../commit]`: `assert 500 == 404` |
| `lock_owned` in `ImportPreviewService._owned` | `test_race_status_does_not_wait_for_a_commit` |
| `find_by_key` not filtering on the site | `test_key_is_scoped_to_its_site` |
| No `pattern` on the header | `test_key_that_is_missing_or_malformed_is_refused[short]` |
| `delete_expired` skipped in the preview | `test_refused_a_preview_purged_by_a_new_one` |
| `ingest` skipped in `_flush` (T046) | Both `test_insight_*` tests, `test_exact_counter_reset_has_no_energy`, `test_exact_counter_long_gap_is_flagged`. `test_exact_counter_anchor_has_no_energy` did not fail, so it gained a stored-row count |
| `TransportStatus.SIMULATED_LIVE` (T046) | `test_exact_imported_data_is_historical`, on a `stale` notice naming the source |

Written after their code, once `make check`'s coverage named the lines nothing reached, each proved by a temporary change: `test_race_commit_waiting_on_a_purge_finds_it_gone` (no `None` check), `test_atomic_interval_rows_reach_ingest_in_batches` (no flush at 5,000, and no guard on an empty flush), `test_atomic_counter_rows_reach_ingest_at_once` (counters batched), `test_atomic_row_outside_its_mapping_rolls_back`, and two more cases of `test_atomic_failure_leaves_nothing_and_the_preview_usable`.

**D3, corrected by measurement.** Removing `populate_existing` left `test_get_import_locked_sees_what_another_session_committed`, as first written, and both `test_race_*_commits_once` tests passing. The identity map is weak, and `get_import` drops its record as soon as it returns a model, so on CPython the next select reads afresh. The stale read needs a strong reference to the record, which the measurement in the table above had and the service does not. So D3 stands as a safeguard, not as the thing keeping SC-001 true today. The two storage tests now hold the record, one of them waiting on a real row lock, and both fail without `populate_existing` (`assert 'previewed' == 'committed'`). Nothing else changed.

### Concurrency repeats

`tests/integration/test_import_commit.py -k race` (T031, T032, T033 and the reverse purge) and the 3 `get_import_locked` tests in `test_import_storage.py`, in separate pytest processes, on Postgres 17 in local Docker: 25 of 25 runs of the first 10 tests, then 12 of 12 runs of all 11. No flake.

### Measurement (T052, T053)

Through the routes, `IMPORT_BENCH=1`, on an Apple M3 with 16 GiB, Darwin 27.2.0, Python 3.13.16, Postgres 17.11 in local Docker. In-process ASGI transport, so no network, and a laptop, not 041's benchmark server. "Stall" is the largest gap of a 10 ms heartbeat task on the event loop.

| 150,000 rows | Bytes | Preview | Preview stall | Commit | Commit stall | Together | Commit peak |
|---|---|---|---|---|---|---|---|
| Interval, 1 stream | 9,450,044 | 9.64 s | 0.34 s | 9.30 s | 0.09 s | 18.93 s | 37.7 MiB, against the 256 MiB bound |
| Counter, 1 stream | 5,738,920 | 8.97 s | 0.19 s | 20.62 s | 2.06 s | 29.60 s | 938.7 MiB, no bound (D10) |
| 100 streams of 1,500 rows, with 4,950 relations | 8,985,044 | 9.08 s | 0.31 s | 13.92 s | 0.13 s | 23.01 s | 210.9 MiB, no bound |

All three are under PRD §18's 60 seconds on this machine, which is not the formal measurement: 041 owns that. The counter's 2.06 s stall and 938.7 MiB peak match the script's 2.00 s and 945.1 MiB, and they sit inside `IngestService.ingest` (Open questions, item 4). The preview route alone, rerun after D4: 9.34 s, and a 156.6 MiB peak under `tracemalloc`, unchanged against its 256 MiB bound.

### For 027 (found here, not fixed here)

- **Client timeout.** `TIMEOUT_MS` is 10 s and a 150,000-row commit took 9.43 s on interval rows and 21.23 s on counters on this machine. So a large commit will time out on the client while it succeeds on the server. Treat a timeout as unknown: `GET /imports/{id}`, and if it says `previewed`, retry with the same key. That retry waits on the lock and replays. Consider a longer timeout for this one call.
- **Provenance text.** `HDProvenanceTag`, merged in PR #28, shows `Data impor`. The spec says `Data historis · Impor CSV`. 026 provides `origin = import` and `transport_status = historical`, and the text is 027's.
- **Counter assumption on append** (D17). The preview may say "first reading" when a file appends to a stored counter, and it does not warn about a reset against stored points.
- **Saran after a CSV** (D2). An imported asset shows a descriptive comparison and no automatic observation, by PRD §12 and AT-20.
- **`IMPORT_STALE` and `IMPORT_ACK_REQUIRED`.** Show `details[0].msg`. `IMPORT_ACK_REQUIRED` links to the checkbox, and `IMPORT_STALE` leads back to a new preview.
- **`rows_after_site_clock`.** Show it when it is above zero, until Open questions item 1 is decided.

### For P1 review

- D24's list is the whole of the diff in P1's modules.
- One commit may call `advance_measurement_revision` several times, through `ingest`, against that method's "Call once" docstring (D10). Please confirm it is acceptable: nothing compares more than equality, and `SummaryResponse.revision` only needs to grow.
- A counter commit of 150,000 rows blocks the event loop for about 2 s and peaks at about 945 MiB inside `IngestService.ingest`, which 026 does not change. Rule 006 says never to block the loop, so this is a known exception until decided. Moving `normalize` and `counter_deltas` to `asyncio.to_thread`, or the windowing that method's `ponytail` comment suggests, is P1's choice.
- `SiteService.update` changes `timezone` with no revision. 026 checks it itself (D6), and it may matter to others.

### Conflicts in other documents (not edited here)

| Document | Says | Reality | Who decides |
|---|---|---|---|
| `specs/021-insights/plan.md` Design | "Expose an invalidation operation so 026 and other relevant writes record the affected identities or periods" | No such operation exists, and none is needed (D1) | P1 |
| `docs/roadmap/architecture.md` Imports | Commit "affected insight invalidation together" | The same sentence block says observations are re-evaluated on read. Behavior matches D1, and only the word "invalidation" does not. `architecture.md` wins over a spec until changed in a PR, so this needs rewording there | Owner |
| `specs/025-import-preview/plan.md` Data Model | "026 writes the others", meaning `committed` and `rejected` | 026 writes only `committed` (D7) | P2, at merge |
| `specs/025-import-preview/tasks.md` D6 | The label "stays within 120 (12 + 60)" | `lower()` can double a name (D16) | P2, at merge |
| `docs/roadmap/README.md` step 2 | The branch takes the folder's exact name | This work is on `m5/import-commit`, as 025 was on `m5/csv-parser` | Owner |

## Open questions

Each needs a decision outside this spec. The tasks implement the safe default, so none blocks 026.

1. **Clock of the `empty` workspace.** "Mulai" opens a demo site with `virtual_now` fixed at 2026-10-26 00.00 WIB. CSV dated after that commits, is stored and shows nowhere, and `rows_after_site_clock` says how many rows (D18). 027's AT-03 cannot reach "real totals" with a recent file until this is decided. Should `empty` follow the wall clock, advance to the imported range, or stay fixed? Owner and P1, since 008 owns it.
2. **Scope across files.** `scope` writes relations only between assets in the same file (D14). A second file with a new asset leaves the site total refused as `unconfirmed` until 029 lets the user confirm it. Per-asset values stay. Keep that, or ask a wider question in 027? Owner.
3. **Stream limit.** `MAX_IMPORT_STREAMS = 100` is not in the PRD (D15). Confirm or change it. Owner.
4. **Counter commit cost.** About 945 MiB peak and a 2 s event-loop stall for 150,000 counter rows (D10), which rule 006 would otherwise forbid. Acceptable until 041, or does P1 want the thread or the windowing sooner? P1.
5. **Staged rows after commit.** They stay (D28). 038 decides retention.

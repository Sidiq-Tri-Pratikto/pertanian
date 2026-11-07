# Feature Specification: Import commit

**Feature Branch**: `m5/import-commit`
**Created**: 2026-10-30
**Status**: Built, awaiting review
**Milestone**: M5 CSV
**Depends on**: 021, 025
**Size**: M
**Covers**: FR-06, FR-19, AT-33, AT-34, AT-37
**Flips**: manifest adapter `csv` → `available`

## User Scenarios & Testing

### User Story 1 - All or nothing (Priority: P1)

**Why this priority**: FR-06: no bad upload can erase earlier data.

**Independent Test**: Fail mid-commit; nothing changed.

**Acceptance Scenarios**:

1. **Given** a valid preview, **When** committed, **Then** all accepted rows, new assets, sources, bindings and relations appear in one transaction.
2. **Given** a failure during commit, **When** it rolls back, **Then** no row, asset, source, binding, relation or audit event remains, both revisions are unchanged, and the preview stays usable with the same key.

### User Story 2 - Retry is safe (Priority: P1)

**Why this priority**: AT-34.

**Independent Test**: Commit twice with one key.

**Acceptance Scenarios**:

1. **Given** a committed import, **When** commit is repeated, **Then** the first result returns with `replayed: true` and no reading is added.
2. **Given** a connection lost after commit, **When** the client reads `GET /imports/{id}`, **Then** it finds `committed` and the first result. While a commit is still in flight it finds `previewed`, and a retry with the same key waits and replays.
3. **Given** a blocked preview, **When** commit is called anyway, **Then** the service refuses with `IMPORT_BLOCKED`.
4. **Given** a preview with skipped rows, **When** commit is called without `acknowledge_skipped`, **Then** the service refuses with `IMPORT_ACK_REQUIRED`.
5. **Given** a key already used for another import of the site, or with a different `acknowledge_skipped`, **When** commit is called, **Then** the service refuses with `CONFLICT` and applies nothing.

### User Story 3 - The result is exact (Priority: P1)

**Why this priority**: Users must see what actually happened.

**Independent Test**: Compare counts with database rows.

**Acceptance Scenarios**:

1. **Given** a commit, **When** it succeeds, **Then** the result lists rows added, skipped, duplicated, assets mapped and created, the period affected, and how many rows end after the site clock.
2. **Given** a late import over an existing period, **When** committed, **Then** the same transaction advances `measurement_revision` and writes one audit event naming the range. The next insight read evaluates that period from the new data, publishes a new revision when the evidence changed, and keeps earlier revisions readable.
3. **Given** a period served only by imported data, **When** insights are read, **Then** the comparison is descriptive and no automatic observation is published, because imported sources have unknown resolution (PRD §12, AT-20).

### Edge Cases

- A preview that has expired, or whose site `measurement_revision`, `binding_revision` or timezone changed, is refused with `IMPORT_STALE` and a re-preview message. The check is site-wide, so any data change on the site makes every open preview stale, including one over unrelated rows. When two distinct previews contend, only a still-valid preview may commit.
- Counter imports store deltas, and a reset interval has no energy.
- Imported data has `origin = import` and `transport_status = historical`, never a disconnected live meter. 027 renders this as `Data historis · Impor CSV`.
- A stream whose rows are all invalid creates no asset, source or binding.
- A duplicate-only commit reports zero new rows and changes no domain data.
- A 60-character name that lengthens when lower-cased still gets a valid source label, and its reimport still matches.
- A preview with more than 100 streams holding staged rows is blocked.
- `scope` answers for the file's own assets. A pair of a file asset and an asset outside the file stays unconfirmed, so the site total is refused while per-asset values stay. See Open questions in [tasks.md](tasks.md), item 2.
- Rows ending after the site clock are stored and appear in no read until the clock reaches them. On the `empty` demo workspace the clock is fixed at 2026-10-26 00.00 WIB, so they do not appear. The result says how many. See Open questions in [tasks.md](tasks.md), item 1.

## Requirements

### Functional Requirements

- **FR-001**: Commit MUST be one transaction through `IngestService`, covering readings, assets, sources, bindings, relations, the audit event, the stored result and the status.
- **FR-002**: Commit MUST require `Idempotency-Key` and MUST be idempotent: `imports.status` and the stored result decide a repeat, and unique measurement identity backs it. A repeat returns the first result with no side effects. A key reused for another import of the site, or with a different `acknowledge_skipped`, MUST be refused with nothing applied.
- **FR-003**: `GET /imports/{id}` MUST report the last confirmed status, plus the first result once committed, without taking a lock, for as long as the import exists. A client past its timeout can therefore find the outcome.
- **FR-004**: The first successful commit MUST write one audit event with the affected range. A data-changing commit MUST advance `measurement_revision` in the same transaction, so the next insight read evaluates the new data before returning anything. It stores no separate invalidation record, because every read path already evaluates under the site lock. A duplicate-only result records no affected periods, and replay writes no new audit event.
- **FR-005**: Commit MUST refuse, under the site lock and with nothing changed, a blocked preview (`IMPORT_BLOCKED`), an expired or stale preview (`IMPORT_STALE`), and a preview needing acknowledgment without it (`IMPORT_ACK_REQUIRED`).
- **FR-006**: Commit MUST create assets, sources and bindings only for streams with accepted rows. Every accepted row MUST fall inside a binding of its source, and no two authoritative ranges of an asset may overlap. `scope` MUST write its relation for each pair of the file's assets that has no relation or containment yet.
- **FR-007**: A preview MUST be blocked when the file has more than 100 streams holding staged rows.
- **FR-008**: The result MUST report the rows ending after the site clock.
- **FR-009**: A foreign import MUST answer `NOT_FOUND` before any replay. Commit MUST work under `COMPOSITION=core-only`. Every failure MUST follow rule 008.

### Key Entities

Import from 025, plus `commit_result`, the stored first result.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Concurrent double commit produces one result, proven by an integration test.
- **SC-002**: Concurrent commits of distinct previews on one site leave one valid result and one stale preview, with no partial changes, proven by an integration test over a shared source interval and a shared binding.
- **SC-003**: Through the routes, preview plus commit of a 150,000-row file within 10 MiB is timed against PRD §18's 60 seconds, which 041 measures formally on its benchmark server. If a client gives up first, `GET /imports/{id}` and a retry with the same key still recover the outcome. Measured on an Apple M3 with 16 GiB and Postgres 17 in local Docker: 18.93 s for 150,000 interval rows and 29.60 s for 150,000 counter rows, so under the target here, with 041's formal number still owed.
- **SC-004**: A commit and a preview purge of the same import finish together with no deadlock, proven by an integration test.

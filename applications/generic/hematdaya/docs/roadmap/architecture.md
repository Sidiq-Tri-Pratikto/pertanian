# HematDaya architecture decisions

Binding for every spec in `specs/`. The PRD (`docs/product/PRD-EN.md`) says what the product does. This file says how it is built. When a spec and this file disagree, this file wins until it is changed in a PR. The constitution wins over both.

## System shape

One modular monolith API, one mobile client, one Postgres database.

```mermaid
flowchart LR
    Mobile["hematdaya-mobile<br/>Expo, Android, iOS, web"] -->|"HTTPS, /api/v1"| API["hematdaya-api<br/>FastAPI"]
    API --> PG[("Postgres 17")]
    CSV["CSV upload"] --> API
    Fixture["Demo fixture generator"] --> API
    Live["Verified meter adapter (046, gated)"] -.-> API
```

The API is the one calculation authority. The mobile app never computes energy, cost, coverage, comparison or percentages. There is no TypeScript calculation engine, so the demo needs a reachable API.

## API modules

Each is a feature module under `applications/hematdaya-api/app/` following rule 005. A module imports another module's service interface, never its repository.

| Module | Owns | First spec |
|---|---|---|
| `capabilities` | Manifest, composition validation, capability guard | 001, 011 |
| `identity` | Principals, the request's acting principal | 004 |
| `sites` | Sites, timezone, context, clock | 004 |
| `assets` | Assets, sources, bindings, relations | 005 |
| `audit` | Append-only change records | 005 |
| `measurements` | Normalized readings, identity, revision | 006 |
| `demo` | Fixture generator, scenarios, demo sessions, reset | 007, 008 |
| `energy` | Periods, summaries, coverage, gaps, ranking, history | 009, 010 |
| `scope` | Aggregation selection, overlap rules | 009, 028 |
| `cost` | Tariffs, cost of energy (optional capability) | 018 |
| `baseline` | Matched windows, common mask, readiness | 020 |
| `insights` | Rules, evidence snapshots, revisions, notices | 021 |
| `feedback` | Useful, not relevant, snooze, hide, restore | 023 |
| `imports` | CSV parsing, previews, atomic commit | 024–026 |
| `schedules` | Weekly windows, effective schedule, outside split (optional capability) | 030 |
| `output` | Output metric and inputs (optional capability) | 032 |
| `catalog` | Source catalog, simulated enrollment | 035 |
| `auth` | Users, sessions, rate limits | 036 |
| `exports` | Export, deletion, retention | 038 |

## Data model

Created by the spec named. Every table carries `created_at`; identifiers are UUID unless noted.

| Table | Key columns and constraints | Spec |
|---|---|---|
| `principals` | `kind` (`demo`, `user`) | 004 |
| `sites` | `owner_principal_id` → principals, `kind` (`demo`, `standard`), `name`, `context`, `timezone`, `currency`, `virtual_now` (required for demo and absent for standard), then `binding_revision` and `measurement_revision` | 004–006 |
| `assets` | `site_id`, `name`, `category`, `location`, `scope_kind` (`device`, `group`, `circuit`, `site_total`), `parent_asset_id`, `expected_use` (`unknown`, `continuous`, `scheduled`, `intermittent`), `archived_at` | 005 |
| `sources` | `site_id`, `label`, `origin` (`live`, `import`, `dataset_replay`, `simulated`), `measurement_kind`, `cadence_seconds`, `resolution_mwh` (nullable means unknown), `transport_status` | 005 |
| `bindings` | `source_id`, `asset_id`, `effective_from`, `effective_to`, `authoritative`; partial `EXCLUDE` on overlapping authoritative ranges per asset | 005 |
| `asset_relations` | `site_id`, `from_asset_id`, `to_asset_id`, `kind` (`contains`, `unknown_overlap`, `disjoint`); same site, no self-reference, no cycle. `disjoint` is positive evidence of separate loads; a missing relation never is | 005 |
| `audit_events` | `site_id`, `actor_principal_id`, `action`, `subject`, `affected_from`, `affected_to`, `detail`; append-only | 005 |
| `measurements` | Source record ID or shape-specific fallback identity, `kind`, interval bounds or `measured_at`, `energy_mwh` BIGINT, `received_at`, `quality`, `revision`. Uniqueness and current reads use the same identity | 006 |
| `demo_sessions` and creation operation records | Session scope, bearer digest, expiry, operation identity and bounded replay metadata | 008 |
| `aggregation_selections` | `site_id` (unique), `revision` | 028 |
| `aggregation_selection_assets` | `selection_id`, `asset_id` | 028 |
| `tariffs` | `site_id`, `effective_from`, `milli_rupiah_per_kwh` BIGINT `>= 0`, `provenance` (`synthetic`, `user`) | 018 |
| `insights` | `site_id`, `kind`, `asset_id`, `period_start`, `period_end`, stable `identity_key`, `current_revision` | 021 |
| `insight_revisions` | `insight_id`, `revision`, `evidence` JSONB, `policy_id`, `policy_version`, `superseded_at` | 021 |
| `insight_feedback` | `insight_id`, `revision`, `principal_id`, `action`, `until` | 023 |
| `imports` | `site_id`, `status`, `file_name`, `content_sha256`, `mapping` JSONB, counts, `idempotency_key` unique per site | 025 |
| `import_rows` | `import_id`, `data_row`, `file_line`, `status`, `parsed`, staged rows | 025 |
| `schedules`, `schedule_windows` | Weekly windows, version, `effective_from`, `is_correction` | 030 |
| `asset_schedule_overrides` | `asset_id`, `mode` (`inherit`, `none`, `continuous`, `custom`), `schedule_id` | 030 |
| `output_metrics`, `output_inputs` | Definition, numerator assets, unit, method, quantities | 032 |
| `users`, session and credential records | Owner identity, hashed opaque access and refresh credentials, revocable session families | 036 |
| `exports`, `deletion_requests` | Owner-only exports and purge status that survives active site removal | 038 |

## Binding decisions

### Ownership

`sites.owner_principal_id` → `principals(kind)` exists from the first migration. A demo session and a user are both principals, so authorization has one shape. Auth (036) adds `users` and never rewrites sites. Every read and mutation resolves the site through the acting principal. A resource owned by someone else returns `NOT_FOUND`, so its existence never leaks. AT-41 runs with two principals from 004 onward, and each later data PR adds its routes to that test.

### Demo sessions

Demo is a public write. Some scenarios seed thousands of rows, so admission enforces active capacity and a shared creation budget in the same transaction as the set-based seed. Creation has a bounded replay window with a separate proof. Neither bearer tokens nor replay proofs are stored in plaintext. Expired or purged sessions take the user back to a new session choice. "Mulai" before auth (036) opens a labelled expiring workspace.

### Two clocks

`sites.virtual_now` (demo sites only) drives periods, staleness, snooze and "today". The wall clock drives `received_at`, audit, TTL and security. One dependency, `site_clock(site)`, returns the right `now`; nothing else calls `datetime.now` for product time. Queries exclude intervals ending after now, and include a full interval that ends exactly at now.

### Numbers

Store energy in integer mWh and tariff in integer milli-rupiah per kWh. Compute cost in nano-rupiah, retaining exact fractions when a supported interval split produces them, and round once at the response. Use decimal strings on the wire (`"14.700"`, `"22050"`) through a string-only Pydantic type because Pydantic `Decimal` input also accepts JSON numbers. Unavailable values are `null` beside a stable reason such as `missing_tariff`, `no_schedule`, `no_output`, `insufficient_history`, `partial_coverage`, `scope_conflict` or `capability_disabled`. The mobile app formats these strings for display without parsing them into floats.

### Reads

Compute on read with SQL aggregation (`SUM`, `range_agg` for coverage union, `generate_series` for buckets). No rollup tables until the benchmarks in 041 fail. FR-19 recompute therefore means creating a new insight revision, not rebuilding aggregates. Bound every range and page: at most 1,000 buckets per series.

### Bindings and conflicts

A partial `EXCLUDE` constraint covers authoritative bindings only. Overlapping non-authoritative candidates can represent unresolved source authority. A combined total requires proven disjoint scope and a valid effective binding over each contributing interval. 009 owns read-time validity and defaults. 028 owns persistence and the read-only preview and atomic write for proposed selection and source authority.

### Imports

Previews are staged in Postgres (`imports`, `import_rows`) so they survive a restart and any instance can serve them. Commit serializes same-import replay and overlapping work on shared sources or bindings. Revalidate the staged assumptions under the lock and commit readings, result, audit and affected insight invalidation together. A repeated commit returns the first result. Affected observations are re-evaluated on read under 021, with historical evidence preserved.

### Transactions

One request is one transaction. `SessionDep` commits before the response is sent, and repositories only flush. Use the owned site row as the shared write lock for binding, scope and measurement changes, with revisions advanced in the same transaction. Import commits acquire the site lock before the import row. Demo admission follows the lock order in 008. See rule 005.

### Contract

`contracts/openapi.json` is generated by `make openapi` and drift-checked in CI on every PR. `src/api/schema.generated.ts` comes from it. Golden responses in `contracts/golden/` (added in 009) pin exact fixture numbers across the boundary; they replace the TypeScript parity test suggested in the old native handoff.

### Capabilities

`cost`, `schedule` and `output` are optional capabilities. Disabled ones are refused at the service boundary by one guard, with a stable reason, wherever the request comes from (011). The manifest explains; it never grants.

### Mobile

- Server state lives in TanStack Query from 012. No client copy of business data beyond its cache.
- Navigation context (period, scope, site) lives in one provider and survives tab switches.
- Detail routes go in `src/app/(tabs)/(beranda,perangkat,saran)/`, so the tab bar stays and back stays in the tab.
- `src/components/hd/` ports a component when a feature first needs it, with the same name and meaning as `window.HD`.
- No `@gorhom/bottom-sheet`, FlashList or `expo-sqlite` until a measured need. Sheets use RN `Modal`, with focus into the sheet and back to the opener verified.
- `expo-secure-store` has no web build, so 036 decides web session handling.
- Until 039 a phone reaches the API over LAN. Release builds block cleartext HTTP, so a release build needs a deployed HTTPS API.
- Charts use `react-native-svg` with a visible text summary and a data table.

## API conventions

| Topic | Rule |
|---|---|
| Base path | `/api/v1`; health stays at `/health/live` and `/health/ready` |
| Auth header | `Authorization: Bearer <token>`, for demo sessions and users alike |
| Time | RFC 3339 UTC instants; ISO local dates for periods; half-open `[start, end)` windows derived from the site's calendar |
| Period query | `start_date` and `end_date` (inclusive local dates) or `preset` (`today`, `this_week`, `last_7_days`); every response echoes the resolved UTC window and timezone |
| Lists | `limit` (max 100) and opaque `cursor` |
| Idempotency | `Idempotency-Key` for demo creation, tariff writes, import commit, enrollment and feedback. Demo creation also requires the separate replay proof from 008 |
| Errors | The envelope in `app/core/errors`; new failures get a typed error, a code in `codes.py`, a row in `public.py`, and a row in `docs/error-handling/catalog.md` |
| Copy | User-facing messages are Indonesian and two clauses: what happened, what to do next |

## Definition of done for every PR

- `make check` passes in each changed application; generated contract and tokens have no drift.
- Failure paths are tested, including an owner-isolation case for new data routes.
- The manifest or registry entry flips only for what actually shipped.
- `docs/error-handling/catalog.md` matches new codes.
- Verification says which runtime was exercised. A web run is never reported as a native result.
- Nothing states a diagnosis, verified waste, verified savings, or an unqualified live connection.

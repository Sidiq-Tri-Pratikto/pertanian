# HematDaya — Product Requirements Document

Version: Generic 1.3. Date: November 8, 2026 (Asia/Jakarta).
Document language: English. Product interface: Indonesian by default, with English selectable. Initial currency: IDR.
Status: accepted product and modular-architecture direction; development specification, implementation verification and field validation are pending.

## 0. Document authority and evidence status

This document defines HematDaya product behaviour and acceptance requirements. The product owner has accepted the reusable modular-monolith direction in section 15; acceptance of that direction is not evidence that it has been implemented. Resolve requirement conflicts in this order: latest explicit product-owner decision → this PRD → an explicitly approved implementation decision. Record approved changes with their affected requirements and verification criteria.

Evidence labels used throughout:

| Label | Meaning |
|---|---|
| Required | Behaviour that must be implemented and verified for generic release |
| Proposed target | An engineering or research acceptance target, not a measured result |
| Deferred | Outside generic v1; must not become a prerequisite for core use |

This is a development specification, not evidence of an implemented application, verified integration, production service, field accuracy, user-study outcome or realized savings. Every acceptance test starts as **not run**; a pass requires evidence against the implemented release and the stated input, runtime and scope. The requirements are self-contained.

## 1. Applicability contract

HematDaya serves household, business and industrial users through one electricity-monitoring and advice product. Every context uses the same measurement semantics, scope-safe calculations and evidence rules. Context selection is optional; a useful core journey requires neither AC, an operating schedule nor production data. Household and industrial journeys are separate release gates.

Generic means reusable electricity monitoring logic, not universal hardware compatibility, automatic appliance identification, or equal suitability for every industrial installation. The family boundary is related electricity-monitoring and advice products, including household, business, industrial and other measured-electricity contexts. An unrelated domain with different user jobs or invariants is a separate product; useful UI or infrastructure patterns may be reused without forcing its domain into HematDaya.

## 2. Product purpose and non-negotiable contract

HematDaya helps a person understand how electricity is used within a declared measurement scope and decide what to investigate or adjust. The same core product must work for a refrigerator and router at home, lighting in a shop, or a compressor and oven in a workshop.

It answers, where supported by data:

1. How much electrical energy was recorded in this period?
2. What is the estimated energy cost when a tariff is known?
3. Which monitored assets contribute most within the selected scope?
4. How does consumption compare with equivalent earlier periods?
5. What happened outside the user's expected-use windows, if any were supplied?
6. How much energy was used per output unit, if a valid output metric was supplied?
7. What evidence supports each observation, and what remains unknown?

Core principles:

- **Monitoring and advice only.** No commands, mains cutoff, relays, IR remotes, thermostat control, arrival automation, or unattended switching.
- **No mandatory AC.** No screen, calculation, fixture, onboarding branch, or acceptance test may depend on an air conditioner being present.
- **Useful without production or a schedule.** Energy, contribution, history, data quality, and eligible trend observations remain available.
- **Honest scope.** A plug meter is not a whole-home or whole-factory reading. A circuit reading is not evidence of each connected appliance's consumption.
- **Evidence before advice.** Categories, power patterns, and an offline meter do not prove faults, occupancy, waste, or an asset being off.
- **One shared product.** Context presets cannot fork the calculation engine, schema, or app into separate household and industrial products.

## 3. Users, contexts, and successful outcomes

| User/context | Example question | Minimum successful outcome |
|---|---|---|
| Household resident | “Which monitored device used the most this week?” | Contribution and history without factory setup |
| Renter or shared-home resident | “What did the devices I measure use?” | Clearly scoped totals; no claim about unmeasured rooms or shared billing |
| Shop, office, or service-business operator | “Did usage change outside opening hours?” | Optional schedule and matched comparison |
| Workshop or IKM owner | “Did energy per batch change?” | Optional output metric with explicit units and measurement boundary |
| Industrial operator | “Which measured circuit or machine changed?” | Compatible source ingestion with overlap-safe scope and data-quality evidence |
| User who does not choose a sector | “Can I inspect this CSV?” | Full core journey with neutral labels |

Initial product: one owner account and one active site; several assets and sources within it. A site may represent a home, shop, workshop, or industrial location. The data model identifies the site from day one. Cross-site dashboards, team permissions, district aggregation, and enterprise administration are deferred.

Optional context presets: `household`, `business`, `industry`, `unspecified`. Default is `unspecified`; selecting a preset is skippable. A preset changes introductory examples and demo selection only. It must not infer occupancy, set a tariff, enable notifications, assign a schedule, or activate output metrics. Changing a preset preserves all readings and settings.

Proposed research targets must be evaluated separately for household and business/industrial participants: at least 4 of 5 first-time users complete core interpretation tasks without help; at least 4 of 5 identify the largest measured contributor within 30 seconds. Combined averages cannot hide one segment failing. No field effectiveness or savings claim is made by these targets.

## 4. Release scope

### 4.1 Required generic v1

- Isolated hardware-free demo, account access for saved server data, one owned site.
- Arbitrary monitored assets with names, categories, optional location labels, and an explicit measurement scope.
- CSV historical import as a complete initial data path; a supported live-meter path only after its adapter and physical suitability are verified.
- Interval energy, estimated cost, contribution, history, matched historical comparisons, freshness, and temporal coverage.
- Optional weekly expected-use schedule, with multiple windows and overnight support.
- Optional output-normalized energy metric for users who need it.
- Evidence-bearing observations, conservative advice, and optional feedback.
- Empty, learning, partial, stale, offline, conflicting-source, unsupported-capability, and invalid-import recovery.
- Shared Android, iOS, and web implementation with a bilingual interface and accessibility requirements.
- Deterministic household and industrial demo fixtures, using the production calculation path.
- Concrete shared-domain, optional-capability and adapter boundaries; validated product composition and a shared-source release/upgrade process as defined in FR-21–22 and section 15.

### 4.2 Deferred

All physical control; weather or occupancy inference; automatic load disaggregation; fault diagnosis; predictive maintenance; non-electric energy such as fuel or heat; solar generation, export, batteries, and signed net-energy accounting; utility-bill reconciliation; demand, reactive-power, tiered or time-of-use billing; cross-user sharing; multiple-site dashboards; sector benchmarks; automated savings verification; paid cloud AI; optional ML beyond the baseline; certification claims.

Microservices, a dynamic plugin platform, an arbitrary rules/workflow engine, per-client source forks, SaaS billing, and self-service tenant provisioning are not required for generic v1. Reuse does not require pooled hosting or a white-label offering.

These exclusions limit the first implementation, not the user's choice of appliance category. A fixed-wired or three-phase load may be analysed through compatible, correctly scoped imported energy data. This does not declare the selected plug meter suitable for it or require a new industrial meter integration in v1.

## 5. Shared domain and measurement boundaries

### 5.1 Records and responsibilities

| Record | Required meaning |
|---|---|
| User/session | Owner identity; authenticated, revocable access to saved data |
| Site | Owner, name, context preset, timezone, currency; initial default Asia/Jakarta and IDR |
| Asset | Stable ID, site, user name, optional category/location, scope kind, optional declared parent, optional expected-use profile |
| Measurement source/channel | Meter channel or imported series; units, interval semantics, origin, cadence, quality and integration status |
| Source binding | Source → asset with effective dates; one authoritative energy source per asset per instant |
| Measurement | Source identity, measurement time/interval, received time, value/unit, quality, provenance and revision |
| Aggregation selection | An explicit set of non-overlapping assets whose readings can be summed |
| Expected-use schedule | Site default or asset override; timezone, weekly windows, effective date |
| Tariff | Optional IDR/kWh, effective time and provenance; single flat rate at each instant |
| Output metric/input | Optional selected asset scope, unit, denominator method, quantity and exact period |
| Insight | Observation type, evidence snapshot, version, limitations, status and feedback |
| Import | Validation preview, source mapping, errors, accepted/skipped/conflicting row counts and commit result |

An asset can represent `device`, `group`, `circuit`, or `site_total`. A name is not an ID. Two assets may share a name; import preview must distinguish or resolve them explicitly. A category is not a sensor capability or verified equipment identity.

Location labels such as “Dapur” or “Area produksi” organize assets. They are not additional metered readings. A derived group may sum disjoint members but cannot create a second copy of their energy in the site total.

A declared containment relation must stay within the same site and cannot contain a cycle or self-reference. Unknown physical overlap is a distinct unresolved state, not permission to assume disjoint loads. A simple parent relation and a confirmed disjoint selection are enough for v1; a full electrical-topology editor is deferred.

### 5.2 No double counting

Every summary includes `aggregation_scope`, included assets, excluded assets with reasons, and data coverage. Enforce these rules before showing a combined total or contribution chart:

1. Two alternative sources for the same asset and interval are replacements, never additive. A binding selects the authoritative source; unresolved overlap blocks those intervals from combined totals and shows a conflict.
2. A measured parent and its contained children cannot all belong to the same aggregation selection. Example: home main meter 10 kWh and measured refrigerator 1 kWh produce a 10 kWh main-meter view or a 1 kWh refrigerator view, never 11 kWh.
3. For unrelated meters, the user confirms that their measured loads are disjoint. If physical overlap is unknown, show individual values and request clarification; do not silently sum them.
4. When a whole-site meter is selected, child details may remain visible separately. Child percentages use the parent only when intervals, boundaries, and coverage are comparable. Unmeasured remainder is not a named appliance or proof of waste.
5. Do not silently switch from a main meter to child meters when the main meter becomes stale. Keep the selected scope and its quality state until the user changes it.
6. Do not add phase-total energy to the sum of the same meter's individual phases. An adapter must declare whether a channel is a total or a component.

For a simple installation with one non-overlapping source per asset, the summary is the sum of those assets. Complex hierarchy editing is not required: the minimum UI is a clear scope selection and overlap warning, with advanced uncertain aggregations refused.

## 6. Asset categories, expected use, and hardware support

### 6.1 Categories remain open

Optional examples: refrigeration, lighting, electronics/IT, pumping, heating/cooking, motors/process equipment, cooling/ventilation, other. Users can keep a custom label or “Lainnya”. Do not route all unknown assets into AC logic. No required brand, category, rated-power value, room sensor, schedule, or production input is part of basic CSV onboarding.

### 6.2 Expected-use profiles

| Profile | Examples, not automatic assignments | Permitted interpretation |
|---|---|---|
| Unknown | Unclassified imported circuit | Totals, quality, matched trends; no expected-hours claim |
| Continuous expected | Refrigerator, router, server, required process cooling | Changes may be observed; continuous use itself is not waste |
| Scheduled | Shop lighting, selected process machine | Compare against explicit windows; off-schedule is an observation |
| Intermittent/cycle | Pump, press, oven, TV | Period energy; no OFF conclusion from a low sample or gap |

The user chooses a profile or keeps unknown. Categories may suggest an explanation but cannot silently assign behaviour. An explicit per-asset “continuous expected” choice overrides the site schedule for that asset. A custom schedule becomes effective only after confirmation. Explanations must say which schedule/profile was used.

### 6.3 Source capability contract

Shelly Plug PM Gen3 and TP-Link devices are candidate measurement adapters, not verified integrations or proof of household/industrial compatibility. A candidate must remain labelled planned or unsupported until implemented and verified for the specific model and capability. The demo and CSV path must not depend on either provider.

Catalog entries declare supported measurement kind, units, cadence, channel scope, and validation status. Show “Terhubung” only after authenticated source enrollment and a valid first reading. A connected meter still does not establish that a particular load is electrically suitable. Installation requirements and actual vendor specifications must be checked for the chosen model and load; fixed wiring requires appropriate qualified installation. Do not provide a DIY mains-rewiring flow.

No integration may advertise switching merely because the hardware includes a relay. No control endpoint is part of generic v1.

## 7. User journeys

| ID | Journey | Acceptance outcome |
|---|---|---|
| P01 | Welcome → Try demo → household demo | Useful data with no AC, schedule, production, tariff, or credentials required |
| P02 | Empty site → import CSV → review mapping and errors → confirm | Clear scope and totals; failed import preserves input and existing data |
| P03 | Beranda → period → largest contributor → history | At most 3 deliberate taps; values and scope reconcile |
| P04 | Saran → change observation → evidence | User can identify observed value, comparison, quality, and unknown cause |
| P05 | Settings → optional expected-use schedule → asset override | Overnight windows and continuous assets behave consistently |
| P06 | Optional output metric → unit and scope → denominator | A valid intensity appears; missing/invalid inputs never become zero |
| P07 | Add source → brand/model → connection → asset binding | Verified first reading; retry does not create duplicate assets or bindings |
| P08 | No tariff, missing data, stale source, or offline client → recovery | Last known values labelled honestly; retry preserves drafts |
| P09 | Two sources or parent/child meters → resolve scope | Conflict is visible and no double-counted total is shown |
| P10 | Insight feedback → snooze/hide → restore | Feedback persists, never deletes measurements or sends a hardware action |
| P11 | Household preset → industry or unspecified | Existing measurements and optional settings remain intact; only examples change |

Continue without data opens empty Home without creating a server workspace. Settings holds optional usage context. The MVP uses a compact layout with a supporting column on populated screens from 768 logical pixels and single-column forms. Indonesian remains the default. The English selector becomes available when all MVP flows, accessibility labels, and recovery copy are ready. Changing language preserves the current context and never dispatches or retries a server mutation or re-evaluates Insights.

P01–P04, P08–P10 must be complete with schedule and output metric absent. Industry must also be usable without output data. No persona is forced to fill an inapplicable field.

## 8. Information architecture and screen contract

Three persistent labelled tabs: **Beranda**, **Perangkat**, **Saran**. “Perangkat” includes metered groups and circuits, with a visible scope label. Settings, import, and tester scenarios are secondary. Native detail screens use a stack; web may use a side navigation with the same three destinations.

| ID | Screen | Content and working actions |
|---|---|---|
| S01 | Welcome | Short value statement, primary Try demo, secondary Continue without data, language selector once bilingual coverage ships |
| S02 | Empty Beranda | Lead with Try demo. Add data opens the CSV screen, where Choose file opens the picker. |
| S03 | Populated Beranda | Period, scope, kWh, optional estimated cost, coverage/freshness, contribution, one observation |
| S04 | Perangkat | Asset name, category/scope, energy, quality; add/import and open detail |
| S05 | Source setup | Provider → model → connection/first reading → name/scope/binding; drafts retained |
| S06 | Asset detail | History, source provenance, totals, quality, related insights; schedule/intensity only when applicable |
| S07 | Saran | Evidence-based list; learning/no-finding state; feedback and restore hidden |
| S08 | Insight detail | What changed, baseline periods, arithmetic, quality, limitations, general advice and feedback |
| S09 | Settings | Site name/context/timezone, tariff, optional schedule/output metric, notification choice |
| S10 | Import | File/paste, example, units/timezone/interval confirmation, scope mapping, preview, commit/retry |
| S11 | Scope/source resolution | Parent/child or duplicate-source explanation; choose a valid non-overlapping view |
| S12 | Optional metric setup | Select numerator assets, unit, denominator method/period; preview and disable |

Default heading: “Energi yang dipantau”; cost heading: “Estimasi biaya energi terpantau”. “Total tagihan” is never a synonym for measured energy cost, including when a main meter is present. Output metrics stay outside Beranda until explicitly enabled with valid data. Household screens must not contain permanent empty “produksi” cards.

## 9. Functional requirements

### FR-01 Demo and saved accounts

Demo runs without credentials, hardware, push permissions, or paid services and carries “Demo · Data simulasi”. It is isolated from user imports and saved live data; reset affects only demo state. Saved server resources require login, short-lived access credentials, revocable refresh sessions, secure native secret storage and appropriate web session protection. A demo is not evidence that server authentication exists.

### FR-02 Site and neutral context

Create one owned site with a visible timezone. Context is optional and independent of data. All resource access is scoped to the owner/site. A timezone change requires confirmation and recalculates local-day boundaries and comparisons; imported naive timestamps retain their original interpretation, and the change does not rewrite stored UTC instants.

### FR-03 Assets and bindings

Create, rename, categorize and archive arbitrary assets. Preserve stable IDs and historical bindings. Removal of a source binding stops future association and retains history. Archiving is reversible; permanent data deletion is a separate explicit action. Source replacement uses an effective time and never splices old and new streams without provenance.

### FR-04 Catalog and enrollment

Show implemented versus planned adapters. Enrollment is expiring and single-use, verifies source identity server-side, and requires a valid first reading. Retry is idempotent. A provider error uses actionable text in the selected language and preserves setup input. Unsupported models return to the catalog without fake success.

### FR-05 Data ingestion

Normalize supported measurements into the contract in section 10. Preserve raw provenance, captured/received times, units, interval/counter semantics, missingness and quality. Handle duplicate delivery, late readings and counter resets. Invalid telemetry is rejected or quarantined with diagnostics; never converted into a valid zero measurement.

### FR-06 CSV import and preview

Support the accepted CSV aliases and canonical format in section 10. Parse, map, validate and preview before commit. Report accepted, skipped, exact duplicate and conflicting rows separately. Import commit is atomic and retry-safe. No bad upload can erase earlier data. All row/size limits, timezone and inferred cadence assumptions are visible before confirmation; details are in section 10.

### FR-07 Energy and history

Provide today/this-week selection and an explicit date range in history. Derive summaries and chart buckets from the same accepted intervals, selection and timezone. Retain full precision internally; round display values only. Missing buckets are gaps; measured zero is a real value. A current incomplete day/week is compared with an equivalent elapsed period.

### FR-08 Estimated cost

Tariff is optional, non-negative, effective-dated IDR/kWh. Use decimal arithmetic and section 11's formula. No tariff means unknown cost, not Rp0. An explicitly entered zero tariff is a valid free-energy estimate, visibly sourced. Explain that taxes, demand/reactive charges and bill components are excluded. A change effective now does not rewrite old costs; a confirmed retroactive correction recomputes affected periods with an audit entry.

### FR-09 Contribution and scope

Rank measured assets only within a valid non-overlapping selection. State selection, exclusions and coverage. For a zero measured total, show no percentage distribution. Preserve an explicit parent view versus child view. Resolve ambiguous overlap before aggregation; never imply that all electrical loads have been captured merely because all enrolled assets are listed.

### FR-10 Optional expected-use schedules

Support site defaults, per-asset override, weekly days, multiple time windows and overnight windows. Schedule is skippable and disabled by default. No schedule means the outside-window metric is unavailable, not zero or 24 hours of waste. Validate, preview and save schedules atomically; details and boundary semantics are in section 11.

### FR-11 Optional output-normalized energy

Enable only on user request. Require a numerator asset selection, explicit denominator unit, exact period, and actual output quantity or a clearly labelled average estimate. Household users never need a denominator. “IKE” is explained as energy per the selected output unit, not a universal benchmark. Section 11 defines denominator validity and matching rules.

### FR-12 Baseline, readiness, and quality gates

Use the same engine for every context. Store baseline windows, readiness, coverage and version separately from tariff. Schedule or output changes invalidate incompatible comparisons. Basic measured totals remain useful during learning. No “normal” verdict may be inferred merely because the baseline is missing or the comparison was suppressed.

### FR-13 Evidence-based insights

Support measured contribution, matched energy change, optional outside-window change and optional intensity change. Every generated insight retains an evidence snapshot and limitations. Thresholds and suppression rules are in section 12. General guidance is explicitly labelled and never substitutes for personalized evidence.

### FR-14 Feedback and notifications

Useful, not relevant, snooze until next local day, hide and restore are optional. Scope feedback to the insight and owner. Suppress repeat notifications for the same observation revision; preserve feedback across equivalent recomputations. In-app Saran is required; push is optional and off until consent. Gateway acceptance is not delivery proof. No response or dismissed feedback can trigger an actuator.

### FR-15 Consistent state and offline reading

One domain state drives summaries, charts, counts and evidence. Refresh on foreground and user request; the phone is not the permanent collector. Cached data includes timestamp, scope and quality. Offline v1 allows reading cached data and retaining drafts; mutating operations wait for an online, confirmed save rather than silently claiming success or attempting complex offline merge.

### FR-16 Data rights and retention

Provide export of accepted measurements with units, intervals, UTC times, original timezone/provenance and scope metadata. Explain archive versus deletion. Confirm permanent deletion and document retention/backup expiry before a live release; deferred purge status is visible. Avoid exporting session or meter credentials. Exported CSV text must be safe to open in spreadsheet software without formula execution.

### FR-17 Demo and repeatability

Provide separate household and industrial scenario entries, plus empty, no-tariff, partial, stale, import-error, source-overlap and reset scenarios. One shared virtual clock makes charts and evidence reproducible. Ordinary product screens do not display tester jargon or debug payloads. Section 19 defines exact fixture oracles.

### FR-18 Error recovery

Back, retry, file parsing errors, lost connection and expired login preserve non-secret drafts and the last confirmed state. Roll back a failed optimistic setting save. API validation never accepts invalid settings just because the UI validated them. Errors distinguish unavailable data from rejected input and offer a meaningful next action.

### FR-19 Audit and recomputation

Imports, binding changes, tariff changes, scope changes and optional metric changes record who, when and affected intervals without secrets. Late data or corrected settings recompute affected aggregates idempotently. Preserve the evidence version of an already viewed insight and mark superseded observations; do not silently rewrite the evidence behind feedback.

### FR-20 Read-only capability enforcement

Neither the client nor the server exposes machine-control routes, actuator credentials, relay commands, AC-specific setup, or IR integrations. Adapter credentials must be measurement-scoped where supported. Tests inspect UI actions and API surface for this contract; a generic label on an AC-control product does not satisfy this PRD.

### FR-21 Bounded reusable product composition

Implement the shared measurement, scope, quality and evidence core once. Cost, expected-use schedules and output/intensity are ordinary optional capability modules with explicit prerequisites; CSV, verified vendors/protocols, persistence and delivery use adapters that call the same application use cases. A small versioned, validated composition specification selects supported capabilities, adapters and policy versions, separately from brand/copy, user context and server authorization. Reject unsupported combinations. Configuration cannot disable correctness/security invariants, grant access, introduce executable client rules or create a customer-specific calculation fork. The backend checks capability availability and prerequisites on API and worker paths; hiding a screen is insufficient. Demo/CSV and the three-tab core remain usable with tariff, schedule, output, live broker and hardware absent.

### FR-22 Shared releases and client delivery

Keep one maintained source release and reproducible builds for each supported product composition. Record release, composition schema/version, selected modules/adapters, policy versions and applied migrations per deployment. An isolated client deployment uses the same source with separate data/storage/secrets/access boundaries when needed; it does not require a source fork or tenant provisioning. Fix shared defects once, add relevant regression proof, verify every supported composition's critical journey plus affected adapter/migration contracts, then roll out with health checks and rollback/recovery instructions. Publishing a release does not automatically upgrade installations. Track rollout status and agree a supported upgrade window before ongoing client operation; exact support duration is an operating decision. Distinct branding or native identifiers may require different client artifacts from the same source release.

## 10. Measurement and import contracts

### 10.1 Canonical measurement

Required normalized fields: `schema_version`, `site_id`, `asset_id`, `source_id`, `source_record_id`, `measurement_kind`, `origin`, `received_at`, `quality`, and the appropriate measured value/time fields below. Owner/site identity comes from authenticated authorization and server mapping, never from a trusted payload claim.

| Kind | Value and time | Meaning and restrictions |
|---|---|---|
| `interval_energy` | `energy_wh`, `interval_start`, `interval_end` | Non-negative consumption within `[start, end)` |
| `average_power` | `average_power_w`, same interval | Average over the declared interval; convertible to energy |
| `cumulative_energy` | `cumulative_wh`, `measured_at`, counter/segment identity | Counter reading; energy requires a second valid reading in the same segment |
| `instant_power` | `power_w`, `measured_at` | Point observation; not automatically an average or energy interval |

`origin` is one of `live`, `import`, `dataset_replay`, `simulated`. Import is not relabelled live just because the user says it came from a real meter. Record source provenance separately if known. Optional voltage/current values do not establish power factor or permit invented kWh.

Example normalized interval, illustrative and independent of any vendor payload:

```json
{
  "schema_version": 1,
  "site_id": "site-demo-home",
  "asset_id": "asset-router",
  "source_id": "source-demo-router",
  "source_record_id": "router-20261020T0000",
  "measurement_kind": "interval_energy",
  "interval_start": "2026-10-19T17:00:00Z",
  "interval_end": "2026-10-19T18:00:00Z",
  "energy_wh": "10",
  "origin": "simulated",
  "quality": ["valid"],
  "received_at": "2026-10-19T18:00:01Z"
}
```

Store UTC instants and the original import timezone/offset assumptions. Reject invalid dates and non-finite numbers. Preserve measurement resolution where known. Input strings representing decimals are parsed with decimal semantics; API representations must not encourage binary floating-point money arithmetic.

### 10.2 CSV formats and backward compatibility

Accepted minimal timestamp-only input:

```csv
timestamp,perangkat,energi_wh
2026-10-20 00:00,Router,10
2026-10-20 01:00,Router,10
```

Neutral explicit-interval input:

```csv
interval_start,interval_end,asset,energy_wh
2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Router,10
2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Kulkas,50
```

Accept these case-insensitive aliases: timestamp = `timestamp`, `waktu`, `tanggal`, `datetime`, `time`; asset = `asset`, `perangkat`, `mesin`, `device`, `nama`, `alat`; interval Wh = `energy_wh`, `energi_wh`, `wh`, `energi`; average W = `average_power_w`, `daya_w`, `watt`, `daya`, `power_w`. The `power_w` alias is accepted as an interval average only after the preview explicitly confirms that meaning. A sparse instantaneous-power file must not be silently integrated.

Explicit start/end headers are required for irregular interval-energy or average-power input. A distinct `cumulative_wh` column with point timestamps selects the counter path with its reset rules; the `energi` alias means interval Wh, never automatically a cumulative counter. If multiple competing value columns exist, preview asks for one measurement kind and column. Do not sum energy and its equivalent power-derived energy.

Import algorithm and UI contract:

1. Accept UTF-8 CSV with optional BOM, comma or semicolon delimiter, quoted fields and line endings from common systems. Decimal comma is accepted in a quoted value or semicolon-delimited file. Reject ambiguous delimiter/number combinations with an example.
2. Enforce proposed limits of 10 MiB upload size and 150,000 data rows before commit. Report which limit failed; upload limits and parsing timeouts also apply server-side.
3. Show column mapping, units, source binding, timezone and expected measurement interval. Required values cannot be inferred from the asset category.
4. Offset timestamps retain their explicit instant. Naive timestamps use the site's timezone only after the user confirms the preview. Ambiguous/nonexistent local times require an offset or correction; impossible dates never roll into another date.
5. With explicit start/end, require end after start and no unresolvable overlap within a source. With timestamp-only interval-energy/average-power rows, infer cadence separately per asset/source from the median positive gap only when at least 90% of positive gaps agree within 1 second. Otherwise request an explicit interval or explicit start/end columns. One-row interval streams always require an interval. Counter rows remain point readings; their adjacent timestamps define candidate deltas and are not converted into assumed-cadence intervals.
6. The timestamp-only convention is interval start. After confirmation, each row covers exactly the declared cadence, including the final row; this is a labelled assumption, not a measured duration. A long gap between records never stretches the earlier row across the gap. Never infer across distinct assets or sources.
7. Missing name/time/value, non-finite or negative consumption, impossible time, and invalid interval are invalid rows. Up to and including 20% invalid rows permits a preview requiring explicit acceptance of the skipped-row result. More than 20%, no usable rows, unknown measurement meaning, or unresolved conflicting rows blocks commit. Structural and scope conflicts cannot be waived as ordinary skipped rows.
8. Count exact duplicate records separately from invalid rows; accept only one. Same source/interval with different values is a conflict to resolve before commit. Reimporting the identical file is idempotent. A different source overlapping a live binding requires explicit replace/skip mapping and cannot be added silently.
9. Limit asset names to 60 characters without truncating silently. Assign IDs explicitly when imported names collide with existing distinct assets; user confirmation selects reuse or creation.
10. Preview shows total data rows and counts that reconcile: accepted unique rows + invalid rows + exact duplicates + conflicting rows. Invalid percentage uses all nonblank data rows as denominator. Header and blank lines are excluded. Conflicting rows are blocked even if invalid percentage is low.
11. Commit accepted rows transactionally with an idempotency key; interruption returns a retryable import status. Result states rows added, skipped, duplicated, assets mapped/created and periods affected. Existing data remains intact after a rejected file or failed commit.

Keep pasted content or selected-file context on error. A large server upload may need reselection after a browser restart; say so rather than claiming a recovered file. Imported text and names are treated as data, never executed as HTML, code, or spreadsheet formulae.

### 10.3 Duplicate, reset, and late-data handling

- Prefer a stable source capture ID; otherwise use source, measurement kind and interval/time identity. Equal values in different intervals remain legitimate records.
- Same identity and same value is an idempotent repeat; a changed value is a revision/conflict with provenance, not a second reading.
- A cumulative counter's first reading establishes an anchor. A non-negative delta between valid adjacent readings in the same segment supplies interval energy. A confirmed reset starts a new segment; do not take absolute values or assume the reset value accounts for the whole interval.
- A gap beyond the source's declared valid-counter interval keeps the interval uncertain. Even if its counter delta is retained as measured energy across a long span, subperiod allocation and outside-window comparisons remain unavailable without finer evidence. Do not manufacture hourly detail.
- Late readings trigger bounded recomputation of affected intervals, costs and insights. Repeated ingestion or recomputation must not change an already correct total.
- Distinguish time coverage from measurement uncertainty: a long counter delta may establish a total while providing inadequate temporal resolution for schedule analysis.

## 11. Calculations and comparison rules

### 11.1 Energy, cost, and rounding

For accepted interval energy, `E_kWh = sum(energy_wh) / 1000` within the valid aggregation selection. For interval-average power, `E_Wh = average_power_w × duration_seconds / 3600`. Instantaneous W never becomes Wh by merely changing the unit label.

Cost for known flat tariffs is `C_IDR = sum(E_interval_kWh × tariff_effective_for_interval)`. If a tariff boundary falls inside an interval, split by overlap duration only under a stated uniform-rate assumption; flag the resulting allocation estimate. Where that assumption is inappropriate or not accepted, show that portion as unknown cost. A gap in tariff history leaves an incomplete cost total with its covered energy stated, not a zero-price interval. Negative tariff is invalid; explicit zero is valid.

Use decimal arithmetic for energy totals, tariffs and money. Keep unrounded totals as the calculation authority. Show kWh with sensible precision for small loads (up to three decimals when needed) and IDR rounded once for display. If rounded contributors do not sum visually, disclose rounding; never change the recorded energy to force equality. Never use a rounded display total as an exact cost oracle.

### 11.2 Period and interval boundaries

All queries use half-open UTC intervals `[start, end)`, derived from the site's local calendar; weeks start Monday. “Hari ini” ends at the shared current time, not a full future day. A historical data-only demo uses its declared virtual now. An imported historical file does not silently move a real user's clock: offer “Lihat periode data” when today is empty.

When a query/schedule boundary crosses a measured interval, proportional allocation is allowed only as a visible uniform-within-interval estimate. The allocated parts must sum exactly to the original interval. Preserve the source resolution; do not show minute-level evidence from hourly data as if minute readings existed. If allocation would materially mislead, show a coarser view or suppress the affected insight.

### 11.3 Coverage and freshness

`temporal_coverage = duration of union(valid measured intervals within requested window) / requested-window duration`. Count overlapping time only once. Exclude invalid intervals and gaps. A sampled instantaneous power point does not provide an energy interval. For counter data, report energy-span validity and temporal granularity separately; a measured total does not prove intrainterval timing.

For a combined scope, show each contributor's coverage and the minimum contributor coverage as the conservative summary coverage. Also expose the window where all selected contributors have valid concurrent data. Do not average a missing high-consumption asset away. A new source covers only its actual start onward; requesting a whole week still reveals the unmeasured earlier period.

Proposed defaults: a live stream becomes stale after more than 2 expected sample intervals; a coverage banner appears below 90%. These are explicit engineering defaults, validated during pilots, not universal equipment tolerances. Historical imports show their range and latest data time with “Data historis”; they are not treated as live sources that have failed to transmit. Client offline status is separate from source staleness.

### 11.4 Expected-use windows

Weekly windows are local-time ranges attached to a starting weekday. Support more than one window per day. Example: Monday 22.00–Tuesday 06.00 is one overnight window anchored on Monday. Use an explicit next-day end flag; equal start/end is invalid unless the user chooses the separate 24-hour option. Merge overlapping windows for arithmetic; never count shared minutes twice.

For an asset, effective expected use is: explicit continuous-expected override → explicit asset schedule → site schedule → unspecified. An explicit “no schedule for this asset” disables inheritance. Preserve the difference between inheriting, disabling, continuous expected, and a custom schedule.

Compute `outside_energy = sum(interval energy × fraction outside union(expected windows))`, and `inside_energy = measured energy − outside_energy`. Fractions are overlap-duration estimates when the interval crosses a boundary. All-day continuous expectation has no outside-use finding. An unspecified schedule leaves the split unavailable. Outside-window electricity is not automatically avoidable energy.

Validate all weekdays, durations and timezone transitions; label the effective schedule/version. Changes default to effective now. The user may explicitly apply a corrected schedule to historical data; recompute with the corrected definition and disclose it. Baseline comparisons must use one equivalent schedule definition or be withheld until compatible periods exist. V1 excludes holiday calendars and arbitrary shift rotation; users may disable comparisons for a known exceptional period.

### 11.5 Optional output/intensity

The user selects the measured numerator scope and denominator meaning. Units may be units produced, batches, kg of product, or another user-defined output; an optional floor-area denominator uses kWh/m² for its stated period and must never be mixed with production output. There is no mandatory household metric and no inferred denominator from sector selection.

Required inputs: metric name, unit, numerator assets, period and method. With actual output, `intensity = measured_energy_kWh_for_period / positive_output_quantity_for_same_period`. Zero output produces “Tidak dapat dihitung: keluaran nol”; missing, negative, non-finite or mismatched-period output does not produce zero, infinity or an interpolated quantity. Different products/units cannot be combined without a user-declared common denominator; v1 does not calculate conversions.

The average-output estimate is explicit: `estimated_output = average_output_per_output_day × eligible_output_days`. For a partial day, require the user to confirm uniform output over declared output windows before using the elapsed fraction of those windows. Without windows or that confirmation, compute only complete eligible days, or request actual output for the elapsed period. Do not prorate production merely because the calendar day is partly over. Batch output is never assumed uniform by default.

Estimated denominators label the result “Estimasi energi per …” and expose the assumption. Missing energy makes intensity provisional recorded-energy-per-output, with missing coverage visible; personalized efficiency-change claims require complete numerator periods and compatible denominators. For actual production comparisons, require the same product/output meaning, units, source scope and full corresponding periods. For area metrics require the same period length/elapsed window. Reset the comparison when these change. A lower ratio is an observation, not proof of realized savings or better equipment efficiency.

### 11.6 Matched baseline

For an eligible current window, consider the same local weekday/time window in each of the previous three weeks. Compare the same asset or unchanged aggregation selection, using equivalent elapsed duration, schedule definition and valid measurement kinds. Use at least two eligible historical windows; otherwise show “Sedang mempelajari pola”.

Each candidate and current window must have at least 90% temporal coverage. For an energy-change insight, compare the **common valid time mask** across current and chosen historical windows, aligned by local weekday/time. That common mask must still cover at least 90% of the requested elapsed window; otherwise suppress the change insight. Sum energy on that same mask, show mask coverage, and retain full recorded totals separately. Never compare a partial current total to a full historical total as if they had equal support.

`B = median(eligible historical energies on common mask)`. Store every baseline window, energy, coverage and the common-mask definition. For a zero baseline, show absolute change only; percentage is unavailable. If baseline or scope changes after correction, create an insight revision. “No eligible change detected” differs from “comparison unavailable”.

## 12. Insight policy and explanation contract

### 12.1 Allowed insight types

| Type | Prerequisites | Required wording/limits |
|---|---|---|
| Contribution | Valid non-overlapping selection and recorded energy | “Kontributor terbesar di antara perangkat yang dipantau”; no invented unmeasured appliances |
| Energy change | Matched baseline, common support, eligible resolution | State current/reference kWh, absolute and eligible relative change |
| Outside-window change | Explicit applicable schedule plus matched baseline | “Pemakaian di luar jadwal”; never automatically “pemborosan” |
| Intensity change | Enabled valid metric and complete compatible periods | State unit, denominator method, quantities and limitations |
| Data-quality notice | Missing/stale/conflicting data | Explain data limitation; do not present it as a load diagnosis |

Continuous/critical loads may receive consumption-change observations. Their advice must never recommend interruption simply because they run continuously. Cooling, heating, refrigeration, pumping, IT and unknown/group loads follow the same evidence rules. No universal “three reminders then OFF” rule exists.

### 12.2 Scale-aware change rule

Do not impose an absolute 3 kWh threshold on all assets. Proposed deterministic first-release increase policy:

- Use the common-mask current value `C`, baseline `B` and historical median absolute deviation `MAD = median(abs(historical_value − B))`.
- Let `r` be the larger of the current or historical window's sum of source interval energy resolutions, in kWh, over that same mask. This conservative floor prevents precision noise from being called a meaningful change. An average-power adapter supplies its propagated energy resolution. If resolution is unknown, show a descriptive comparison but suppress an automatic personalized change alert pending calibration.
- An increase qualifies only if `C − B > 0` and `C − B >= max(0.30 × B, 3 × MAD, 5 × r)`, and all readiness, quality, scope and schedule gates pass. The values 30%, 3 and 5 are proposed engineering policy constants, not validated detection accuracy or a user-facing threshold editor.
- When `B = 0`, require positive absolute change meeting the other floors; show no percentage. A decrease can be described with symmetric absolute/relative evidence after the same gates, without calling it verified savings.
- For intensity, use the equivalent rule in the metric's units, propagating measurement resolution through the compatible denominator. No rule may compare kWh/unit to kWh/kg or merge estimated and actual methods silently.

Fixtures must exercise both small household and larger industrial changes with this same rule. Calibrate sensitivity with both contexts before a live pilot; if calibration is unresolved, measured facts and non-alert descriptive comparisons still work. No expensive model is needed to deliver core value.

### 12.3 Evidence and ranking

Every personalized insight includes: asset/scope; observation period; observed value and unit; historical values and median; absolute change; relative change or why unavailable; schedule/denominator if used; current, baseline and common-mask coverage; source origin/resolution; calculation version; generated time; “Yang belum diketahui”; optional labelled “Saran umum”. Optional cost differences use an explicitly stated common tariff assumption, so a rate change is not misrepresented as consumption change.

Example household: “TV memakai 0,56 kWh pada periode pembanding yang sama, sebelumnya median 0,36 kWh. Penyebab perubahan belum diketahui.” Example industry: “Energi kompresor di luar jadwal meningkat; periksa apakah ada kegiatan yang memang memerlukan pemakaian tersebut.” Numbers must come from the evidence snapshot, not prose generation.

Rank blocking data-quality notices separately from consumption insights. Within eligible observations, rank by absolute additional kWh, then recency with a stable ID tie-breaker; show contribution even during learning if its scope is valid. Do not manufacture an alert to fill Saran. Fewer observations with clear limits are acceptable.

Statistics and deterministic explanations are sufficient. A future model must beat this baseline on chronological held-out data, evaluated separately by context and without train/test leakage. An LLM may not invent arithmetic, readings, diagnoses or autonomous physical actions.

## 13. State and recovery matrix

| State | What remains visible | Required action/recovery |
|---|---|---|
| No data | Explanation, no fake zero | Import, demo, or supported-source setup |
| Known zero | Valid 0 kWh with coverage | No divide-by-zero contribution or baseline percentage |
| Learning | Measured totals/contribution | Explain insufficient comparable history |
| No tariff | kWh/history/eligible energy insights | Optional add tariff; no Rp0 |
| No schedule | Core data | No outside-window value or warning; optional setup only |
| No output metric | Core data | No production card or requirement |
| Partial data | Recorded totals labelled incomplete, gaps, per-asset coverage | Retry or inspect source; suppress incompatible comparisons |
| Live source stale | Last reading and timestamp | Inspect source/retry; no “perangkat mati” claim |
| Historical import | Its exact range and latest record | “Lihat periode data”; do not label offline live meter |
| Client offline | Cached confirmed values and age | Reconnect/retry; drafts retained |
| Unsupported adapter | Catalog capability explanation | Return without losing asset draft |
| Invalid CSV | Row/header/time/units explanation and preview | Correct/reselect; existing readings unchanged |
| Conflicting source/scope | Individual values with warning | Resolve source/selection before combined total |
| Rejected optional setting | Last confirmed settings, unsaved draft | Correct/retry or cancel without recomputation mismatch |
| Expired session | Non-secret draft | Login and explicitly retry; no duplicate commit |
| No qualifying observations | Honest empty Saran | Show history or useful general guidance, not fake warnings |

These states are independent flags. A site can simultaneously be learning, without a tariff, and partially measured. One generic “error” state cannot erase those distinctions.

## 14. UI, accessibility, and content acceptance

| ID | Required check |
|---|---|
| UX-01 | Exactly three primary destinations labeled in the selected language and selected state independent of colour |
| UX-02 | One obvious primary action per task screen; optional setup has a visible skip/cancel path |
| UX-03 | Neutral default labels: Perangkat, Lokasi, Energi; no mandatory factory, AC, occupancy or production wording |
| UX-04 | Largest contributor and featured evidence reachable within 3 deliberate taps from populated Beranda |
| UX-05 | Back/retry retains form input, selected period, scope and navigation context |
| UX-06 | Source origin, estimation, freshness and coverage visible where they change interpretation |
| UX-07 | Internal minimum 48×48 logical-unit mobile hit areas, measured in each runtime; web mobile controls use 48×48 CSS px, Android uses 48×48 dp, iOS uses declared point/logical units. Normal text contrast ≥4.5:1 and required non-text control/chart information ≥3:1, with applicable WCAG exceptions; verify actual states |
| UX-08 | Text resized to 200% without lost content/function; long Indonesian names wrap; controls expose meaningful names in the selected language, roles, selected states and values; charts have a readable summary and structured data alternative |
| UX-09 | Verify 320 CSS px web reflow, plus 360, 390, 430, 768, 1280 and 1440 CSS px responsive widths; small-height phone, safe areas and keyboard avoidance. No horizontal page scrolling or lost controls; use stacked data rows where needed. Record text resize and reflow separately |
| UX-10 | Complete web tasks by keyboard without a trap; visible logical focus remains unobscured, overlays manage focus, Escape dismisses sheets and focus returns to the invoking action; announce save/import status to assistive technology |
| UX-11 | Loading/pressed/saving/error states for every primary action; failed save never looks confirmed |
| UX-12 | No AC controller, mandatory schedule, mandatory output data, forced push permission, or sector-dependent core navigation |
| UX-13 | Gap, unknown value, measured zero and incomplete total have distinguishable presentation |
| UX-14 | Same units, totals and evidence on every screen; reduced-motion preference respected |
| UX-15 | Schedule preview explains overnight start/end and inheritance; metric preview shows numerator and denominator |
| UX-16 | Household and industry participants each receive tasks using their own familiar examples; results reported separately |
| UX-17 | Beranda reading order: period and measurement scope → recorded kWh → qualified optional cost → completeness/freshness → largest contributors → eligible observation. Keep meaning-changing qualifications visible; reveal comparison, calculation and provenance progressively through clearly labelled detail actions |
| UX-18 | Contributor ranking uses directly labelled horizontal bars/list with a shared zero baseline; comparison graphics use aligned periods and comparable scales. Every chart has period, unit, scope, exact-value text/data alternative and quality; no hover, colour or precise dragging is required to answer the core task |
| UX-19 | Label physical measurement scope separately from temporal completeness, for example “Cakupan pengukuran: 4 perangkat” and “Kelengkapan data: 92% periode”. Annotate gaps with unavailable periods; measured zero, learning, no eligible change, stale source, historical import and client offline remain independently understandable, never “92% akurat” |
| UX-20 | CSV flow exposes file/paste → semantics/mapping → preview → explicit confirmation → result. Provide a focusable error summary linked to row/field details where actionable; consistent messages in the selected language state the correction and whether commit is blocked. Define data-row versus file-line numbering; retain input/mapping and confirmed data on back/error/retry |

Approved copy patterns: “Hanya mencakup sumber yang dipilih”; “Data belum diperbarui”; “Sebagian data belum tersedia”; “Tidak ada jadwal yang diatur”; “Estimasi ini tidak sama dengan tagihan listrik”; “Penyebab perubahan belum diketahui”. Do not shame users for continuous operation, skipped setup, rejected advice, or dismissed notifications.

### 14.1 Research rationale and standards boundary

These UX requirements are design decisions informed by published work and accessibility guidance, not findings from a HematDaya participant study. Qualitative household work found that monetary feedback depended on tariff credibility and that appliance-linked explanations helped interpretation; its context does not validate Indonesian households or industry. Therefore kWh remains the measurement authority, cost is qualified, and named measured contributors support investigation. Graphical-perception experiments support aligned position for quantity comparison; missing-data experiments show that presentation changes interpretation. They motivate direct labels, comparable scales and explicitly annotated gaps, without establishing one universally best chart or authorizing imputation. ([Hargreaves et al.](https://www.wren.uk.com/images/documents/publications/hargreaves_smart_meters.pdf); [Heer and Bostock](https://hci.stanford.edu/publications/2010/crowd-perception/heer-chi2010.pdf); [Song and Szafir](https://cmci.colorado.edu/visualab/papers/song_VIS_2018.pdf))

Progressive disclosure supports task-first complexity; it must not hide a limitation that changes the apparent meaning of a total. Recoverable validation follows the pattern of an error summary plus linked field messages. Chart summaries/data alternatives follow WAI guidance for complex graphics. These are adapted patterns, not evidence that the proposed navigation or import flow is already intuitive. ([NNGroup](https://www.nngroup.com/articles/progressive-disclosure/); [GOV.UK error summary](https://design-system.service.gov.uk/components/error-summary/); [WAI complex images](https://www.w3.org/WAI/tutorials/images/complex/))

WCAG 2.2 SC 2.5.8 defines a **24×24 CSS px AA target minimum with exceptions**; it does not define a 48-unit minimum. HematDaya deliberately uses the stricter internal 48-unit mobile target above, with runtime-specific measurements. Android recommends 48×48 dp. WCAG also supplies web criteria for 200% text resize, 320 CSS px reflow, contrast, keyboard/focus, error identification and programmatic status. Applying this selected checklist is not a full WCAG conformance audit or native certification. Check Android/TalkBack, iOS/VoiceOver and web separately; screenshots alone cannot prove focus or screen-reader behaviour. ([WCAG 2.2](https://www.w3.org/TR/WCAG22/); [Android accessibility](https://developer.android.com/guide/topics/ui/accessibility/apps))

## 15. Architecture and implementation boundary

### 15.1 Accepted modular-monolith decision

The accepted architecture is one backend domain application with explicit internal boundaries, an API entry point and an optional worker invoking the same use cases. PostgreSQL is the initial persistence target. The implementation target remains React Native + Expo + TypeScript with Expo Router for Android/iOS/web, FastAPI/Python for the backend, and Docker Compose for a pilot server. A verified MQTT adapter may use Mosquitto with TLS; neither the broker nor a separate worker is required for CSV/demo. These are accepted direction and implementation targets, not claims that components already exist or versions are verified.

```mermaid
flowchart TD
    CSV["CSV / historical input adapter"] --> USE["One backend application: shared use cases"]
    API["FastAPI: authenticated API entry"] --> USE
    LIVE["Optional verified vendor / protocol adapter"] --> USE
    WORKER["Optional worker entry"] --> USE
    USE --> CORE["Measurement, scope, quality and evidence core"]
    USE --> MOD["Optional cost / schedule / output capability modules"]
    MOD --> CORE
    CORE --> STORE["Persistence adapter"]
    STORE --> DB[("PostgreSQL")]
    APP["Expo app: Android, iOS, web"] <-->|HTTPS| API
    FIXTURE["Deterministic demo input"] --> USE
```

Related future electricity products extend concrete modules/adapters or validated composition. V1 implements boundaries needed by its actual CSV/demo and optional analyses; it does not build an arbitrary generic engine, plugin registry, microservices or one service per module. Cohesive components and ordinary function/service interfaces are sufficient. The accepted separation follows ports-and-adapters and modular-component guidance; a folder diagram alone does not enforce it. ([Cockburn](https://alistair.cockburn.us/hexagonal-architecture/); [Brown](https://simonbrown.je/modular-monolith/))

### 15.2 Responsibilities and invariants

| Boundary | Responsibility and constraint |
|---|---|
| Shared core | Site/asset/source identity and effective bindings; normalized measurement semantics; interval energy derivation; overlap-safe selection; period summaries; completeness/freshness; immutable or revisioned evidence. No context-specific arithmetic fork |
| Optional capability modules | Cost requires effective tariff; outside-window analysis requires an applicable schedule; output/intensity requires a compatible positive denominator and period. Consume canonical summaries and retain limitations; do not redefine energy, scope or authorization |
| Adapters | CSV and actual supported vendor/protocol mappings, PostgreSQL persistence, API/export delivery and worker invocation. Translate at the boundary; do not bypass core validation or add interfaces for hypothetical providers |
| Product composition | Bounded, schema-versioned supported capabilities/adapters and approved policy IDs/versions. Validate at startup/build or deployment; reject unsupported combinations |
| Presentation/context | Branding/copy and user-selected context/examples are separate from composition. The unspecified/household/business/industry preset keeps its narrow meaning in section 3 |
| Server authorization | Verified owner/resource permissions apply independently of brand, context and enabled capabilities. Configuration never grants access; every API/worker path enforces eligibility and permission |

Correctness and security invariants are unconditional: compatible units, explicit interval meaning, no missing-as-zero, no duplicate/double counting, valid counters, ownership, atomic imports and traceable evidence. Analysis policies are separate versioned, calibratable decisions: baseline selection, coverage readiness, the 30%/MAD/resolution rule and stale thresholds. Preserve section 11–12 defaults and record the policy identity/version on each finding. Updating a policy cannot disable an invariant; no end-user arbitrary rule editor is required.

The frontend consumes summaries/evidence rather than implementing a second contradictory live calculation authority. A standalone demo may use equivalent fixture calculations when the runtime differs; parity assertions must cover the exact server contract. Backend API and optional worker call the same domain use cases. The phone holds no vendor secrets, does not collect continuously, and never becomes the permanent ingestion process. Backend ingestion continues when the app closes.

### 15.3 Shared source, deployment and upgrades

Start from one repository and one maintained source release for app, backend, contracts, fixtures and supported composition specifications. A branded/native build may differ by identifier, assets or platform configuration while remaining reproducible from the recorded source release. Permanent per-client calculation branches, copied template cores and customer-name conditionals are not the reuse strategy. Extract a separately versioned package only when independent consumers need it; do not create a package platform in advance.

An isolated client deployment is supported as a delivery option when data or operating commitments require it: repeatable deployment definition, separate database/storage/secrets/access boundaries, and an inventory of release/composition/migration versions. **Site is a domain location, not a tenant.** V1's owner/site authorization does not claim pooled tenant isolation. White-label identity, shared code, SaaS delivery and tenancy are separate choices; no billing or self-service tenant provisioning follows from this decision.

For a shared fix, add relevant regression proof, run core and affected adapter contracts plus each supported composition's critical household/industrial journey, record migrations/restore implications, tag the source release, then stage and roll out with health checks and rollback. Track which deployments actually upgraded; a source publication is not an installation update. Before client operation, define a bounded support/upgrade window. These requirements adapt common-codebase and version-inventory guidance without imposing a fleet-management framework. ([Azure deployment/configuration](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/deployment-configuration); [Azure updates](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/updates))

### 15.4 Minimal runtime/design contract

The client needs a small read-only capability/deployment manifest, not a configurable UI engine: manifest schema version, source release, composition ID/version, enabled supported capabilities/adapters and their status, and policy IDs/versions. It contains no secrets or authorization grants. Use it to explain unavailable setup/analysis; the server remains authoritative for permission and per-request applicability. A disabled capability is rejected consistently server-side with an actionable reason, not accepted through a hidden route.

CSV/demo operation requires no broker, vendor account, cloud AI, push, tariff, schedule or output metric. Record exactly which native builds and web runs were exercised; a browser preview is not proof of Android/iOS execution. A future product with unrelated domain rules is a separate application, even if it reuses infrastructure patterns.

## 16. Proposed API contract

These are new generic API requirements, not claims about existing routes. All data routes are under `/api/v1`; identifiers are opaque; every read and mutation checks ownership. Path nesting does not itself establish authorization.

| Method and route | Responsibility |
|---|---|
| POST `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout` | Account/session lifecycle |
| GET/PATCH `/me` | Account metadata |
| POST `/sites`; GET/PATCH `/sites/{site_id}` | Initial owned site, context/timezone settings |
| GET `/capabilities` | Non-secret manifest in section 15.4; client explanation only, never an authorization grant |
| GET `/device-catalog` | Implemented/planned measurement adapters and capabilities |
| POST `/sites/{site_id}/enrollments`; GET `/enrollments/{id}` | Expiring, verified measurement setup |
| GET/POST `/sites/{site_id}/assets`; GET/PATCH `/assets/{id}` | Asset identity, scope, category, archive state |
| POST `/assets/{id}/bindings`; DELETE `/assets/{id}/bindings/{binding_id}` | Effective-dated measurement source assignment; retain history |
| GET/PUT `/sites/{site_id}/aggregation-selection` | Non-overlapping default summary scope |
| POST `/sites/{site_id}/imports/preview`; GET `/imports/{id}` | Parse and validate without committing readings |
| POST `/imports/{id}/commit` | Explicit, idempotent acceptance of resolved preview |
| GET `/sites/{site_id}/summary`; GET `/assets/{id}/summary` | Explicit start/end or period, timezone, selected scope |
| GET `/assets/{id}/measurements` | Bounded, paginated/downsampled history with gaps/provenance |
| GET/PUT `/sites/{site_id}/schedule`; GET/PUT `/assets/{id}/schedule` | Optional schedule and asset inheritance/override |
| GET/POST `/sites/{site_id}/tariffs` | Effective-dated flat rates and correction provenance |
| GET/PUT/DELETE `/sites/{site_id}/output-metric` | One optional initial metric, numerator selection and denominator definition |
| GET/PUT `/sites/{site_id}/output-inputs` | Actual-period quantity or explicitly estimated denominator input |
| GET `/sites/{site_id}/insights`; GET `/insights/{id}` | Evidence-bearing observations and revisions |
| POST `/insights/{id}/feedback` | Useful/not relevant/snooze/hide/restore |
| GET/PATCH `/notification-preferences`; POST/DELETE `/push-registrations` | Optional consent and registrations |
| POST `/sites/{site_id}/exports`; GET `/exports/{id}` | Owner-only, expiring measurement export |
| DELETE `/sites/{site_id}` | Explicit confirmed deletion request and purge status |
| GET `/health/live`, `/health/ready` | Process readiness, not meter health or physical load safety |

Enforce deployed capabilities and per-request prerequisites on optional analysis/setup routes as well as worker invocation. Reject disabled or unsupported capability use with a stable reason; owner checks still apply.

Summary response contract includes selected UTC/local window, timezone, source origins, asset selection/exclusions, unrounded recorded energy, display rounding policy, cost availability/covered energy, per-asset and combined quality, latest measurement time, schedule/metric applicability and revision. Unavailable values use `null` plus a reason such as `missing_tariff`, `no_schedule`, `no_output`, `insufficient_history`, `partial_coverage` or `scope_conflict`; never overload numeric zero as an error.

Validation errors contain a stable diagnostic code and actionable message in the selected language, with row/field details where appropriate. Source credentials, internal tracebacks and other users' resource existence are not returned. Bound all range queries and history pages; no endpoint returns unbounded raw years of samples.

UI-facing records use `asset`, not `machine`. If an integrating application already exposes `/machines` routes or equivalent machine-specific contracts, preserve supported callers through an explicit compatibility adapter and verified migration. Do not silently rename or remove a supported interface.

## 17. Security, privacy, and operational reliability

- Require HTTPS; use broker TLS, authenticated per-source identity and ACLs for live ingestion. Never accept a claimed `device_id` or `site_id` as authorization, expose meter ports through router forwarding, or put vendor credentials in mobile/web code.
- Apply owner checks to site, source, import preview/commit, raw history, feedback, export and deletion. Revoke sessions and source credentials independently. Server authorization also applies to nested records referenced in a valid request.
- Validate file size, row limits, timestamps, units, numeric finiteness, intervals and asset mappings at the server trust boundary. Rate-limit authentication, imports and exports; parse CSV as data.
- Keep personal routine and production patterns private. Collect only fields needed for monitoring. No continuous location permission, occupancy inference, ad tracking or cross-customer model training is required.
- Do not log tokens, passwords, broker credentials, raw personal CSV content, or sensitive asset names in routine telemetry. Log correlation IDs, counts, quality and failure categories instead.
- Back up saved data and configuration with a documented restore procedure. Before a pilot, perform a restore rehearsal and ensure restored aggregates reconcile against raw readings; a backup job's success message is not a restore test.
- Default measurement retention is until owner deletion; v1 has no hidden automatic expiry. Publish any operator storage limit before upload. Deletion revokes user-facing access immediately, purges active records within a proposed 30 days, and expires residual backups within a further proposed 30 days; disclose actual configured periods and test them before a live launch.
- Separate demo reset, archive, source unlinking and permanent deletion. Confirm destructive operations with the specific scope; unlinking or feedback must never delete readings.
- Keep import commits and recomputation idempotent. A crash between stages must recover to a known status without partial double-counted data. Quarantined readings remain excluded and diagnosable.
- Provide source health and processing-lag diagnostics without presenting an app health endpoint as evidence that a physical device is operating safely.

These are product requirements for data the user entrusts to the service, not a claim of regulatory certification or a substitute for an installation assessment.

## 18. Non-functional and operating targets

All numbers below are proposed acceptance targets to benchmark and revise with evidence.

| Area | Initial target / required evidence |
|---|---|
| Working site scale | Demonstrate one site with 20 sources and 90 days of one-minute intervals without unbounded client downloads |
| Summary response | p95 under 2 seconds on a documented pilot-size server and dataset; name hardware, concurrency, cold/warm state |
| Import | A file within 10 MiB and 150,000 rows completes validation/commit within 60 seconds on the benchmark server, or reports queued progress and a recoverable status |
| History | Return at most 1,000 plotted buckets per requested series by default; retain raw data and disclose aggregation |
| Calculation correctness | Exact decimal fixture totals; equivalent segmentation/replay order produces the same result |
| Ingestion freshness | Display actual capture/receive lag; approximately 60-second live cadence is an adapter target, not a requirement for hourly CSV |
| Failure recovery | Retry after timeout/crash does not duplicate imports, assets, bindings, cost or alerts |
| Accessibility | Complete UX-01–UX-20 checks with recorded tools/devices and failures |
| Privacy | No cross-owner data in acceptance tests; no real secrets in source/runbooks |
| Platform evidence | Name Android device/emulator, iOS device/simulator and web browsers actually tested; unsupported runtime checks stay not run |

Do not claim arbitrary industrial scale or service-level availability from these targets. Daily use must not require a background phone polling loop. Offline caching is for reading/drafts, with explicit online commits in v1.

## 19. Deterministic fixtures and arithmetic oracles

### 19.1 Fixture protocol

These are **specifications for fixtures to implement**. Fixture generators and tests must assert the exact values below from their generated readings. Simulated fixtures verify deterministic behaviour; they do not establish live integration, field accuracy or user outcomes.

Both main fixtures use Asia/Jakarta, hourly interval-start readings, one disjoint source per asset, resolution 1 Wh, integer Wh, origin `simulated`, and complete coverage. Range: September 28, 2026 00.00 through October 26, 2026 00.00 exclusive: 28 days × 24 hours × 4 assets = **2,688 data rows per fixture**. Explicitly emit valid zero intervals. Use virtual now October 26, 2026 00.00. Initial demo selection is the completed range “19–25 Oktober”, not a falsely populated “Minggu ini”.

Comparison window: October 19 00.00–October 26 00.00, against the equivalent three preceding complete weeks. In the variants below, “current” means this selected observation window, not the virtual clock's new calendar week. These fixed ranges avoid comparing a finished week against a partial current week. Today/this-week on the virtual Monday can correctly be empty; a separate partial-period scenario exercises current-period UI.

### 19.2 Household fixture H — no AC

| Asset | Exact daily hourly generation | Daily energy | Weekly energy |
|---|---|---:|---:|
| Kulkas | 50 Wh every hour | 1.200 kWh | 8.400 kWh |
| Router | 10 Wh every hour | 0.240 kWh | 1.680 kWh |
| Pompa Air | 150 Wh in each interval starting 06.00 and 18.00; zero otherwise | 0.300 kWh | 2.100 kWh |
| TV | 120 Wh in each interval starting 20.00, 21.00, 22.00; zero otherwise | 0.360 kWh | 2.520 kWh |
| **Total** | Sum of the four disjoint sources | **2.100 kWh** | **14.700 kWh** |

Tariff scenario uses an explicitly synthetic Rp1,500/kWh: daily Rp3,150; weekly **Rp22,050**. Four-week energy is **58.800 kWh**, estimated cost **Rp88,200**. Largest contributor is Kulkas, `8.4 / 14.7`, approximately 57.14%. Baseline and current energy are identical; no change alert is expected.

No site schedule or output metric is enabled. Kulkas and Router have explicit continuous-expected profiles. Their normal operation must not generate an off-hours warning or shutdown advice. Clear the tariff to verify that all core energy journeys still work.

Household change variant: add 200 Wh to the TV interval starting 19.00 on each of the seven current-week days only. Current TV energy becomes **3.920 kWh**, baseline **2.520 kWh**, absolute change **1.400 kWh**, relative change approximately **55.56%**. The 168 hourly intervals give `r = 0.168 kWh`, so the rule's floor is `max(0.756, 0, 0.840) = 0.840 kWh`; the change qualifies despite being below 3 kWh. Site current energy becomes **16.100 kWh**, estimated cost **Rp24,150**. No outside-window claim is possible without a schedule.

### 19.3 Industrial fixture I — no AC

Monday–Saturday are output days. On Sunday all four assets have recorded zero intervals. On each output day:

| Asset | Exact hourly generation on output days | Daily energy | Six-day week energy |
|---|---|---:|---:|
| Oven | 2,000 Wh per interval starting 08.00–13.00 inclusive | 12.000 kWh | 72.000 kWh |
| Kompresor | 1,000 Wh per interval starting 08.00–13.00 inclusive | 6.000 kWh | 36.000 kWh |
| Mesin Press | 1,000 Wh per interval starting 13.00–16.00 inclusive | 4.000 kWh | 24.000 kWh |
| Lampu Area | 200 Wh per interval starting 07.00–16.00 inclusive | 2.000 kWh | 12.000 kWh |
| **Total** | All other intervals recorded as zero | **24.000 kWh** | **144.000 kWh** |

Expected-use schedule: Monday–Saturday 07.00–17.00. Outside-window energy is exactly zero; Sunday zero is measured, not missing. Synthetic flat tariff Rp1,500/kWh yields **Rp36,000 per output day**, **Rp216,000 per week**, **576.000 kWh / Rp864,000 across four weeks**. Oven contributes 50% of weekly energy.

Optional actual output: 480 units per output day, 2,880 units per week; whole-fixture selection intensity is `144 / 2880 = 0.050 kWh/unit`. Disabling the metric removes it without breaking totals, rankings, trends or advice. No default production value exists outside this fixture.

Industrial outside-window variant: add 500 Wh to Kompresor at 18.00 on each of the six current-week output days. Current outside-window energy is **3.000 kWh**, baseline **0.000 kWh**; absolute change is shown, percentage unavailable. Current total is **147.000 kWh**, cost **Rp220,500**. The extra 3 kWh is an observation, not verified avoidable waste.

### 19.4 Boundary and recovery oracles

| Scenario | Exact expectation |
|---|---|
| Parent 10 kWh plus child 1 kWh | Valid parent selection 10; child selection 1; never 11 |
| Alternative source duplicates 2 kWh for same load/time | Resolve authority; never 4 kWh |
| Average power 100 W for 30 minutes | 50 Wh = 0.050 kWh |
| Single instantaneous 100 W sample | No implied interval energy |
| Counter readings 100 → 130 → 5 Wh with reset | First 30 Wh delta valid; reset interval unknown, not −125 or +125 Wh |
| Monday 22.00–Tuesday 06.00 schedule; 1 kWh per hourly interval during Monday 21.00–Tuesday 07.00 | 10 kWh total; 8 inside and 2 outside |
| One 60 Wh interval spanning 16.30–17.30, schedule ending 17.00 | 30 Wh inside, 30 outside, both labelled proportional estimates |
| Half of an asset's daily intervals missing | 50% coverage; recorded partial energy, no zero fill or matched change alert |
| 10 nonblank CSV data rows, 2 invalid | 20% invalid; preview may commit the 8 valid unique rows only after confirmation |
| Same row count, 3 invalid | 30% invalid; commit rejected, earlier data intact |
| 2 kWh; 1 kWh under Rp1,000 then 1 kWh under Rp2,000 | Rp3,000, not a retroactive Rp4,000 |
| Zero output with positive energy | No numeric intensity; explicit zero-output explanation |
| All readings zero with full coverage | Valid zero energy; no contributor percentages or division error |

## 20. Acceptance and verification matrix

**Initial execution status for every row: not run.** Document creation verifies the specification's internal structure and arithmetic only; these tests must be executed against a future generic implementation. Each result records runtime, fixture/input, expected/actual outcome and evidence. A simulated meter pass is labelled simulated, not live.

| ID | Scenario | Pass condition |
|---|---|---|
| AT-01 | Household demo without AC | P01–P04 and feedback work; no controller, production or schedule prerequisite |
| AT-02 | Industrial demo without AC | Same engine and navigation, correct I fixture, no mandatory output entry |
| AT-03 | Unspecified context | Neutral onboarding and complete CSV/core journeys |
| AT-04 | Switch context preset | Readings, source identity, tariff and optional inputs unchanged |
| AT-05 | Household H totals | Exact daily, week and four-week energy/cost oracles |
| AT-06 | Industrial I totals | Exact daily, week, four-week and optional intensity oracles |
| AT-07 | No tariff | Energy/history retained; cost unavailable, never implied free |
| AT-08 | Explicit zero tariff | Valid zero cost distinguished from missing tariff |
| AT-09 | Effective-dated tariff | Exact split-cost oracle; no silent rewriting of old prices |
| AT-10 | No schedule or output metric | Core screens useful; no mandatory empty factory cards |
| AT-11 | Continuous assets | No normal-operation waste or shutdown recommendation |
| AT-12 | Multiple schedule windows | Union of windows used; overlapping time not counted twice |
| AT-13 | Overnight weekly boundary | 8 kWh inside / 2 outside oracle; correct start-day anchoring |
| AT-14 | Asset schedule override | Continuous/custom/disable/inherit are distinct; displayed evidence names effective schedule |
| AT-15 | Interval crossing boundary | Energy conserved; uniform allocation disclosed |
| AT-16 | No valid baseline | Learning state; no fake “normal” conclusion |
| AT-17 | Household small change | H change variant qualifies at +1.4 kWh using shared rule |
| AT-18 | Industrial outside-window change | I variant +3 kWh, zero baseline and no percent/waste claim |
| AT-19 | Missing/unequal comparison coverage | Correct common mask or suppressed comparison; totals still labelled |
| AT-20 | Unknown resolution | Descriptive comparison allowed; automatic change alert withheld |
| AT-21 | Zero baseline and zero total | No infinity, NaN, divide-by-zero or arbitrary percent |
| AT-22 | Optional actual output | 0.050 kWh/unit oracle; period, units and scope explicit |
| AT-23 | Missing/zero/negative output | No invented intensity; actionable validation |
| AT-24 | Estimated partial output | No unconfirmed calendar-time prorating; labelled estimate only with valid windows/assumption |
| AT-25 | Incompatible output unit or product | Comparison withheld until compatible data exists |
| AT-26 | Timestamp-only and explicit-interval CSV | Correct aliases, mapping and preserved interval-Wh meaning |
| AT-27 | Power/counter semantics | Average power converted correctly; instantaneous and cumulative values not misread |
| AT-28 | Semicolon, quoted field, decimal comma, BOM | Parsed without altering values or asset names |
| AT-29 | Bad header/date/unit/non-finite/negative value | Actionable preview/error; no silent coercion or overwritten data |
| AT-30 | Invalid-row threshold | 2/10 may confirm skipped result; 3/10 rejected |
| AT-31 | Irregular cadence and one-row import | Explicit interval requested; missing gaps not integrated across |
| AT-32 | Row/byte/name limits | Client/server enforce limits without partial commit or silent name truncation |
| AT-33 | Duplicate/reimport | Exact repeats counted once; conflicting values require resolution |
| AT-34 | Interrupted import commit | Retry returns one committed result, no duplicate readings |
| AT-35 | Source overlap and rebinding | Authority/effective times explicit, history retained, no double counting |
| AT-36 | Parent/child or phase-total overlap | Exact no-double-counting oracles; ambiguous combination refused |
| AT-37 | Late readings/counter reset | Correct bounded recomputation, no negative/artificial energy |
| AT-38 | Partial/stale/offline/historical states | Independent labels; cached timestamp; no false device-OFF claim |
| AT-39 | Feedback/snooze/hide/restore | Persists and respects revisions; measurements intact; no actuator |
| AT-40 | Save failure/back/retry/session expiry | Draft and confirmed values retained; no success on failure |
| AT-41 | Another owner's identifiers | Denied on all reads/mutations/exports without data leakage |
| AT-42 | Enrollment and credentials | Identity verified, first reading required, no duplicate binding or client vendor secret |
| AT-43 | Demo reset/unlink/archive/delete | Actions affect only their declared scope; proper confirmation and retention behaviour |
| AT-44 | Text/CSV injection and export | Names rendered safely; spreadsheet export cannot execute untrusted text as formulae |
| AT-45 | Small mobile and large text | UX-01–UX-20 mobile checks pass with measured hit areas, 200% text, declared widths, safe areas and keyboard avoidance |
| AT-46 | Web keyboard and responsive views | 320 CSS px reflow, visible/unobscured focus, keyboard-only tasks, Escape/return focus, chart alternatives and programmatic status checks pass; record actual contrast and hit areas |
| AT-47 | Core-only installation | CSV/demo complete without broker, live meter, AI subscription or push |
| AT-48 | Platform status | Android, iOS and web runs individually evidenced or honestly not run |
| AT-49 | No physical-control path | UI, API and adapters contain no enabled actuation path |
| AT-50 | Restore and recomputation | Restored raw data reconciles; idempotent replay preserves totals |
| AT-51 | Timezone/date-range change | UTC data preserved; local boundaries and naive-import assumptions explicit |
| AT-52 | Per-segment usability | Household and industrial research reported separately; no invented participant results |
| AT-53 | Bounded composition and backend enforcement | Supported core-only/enabled compositions validate; unsupported combinations rejected. API/worker cannot bypass disabled capability, prerequisites, scope checks or ownership through changed config/context/brand; no invariant can be disabled |
| AT-54 | Shared release and isolated delivery | Two supported composition/build records use one source release and exact H/I oracles; affected adapter/regression checks documented. Isolated option has separate data/secrets/access; release/migration/rollout/rollback records identify deployed versions; no tenant claim inferred from Site |
| AT-55 | Plain hierarchy and progressive evidence | UX-17 holds in both fixtures: period/scope, kWh, qualified cost and quality interpretable before opening details; optional setup remains skippable and detail/back retains period/scope |
| AT-56 | Comparable and accessible charts | UX-18: ranking labels/scales and exact values reconcile; current/reference support matches; text/data alternatives answer the task by touch, keyboard and screen reader without hover/colour dependence |
| AT-57 | Scope, completeness and independent states | UX-19: selected equipment scope differs visibly from time completeness; gaps annotated rather than zero-filled; valid zero, learning, no finding, stale, historical and offline states combine without invented equipment status |
| AT-58 | Recoverable accessible CSV | UX-20: error summary focuses and links to actionable row/field errors with explicit numbering; valid/invalid/duplicate/conflict counts reconcile, 20% threshold obeyed, retry/back retains mapping and confirmed data; status is announced and no premature success occurs |

### 20.1 User-study protocol

Recruit five household users and five small-business/industrial users when available; do not infer household success from five factory operators. No participant needs electrical or MQTT expertise. Give neutral tasks, without naming the controls to press:

1. “Cari perangkat yang memakai energi paling besar pada periode ini.”
2. “Jelaskan apa saja yang termasuk dalam angka energi dan biaya di beranda.”
3. “Jelaskan arti saran ini dan apa yang belum bisa diketahui dari datanya.”
4. “Masukkan data dari berkas ini; lalu perbaiki berkas yang salah.”
5. “Lihat pemakaian tanpa tarif dan jelaskan mengapa biayanya belum ada.”
6. “Tunjukkan bagian waktu yang belum tersedia dan jelaskan bedanya dengan pemakaian nol.”
7. “Meter utama mencakup perangkat ini. Pilih tampilan yang dapat dijumlahkan dengan benar.”

Optional contextual task: business users set an overnight schedule; users who actually need output metrics enter a unit/quantity. Household participants must be able to finish without these tasks. Record completion, time, wrong turns, assistance, scope/quality misunderstanding and any unsafe interpretation. Report segment counts, failures and observations, not just averages. Record unaided success per task and across the entire core sequence, task time, assistance, wrong turns, scope/quality mistakes, runtime and assistive technology. Use neutral instructions and participants' own accessibility configurations where practical; a small formative round does not estimate population success. Accessibility review and participant comprehension are separate evidence. A missing study remains pending. ([GOV.UK moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing))

## 21. Delivery sequence and completion gates

| Stage | Deliverable | Gate before advancing |
|---|---|---|
| G0 — specification | Complete Indonesian/English PRDs, standalone English design handoff and execution prompt | Matching requirement IDs, accepted architecture, fixture authority and evidence status; no AC prerequisite |
| G1 — shared calculation proof | Shared core/use cases, bounded composition, optional modules, import validation, H/I fixtures and boundary oracles | Decimal totals, source/scope integrity, backend capability checks, schedule and optional metric checks |
| G2 — playable core | Shared three-tab app, CSV/demo, state recovery, evidence/feedback | Household and industrial journeys both work without schedule/output input |
| G3 — saved data service | Owner auth, persistence, import commits, exports, retention/restore | Ownership, privacy, idempotency and failure tests |
| G4 — platforms and usability | Responsive web/native builds and separate segment studies | Declared platform evidence and UX checks; task-blocking issues fixed |
| G5 — optional live pilot | Selected meter adapter, authenticated ingestion, appropriate installation | Actual reference comparison and quality evidence per installation |

This ordering does not permit a credential-free demo to be exposed as a production saved-data service. A release can provide a clearly labelled CSV-only core before live hardware support; live status is a separate gate. Advance by verified deliverables and evidence rather than an event deadline.

Final deliverables for implementation: runnable shared app/server as applicable; fixture generator and calculation/contract tests; source adapter capability/status list; setup/runbook with no secrets; UX/platform results; household and industrial walkthroughs; research script/results or pending status; explicit list of simulated, implemented-unverified, verified and blocked paths. A running demonstration alone does not satisfy the release gates.

## 22. Implementation and handoff requirements

### 22.1 Product and calculation contract

Implement electricity monitoring and evidence-based advice through the three-tab bilingual interface and shared mobile/web target. The complete CSV/demo path, optional tariff, statistical baseline, missing-data semantics, provenance, scope-safe aggregation, secure ownership checks, retry-safe operations and exclusion of physical control are required parts of the handoff. No delivery may omit a safeguard because another context does not display its setup screen.

### 22.2 Compatibility and data preservation

When integrating with an application or migrating stored data, explicitly map IDs, source bindings, browser/server records, CSV aliases, API clients, calculations and tests. Preserve supported timestamp-only CSV aliases and their interval-Wh interpretation, original imported asset names and valid historical measurements. Industrial machine records can be represented as assets without losing their identity or history. Use compatibility adapters for supported external contracts and verify affected callers before removing an interface.

Do not perform an unverified bulk string rename or destructive schema conversion. Document migration, rollback and recovery steps; prove restored readings reconcile with summaries and that repeated migration/import does not duplicate energy. Schedule, tariff, metric and source changes retain effective times and evidence revisions. Data deletion remains a separate explicit owner action.

### 22.3 Reusable delivery contract

Deliver the concrete boundaries and release records in section 15 and FR-21–22, including supported composition validation, the minimal capability manifest, shared-domain/API/worker checks, and an upgrade/rollback process. Preserve identical core arithmetic across supported builds; a client-specific change belongs in a named module, adapter or bounded configuration only when it matches that responsibility. Unsupported combinations fail clearly. Do not implement a microservice split, generic plugin system or tenant control plane merely to demonstrate reuse.

### 22.4 Verification and operational handoff

Deliver a reproducible setup, versioned measurement/API contracts, deterministic fixture inputs and calculation assertions, adapter capability/status records, and recorded acceptance results. Identify the release, configuration, runtime and dataset used for each result. Include owner-isolation and invalid-import checks, source/parent-child overlap cases, retry/recovery behaviour, restore evidence and separate household/industrial usability outcomes. Unexecuted checks remain not run.

Keep secrets out of code, fixtures, exports and runbooks. Document deployment, backup/restore, credential revocation, retention/deletion and failure diagnosis before saved live data is offered. Verify framework versions, vendor behaviour, electrical suitability and physical measurement accuracy for each supported adapter at implementation time; unsupported capability remains visibly unavailable. No field or savings claim follows from passing a simulated fixture.

## 23. Open assumptions, risks, and definition of done

| Uncertainty | Required evidence / disposition |
|---|---|
| Whether users understand measurement scope | Separate household/business usability tasks; fix misleading totals before release |
| Whether the chosen adapter/load combination works | Physical setup and reference-meter comparison; publish only tested capability |
| Sensitivity of change thresholds | Calibrate household and industrial datasets; report false/missed observations by context |
| Imported interval semantics and resolution | Explicit preview confirmation; retain provenance; suppress unsupported comparisons |
| Industrial shift calendars and output meaning | Explicit weekly windows and output units; advanced rotations/conversions deferred |
| Mixed parent/child or net-energy meters | Resolve aggregation; unsupported signed net-energy remains blocked rather than miscomputed |
| Native build and push availability | Test named runtimes separately; push never blocks core value |
| Real savings and equipment efficiency | Not established by a demonstration or consumption observations; require separate measured evaluation |

Generic v1 is complete only when the implemented release satisfies its required functional, UX, data-integrity, security and reusable-delivery checks; both H/I core journeys are evidenced without AC; households work without schedules or output inputs; supported scopes never double count; arithmetic and import oracles pass; unavailable values remain honest; and runtime/field status is explicitly reported. A documented failed or not-run gate is not a pass.

The specification is generic across **measured electricity-consuming assets and user contexts**. It does not promise that every electrical device can use the same hardware, that every connected appliance can be identified separately, or that monitoring alone can prove avoidable waste. This boundary is part of the product contract.

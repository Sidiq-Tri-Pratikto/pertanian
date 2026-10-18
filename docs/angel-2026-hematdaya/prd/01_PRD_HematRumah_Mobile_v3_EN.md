# HematRumah — Product Requirements Document
## Version 3.0: a simple mobile app for electricity monitoring and useful recommendations

Date: October 18, 2026 (Asia/Jakarta).
Document language: English. Product interface: Indonesian.
Status: development specification; usability targets are proposed, and live hardware integrations are unverified.
Working product name: HematRumah.

## 1. Product contract and authority

HematRumah helps household residents understand electricity use across the appliances they monitor and receive useful recommendations based on available evidence. A supported energy meter alone must provide the core value.

The implementation target is React Native + Expo + TypeScript for Android and iOS, using one shared application codebase. A browser-based phone preview is acceptable for the design prototype when its runtime cannot render native code. It is a design simulation, not delivery of the native application.

This document replaces the active requirements of earlier HematRumah files, including web/PWA/Next.js architecture, an AC-first experience, controller-led onboarding, and older acceptance-test meanings. The embedded PRD in each v3 handoff is identical to this file. For a conflict, use the user's latest explicit correction first, then this v3 PRD. Archived discussion explains decisions; it is not an instruction to implement superseded ideas.

The three new files are:
1. 01_PRD_HematRumah_Mobile_v3_EN.md — product specification.
2. 02_Claude_Design_HematRumah_Mobile_v3_EN.md — standalone playable-design handoff.
3. 03_Claude_Code_HematRumah_Mobile_v3_EN.md — standalone implementation handoff.

## 2. Problem, users, and outcomes

A nontechnical resident may have electricity measurements but still struggle to understand which appliance contributes most, whether its pattern changed, and what advice is justified. A dense technical dashboard or mandatory smart-home control setup adds effort before delivering that value.

Primary users are Indonesian household, apartment, and boarding-room residents who use a phone and have a compatible meter. They do not need to understand MQTT, watts, model training, or cloud credentials.

The core experience answers:
- “Berapa pemakaian perangkat yang saya pantau?”
- “Perangkat mana yang paling besar kontribusi biayanya?”
- “Apa yang berubah, dan apa saran yang masuk akal?”

A successful outcome can be reading and understanding an explanation. Acting on hardware, acknowledging every recommendation, or enabling automation is not required.

### Proposed success measures

| Measure | Proposed target / interpretation |
|---|---|
| Usability | At least 4 of 5 representative first-time testers complete each core research task without moderator guidance |
| Find main cost contributor | Within 30 seconds from a populated Home for at least 4 of 5 testers |
| Explain an insight | Tester identifies the observation, comparison, and limitation in their own words |
| Meter-only usefulness | Complete monitoring and recommendation journey without Tuya, controller, sensor, weather, LLM, or schedule |
| Trust | Correct units, visible freshness/coverage, and no missing data displayed as zero |
| Insight relevance | Record optional usefulness feedback and false-positive reports; do not invent a target percentage before a pilot |

These are acceptance targets and research plans, not measured results. Do not claim a savings percentage or validated Indonesian household impact without an appropriate real-home evaluation.

## 3. Release boundary

### Tier A — required core MVP

- Mobile application, individual accounts, isolated demo mode.
- Multiple monitored appliances in one account.
- Supported-meter catalog and guided enrollment.
- Shelly Plug PM Gen3 as the first integration target; TP-Link visible as “Segera hadir”.
- Appliance name/category, current power where available, energy, estimated cost, simple daily/weekly history.
- Totals explicitly limited to monitored, distinct measuring channels.
- Category-aware usage learning and evidence-based recommendations.
- Read-only recommendations and optional feedback.
- In-app insight inbox; optional native push notifications with platform setup verified separately.
- Learning, empty, loading, offline, partial-data, missing-tariff, error and retry states.
- Complete hardware-free simulator, provenance labels and shared virtual clock.
- Server collection that continues while the app is closed.

### Tier B — optional AC extension, after Tier A passes

Preserve the earlier AC ideas as a separate, disabled-by-default module:
- Link a tested controller, initially the BARDI/Tuya candidate.
- AC ON/OFF and supported temperature setpoint.
- Explicit one-off arrival preparation.
- Advanced, opt-in AC remote-OFF after three unanswered received reminders.

These do not gate core completion. Access them from the relevant AC detail/settings. The default design walkthrough covers Tier A. Omit optional UI entirely if it would dilute that walkthrough; document the module boundary instead. Do not introduce a fourth main tab.

### Further enhancements — do not implement in this release

Live TP-Link or extra vendor integrations; physical mains cutoff; whole-home disaggregation; enterprise management; equipment-fault diagnosis; cameras or occupancy inference; geofencing; mandatory location; general chat/voice assistant; solar/battery optimization; dynamic purchasing or billing integration; subscriptions/marketplaces; guaranteed savings; complex household sharing or multiple homes; separate Android/iOS application codebases; dark mode as a separate design project.

Weather and optional routine/context may be added when relevant and available, but are never prerequisites for Tier A.

## 4. Domain model and appliance behavior

| Concept | Meaning |
|---|---|
| Meter | Physical energy-measuring channel and its connectivity identity |
| Appliance | User-labeled load, such as “Kulkas Dapur”, with a category/usage profile |
| Binding | Time-bounded association between meter and appliance |
| Provider/model | Integration and device-specific capabilities |
| Controller | Optional actuator, independent of the meter |
| Room sensor | Optional temperature/humidity source, independent of energy |
| Insight/recommendation | Observation plus evidence, uncertainty, and optional advice |

One meter per appliance is the initial simple interaction. If a meter covers multiple loads, label it as a group/unknown load and provide descriptive totals. Do not infer each appliance's share. Do not build complex group management.

Initial categories: refrigerator/freezer, TV, computer/workstation, AC, washing machine, other. Store the user's classification; it is not proof of appliance identity.

| Profile | Appropriate baseline | Avoid |
|---|---|---|
| Continuous: refrigerator | Daily/interval energy and comparable coverage | “It has been on too long; turn it off” |
| Session: TV/computer | Estimated session duration, timing, energy | Claiming longer use proves waste or absence |
| Modulating: inverter AC | Session/interval energy, optional weather context | Inferring room comfort/setpoint from watts |
| Cycle: washing machine | Descriptive cycle energy when sufficiently observed | Treating every low-power gap as OFF |
| Unknown/group | Conservative energy summaries | Invented appliance-specific diagnoses |

Schedules are optional. No model may assume occupancy or claim an exact waste amount from a meter alone.

## 5. Mobile information architecture

Only three persistent bottom tabs:
- Beranda — understand the selected-period overview.
- Perangkat — browse/add appliances and open their details.
- Saran — browse explanations and optional feedback.

Profile/settings is a secondary icon with an accessible label. Detail and setup screens use stack navigation. Preserve tab/period/scroll context on return. Android back, visible back, keyboard dismissal, and accessible focus must behave predictably.

### Screen requirements

| ID | Screen | Required content and main action |
|---|---|---|
| S01 | Welcome / account / demo | Short value statement; “Mulai” and a visible “Coba demo”; clear mode boundary |
| S02 | Empty Beranda | Why a meter helps; one “Tambah perangkat” action; optional demo entry |
| S03 | Populated Beranda | Period, monitored energy/cost, freshness/coverage, ranked device preview, at most one featured insight |
| S04 | Perangkat | Simple cards: appliance name/category, energy/cost, last data/status; “Tambah perangkat” |
| S05 | Add meter wizard | Brand → model → connection/first reading → appliance name/category → success |
| S06 | Appliance detail | Selected-period energy/cost, simple history, comparison, related insight; optional technical details |
| S07 | Saran | Insight cards with plain observation, period and freshness; empty/learning state |
| S08 | Insight detail | What changed, comparison, evidence, limitation, optional practical suggestion and feedback |
| S09 | Settings | Tariff, timezone, notification preference; optional city/context; account |
| S10 | Appliance settings | Rename/category, meter connection details, remove binding; optional controller entry only if appropriate |

The overview heading must say “Estimasi biaya perangkat dipantau” or an equally clear short equivalent with visible scope. It must never say “Total tagihan rumah” based only on plug meters.

Home shows the most important information first. Avoid technical tile walls, multi-axis charts, remote-control panels, mandatory chat, sidebars, or raw event tables.

## 6. UI/UX quality contract

The following IDs are binding for Design and Code. Visual styling can evolve while satisfying them.

| ID | Requirement | Verification |
|---|---|---|
| UX-01 | Three labeled bottom tabs; selected state visible without color alone | Navigate all tabs, deep links, and return paths |
| UX-02 | One primary action per task screen; simple hierarchy | Check first-use, setup, detail and error screens |
| UX-03 | Ordinary Indonesian; explain technical terms on demand | No MQTT, Tuya IDs, JSON or trace codes in everyday task instructions |
| UX-04 | At most 3 deliberate taps from populated Home to highest-contributor evidence or featured insight detail | Count taps; exclude auth/setup and scrolling |
| UX-05 | Setup back/retry preserves name/category and completed choices | Go back, induce failure, retry; explicit exit may ask to discard |
| UX-06 | Clear freshness, coverage, estimates and demo labels | Inspect normal, offline, partial and simulated scenarios |
| UX-07 | Accessible targets and contrast | Aim for at least 48 logical-unit touch areas; normal text contrast ≥4.5:1, large text ≥3:1; verify final palette |
| UX-08 | Large text and screen readers | Verify about 200% text scaling, logical focus, labels/state, text chart alternative; no blocked CTA |
| UX-09 | Safe areas and keyboard | Verify widths 360/390/430, small height, long names, scrolling and keyboard avoidance |
| UX-10 | Predictable feedback/recovery | Immediate loading/pressed state; retry explanation; no indefinite spinner or dead primary action |
| UX-11 | Optional setup stays optional | Tariff, permissions, weather, schedule and controller can be skipped |
| UX-12 | Calm, nonjudgmental recommendations | Explain evidence; no red warning for normal refrigerator operation or guilt for dismissing advice |

Layout guidance: comfortable spacing using a small spacing scale; clear text sizes; icons paired with labels; readable card grouping; restrained shadows and motion; plain bar/line charts with accessible summaries. Use subtle brand color and reserve warning/error colors for meaningful states. Do not rely on aesthetics alone as proof of usability.

Suggested hierarchy: monitored estimate and period → top contributing devices → one useful insight. Secondary technical power/voltage/current goes behind “Detail pengukuran”. In a healthy state, status should be quiet rather than visually competing with energy/cost.

### Language and formatting

- Use IDR and Indonesian numeric/date formatting consistently.
- “Tidak ada data” differs from “0 kWh”.
- “Data meter terlambat” differs from “Perangkat mati”.
- “Sedang mempelajari pola” still shows available measured history.
- Every example number or generated reading has provenance.
- Permission prompts appear after a brief explanation when the user chooses the related feature.
- Denying notifications never blocks any core task.
- Long appliance names wrap or truncate accessibly; full name remains available in detail.
- Surface concise actionable error text. Technical support details may be disclosed separately.

## 7. Core user stories and journeys

### P01 — Start and add an appliance

As a first-time resident, I can try a demo or create an account, choose Shelly/model, follow connection guidance, receive a valid reading, name/categorize my appliance, and see monitoring.

Required behavior:
1. Brand selection; TP-Link opens “Segera hadir”, then returns without losing context.
2. Model summary describes monitoring, not switching.
3. Connection clearly distinguishes waiting from connected.
4. A physical pilot may need operator-assisted Wi-Fi/MQTT configuration. Explain that support honestly in the setup flow without dumping developer instructions into the product.
5. Name/category; show examples across categories. Returning from this step preserves entered values.
6. Success opens appliance detail and returns naturally to populated Home.
7. Tariff, city, schedules, notifications and controller are skippable.

Connection state: draft → waiting for authenticated first reading → verified → assigned. Expired enrollment can be renewed safely; retries must not create duplicate appliances/bindings.

### P02 — Understand usage and contribution

As a resident, I can choose today or this week, see monitored energy/cost and contributing appliances, then open the largest contributor to understand its history.

Changing period updates all relevant values consistently. “Hari ini” is local midnight to current time; “Minggu ini” is Monday local midnight to current time, with explicit dates. Comparison periods are matched in elapsed duration/coverage where used.

Missing tariff shows energy and an optional “Tambahkan tarif” cue. Partial coverage shows a partial observed amount, not a complete estimate of unmeasured usage.

### P03 — Read a useful explanation without control

As a resident with a refrigerator meter, I can read that its comparable-period energy changed, see the evidence, and choose to inspect usage conditions. No OFF button is needed.

The explanation must answer: what changed, compared with what, how much usable data supports it, and what remains unknown. General tips must be labeled as general guidance.

### P04 — Give optional feedback

As a resident, I can mark an insight “Bermanfaat” or “Kurang sesuai”, optionally indicate conditions changed, dismiss it or request a later reminder. Reading is already a valid outcome.

Feedback persists and updates the visible card/detail consistently. A snooze suppresses repeated notices of that insight for the chosen interval; it does not delete measurements or enable control.

### P05 — Recover from incomplete data

As a resident, I can understand an empty/cold-start/offline/partial-data state, see last known values where appropriate, and retry without losing my place.

Core workflows remain usable when the phone has cached data, notification permission is denied, tariff/weather are absent, or the optional provider fails. Mutations requiring connectivity show a clear retry and are not falsely marked saved.

### P06 — Explore optional AC features

Only from an AC detail/settings, an interested user can enable an optional controller module. This is not required to finish P01–P05. Its complete conditional contract appears in section 10.

## 8. Functional requirements

### FR-01 — Mobile accounts and demo

Support register/login/logout, short-lived access tokens, rotated/revocable refresh sessions and server ownership checks. Use native secure storage for session secrets; do not carry over web cookies as the primary mobile authentication design. Passwords are hashed with an appropriate maintained password-hashing implementation.

Demo must work without hardware, vendor credentials, LLM or external data. Maintain a clear “Demo · Data simulasi” indicator. Leaving demo returns to the mode entry without leaking demo data into a real account. Logging out removes user cache and invalidates/revokes the relevant server refresh session.

### FR-02 — Catalog and capabilities

Catalog flow: provider → model → connection → appliance assignment. Shelly Plug PM Gen3 supports energy monitoring; TP-Link is coming soon. Keep catalog potential capabilities separate from effective tested capabilities.

Capabilities include can_measure_energy, can_control_ac, can_read_room_temperature, can_cut_power. For Plug PM alone, only monitoring is offered. The current selected configuration never advertises mains cutoff.

### FR-03 — Enrollment and binding

Issue expiring single-use enrollment with authenticated device/broker identity. An arbitrary submitted device_id is insufficient ownership proof. The pilot may use server-assisted provisioning, documented separately from the consumer screens.

Require a first valid reading before claiming live connection. Support name/category editing and removing a binding with confirmation. Removing stops future association; it does not silently destroy historical readings. Reassignment closes the old binding and creates a new interval; history remains attached to the load measured at that time. Category changes invalidate incompatible learned baselines and show relearning where needed.

### FR-04 — Telemetry, time and quality

Configurable collection target: approximately 60 seconds; proposed stale threshold: 180 seconds. These are application defaults, not guaranteed device intervals.

Normalize active power W, cumulative energy Wh, optional voltage/current, source/receipt timestamps, source event identity, origin and quality. Deduplicate delivery, handle counter resets/out-of-order data and clock anomalies, and preserve gaps. Backend collection continues while the mobile app is closed.

Use UTC persistence and account/device timezone for display and bucketing. Default display timezone is Asia/Jakarta, editable. Do not invent a source timestamp when only receipt time exists. Do not promise device-side historical backfill unless verified.

### FR-05 — Energy and estimated cost

Use positive cumulative-counter differences within valid segments, divided by 1000 to obtain kWh. A decrease starts a reset segment. Duplicate or late arrival cannot create duplicate/negative consumption. Prefer counter deltas; power integration is a separately labeled estimate limited to sufficiently covered intervals.

Cost = allocated kWh × user-entered tariff effective during that interval. Use decimal monetary arithmetic, not binary-float currency accumulation. Effective-dated tariff changes do not rewrite prior costs. Unknown tariff displays no fabricated rupiah amount.

A gap-crossing counter delta can establish total energy over the segment but not its exact allocation across midnight or a tariff boundary. Store unallocated/uncertain energy separately. Show known cost/energy as partial, and explain what cannot be allocated.

Aggregate distinct monitored channels only. Reject overlapping duplicate bindings for the same channel. Never present plug-meter totals as a PLN bill or whole-house consumption.

### FR-06 — Overview, list and detail

Home and appliance list show selected-period energy/cost, category/name, freshness and appropriate status. Show today/this-week history; more advanced charts are secondary. A comparison must state the exact reference and whether periods are sufficiently comparable.

Detail provides textual chart summary, related insights and optional measurement details. Current power, last power sample and appliance ON/OFF are different concepts. Offline meter data cannot prove appliance OFF.

### FR-07 — Category-aware learning

Start with deterministic summaries and robust contextual baselines such as medians/quantiles and time/day profiles. Session inference uses category-specific thresholds/hysteresis and marks uncertainty; it must not use one threshold across all appliances.

Proposed readiness:
- Session-duration insight: at least 10 valid sessions spanning at least 7 days.
- Continuous daily-energy comparison: at least 7 comparable day windows in reference history, each with ≥90% usable coverage; target window also ≥90%.
- Weekly contribution summaries need measured energy, not a trained model.

These are configurable pilot assumptions. Inadequate history shows learning/descriptive summaries. Do not fabricate a personal insight to populate a screen.

A simple regression such as Ridge may be evaluated when sufficient data exists; it is not a prerequisite for useful monitoring. Use only known features and chronological evaluation against a simpler baseline. A model never calls a controller.

### FR-08 — Evidence-based recommendations

Each personalized recommendation stores:
- appliance, insight type and relevant interval;
- observed metric/unit and reference metric/period;
- change calculation, coverage and model/rule version;
- provenance, uncertainty and generated/expiry timestamps;
- explanation and optional practical suggestion;
- optional feedback/dismiss/snooze state.

Initial insight types: cost contribution, comparable energy change, session-duration change for suitable appliances, descriptive patterns, and cautious sustained-low-load review. Do not assume low load is useless; medical/essential/unknown loads receive only descriptive guidance.

Do not infer equipment faults, occupancy, remote settings, exact avoidable waste or savings causation from unsupported data. A refrigerator can receive “Periksa apakah kondisi penggunaan berubah”, not “Matikan karena menyala terlalu lama”.

Read-only detail with “Lihat penjelasan” is a complete experience. No hardware CTA is mandatory. General advice is distinguished from a personalized finding.

### FR-09 — Feedback and notifications

Provide optional useful/not-relevant feedback and dismiss/snooze. Notification preferences are secondary settings; the insight inbox works without push. Deduplicate messages per insight/incident and allow a quiet period.

Core push scope is an optional new-insight notice with a deep link into Saran/detail. Verify OS permission and native development-build credentials separately. Gateway acceptance is not proof of receipt/read. If live push setup is unavailable, complete in-app behavior and label live push unverified.

### FR-10 — Optional context and settings

Manual tariff in IDR/kWh and effective date, timezone, names/categories, notification preference. City/weather context and optional routine can be skipped. No continuous GPS/location permission. Weather is used only for appropriate models and explicitly flagged if missing/stale.

Tariff entry explains “tarif per kWh” in simple language. Do not hardcode an assumed PLN plan, fetch billing credentials, or claim the entered tariff is an official verified rate.

### FR-11 — Informational alerts

Core alerts provide neutral observations and optional responses. Category-specific limits and deduplication avoid repeated nuisance prompts. An unanswered core insight does not trigger action.

For a session-based AC, “Penggunaan AC Kamar lebih lama dari biasanya. Apakah kamar masih dipakai?” is a possible prompt, not a universal template. Continuous-operation appliances receive no duration-based OFF suggestion.

## 9. Data interpretation and analytics rules

1. Maintain raw normalized readings plus quality metadata and derived aggregates.
2. Deduplication uses stable capture/event identity. Identical numeric readings can be legitimate separate samples.
3. Recompute affected derived intervals for late readings idempotently; never double-add deltas.
4. Segment cumulative counters at resets/invalid transitions. Do not assume a full starting counter belongs to a new account.
5. Coverage distinguishes fresh status, observed interval coverage, and energy allocation confidence.
6. Matched comparisons use the same appliance/binding/profile and comparable elapsed windows. Suppress percentage change when reference is zero or unsuitable; show the absolute observation instead.
7. Missing data, missing tariff, and learning are independent states.
8. Synthetic, dataset-replay, and live data remain distinguishable in storage and UI.
9. Compare optional ML to simple baselines with chronological splits; fit preprocessing only on training data. Record sample sizes, units, errors and limitations; no invented benchmark.
10. Demonstrating a savings opportunity does not prove realized savings. Do not add a savings score requiring an unsupported counterfactual.

Plegma and CN-OBEE are historical research candidates, not bundled verified datasets. Inspect their actual fields, license, load channels and suitability before use. Deterministic synthetic fixtures are enough for initial product development. Real local pilot evidence is a separate validation stage.

## 10. Optional AC module — conditional requirements

### FR-12 — Controller-based AC operation

An explicitly linked controller with per-function tests may provide ON/OFF and supported setpoint. Shelly Plug PM Gen3 is monitoring-only. The candidate path is app → our API → Tuya Cloud → BARDI → IR → AC; this is a design target, not verified project hardware.

Separate these evidence states: requested/scheduled, provider accepted, appliance activity observed, target temperature observed, failed, unknown outcome, expired/cancelled. A successful IR API request does not prove the AC received it. Energy changes are supporting activity evidence, not precise comfort measurement.

Check ownership, capabilities, expiry and idempotency; store audit events. A post-dispatch timeout is unknown outcome, with no blind retry of an IR toggle. Prefer supported desired-state commands. Do not promise physical exactly-once execution.

Live gates: actual model/account pairing, project region/entitlement, IR code/ON/OFF/setpoint support, and sensor API access tested independently. Do not assume a BARDI OEM account equals Smart Life. Trial expiry/quotas/price are console dependencies, not guaranteed constants in this PRD.

### FR-13 — One-off arrival preparation

Require explicit selected AC, arrival time and requested target/preference. No habitual auto-ON inferred from meter data. A review screen explains planned start and uncertainty; allow edit/cancel.

Fresh indoor-temperature history is necessary to learn and verify target attainment. Without it, offer a clearly accepted estimate; without cooling history, offer an explicitly chosen manual duration. A target is not guaranteed. Forms are sufficient; no required LLM or chat screen.

Persist schedules with versions, expiry and atomic claims. Editing/cancelling/manual override invalidates older actions. Recheck immediately before dispatch. Never execute a missed start late after a restart.

### FR-14 — Three-reminder remote-OFF

AC-only, per-device opt-in, default OFF, advanced settings. Never apply to refrigerator/unknown loads.

In one active incident, each reminder counts only after confirmed receipt and its response window expires without response. Proposed interval: 10 minutes; after the third, show a 60-second cancellable countdown. Gateway acceptance/unknown/failed delivery do not count. If receipt cannot be established, do not execute automatic OFF.

Any response, snooze, active manual override, ended session, stale telemetry, unavailable controller, disabled policy or expired incident prevents/escalation-cancels the action. Revalidate all guards immediately before sending OFF. Policy updates/version changes invalidate queued work. Cancellation after an external send cannot retract it; report the actual state.

This sends remote OFF. It never disconnects mains in the selected configuration. Any restart delay must follow tested appliance/provider constraints.

## 11. Architecture and technology

~~~mermaid
flowchart TD
    APP["React Native / Expo app"]
    API["FastAPI"]
    DB[("PostgreSQL")]
    WORKER["Python ingestion and analysis worker"]
    MQTT["Mosquitto with TLS"]
    METER["Supported meters: initially Shelly"]
    APP <-->|HTTPS| API
    API <--> DB
    METER -->|Outbound telemetry| MQTT
    MQTT --> WORKER
    WORKER <--> DB
~~~

Optional native push, weather and Tuya are adapters outside the core path. The mobile app reads our API; it does not hold vendor API secrets or act as the always-on meter collector. No Raspberry Pi is required for the proposed Shelly-to-server path, subject to physical configuration testing.

| Layer | Initial implementation |
|---|---|
| Mobile | React Native, Expo, TypeScript, Expo Router; reusable native components and tokenized styles |
| Client data | A maintained query/cache library or a simple equivalent; explicit loading/error/stale state |
| API | FastAPI modular monolith with generated OpenAPI |
| Storage | PostgreSQL, migrations, UTC timestamps and decimal cost/tariff |
| Ingestion | Mosquitto TLS, per-meter identity/ACL, Python consumer |
| Analysis | Shared Python domain logic; statistics first, optional scikit-learn |
| Server deployment | Docker Compose: API, worker, database, broker; HTTPS reverse proxy for a pilot |
| Mobile running | Expo dev server / development build separately from server Compose |

Document how a real phone reaches the development API; phone localhost is not the development computer. Do not require Docker to build or run iOS locally on Linux. Verify platform-specific builds and notification setup in the environment actually available. A browser render does not prove iOS/Android execution.

Refresh queries on foreground and user pull-to-refresh. Proposed foreground refresh is 15 seconds while appropriate screens are visible. Backend sampling continues independently; avoid battery-heavy background loops on the phone.

## 12. Minimum data and API contracts

### Core records

User, RefreshSession, DeviceCatalog, MeterEnrollment, MeterChannel, Appliance, MeterBinding, Measurement, CounterSegment, EnergyAggregate, EffectiveTariff, UsageProfile/BaselineVersion, Recommendation, RecommendationFeedback, NotificationPreference, PushRegistration, ActivityEvent.

All resource access is scoped to the owner. A recommendation retains its evidence snapshot so explanations remain interpretable after recalculation. Appliance-specific AC fields belong to optional capability records.

Optional records: ControllerBinding, RoomSensorReading, WeatherObservation, Command/Attempt, ArrivalPlan, ScheduledAction, AlertIncident, ReminderReceipt, AutomationPolicy.

### Minimum API routes

| Method / route under /api/v1 | Purpose |
|---|---|
| POST /auth/register, /auth/login, /auth/refresh, /auth/logout | Account/session lifecycle |
| GET/PATCH /me | Profile and timezone |
| GET /device-catalog | Supported/coming-soon providers and model capabilities |
| POST /enrollments; GET /enrollments/{id} | Create and check verified setup |
| POST /appliances; GET /appliances | Assign verified meter and list |
| GET/PATCH /appliances/{id}; DELETE /appliances/{id}/binding | Detail/settings and close binding |
| GET /summary; GET /appliances/{id}/summary | Period totals, coverage, provenance |
| GET /appliances/{id}/measurements | Bounded history/chart data |
| GET /recommendations; GET /recommendations/{id} | Inbox and evidence |
| POST /recommendations/{id}/feedback | Optional feedback/dismiss/snooze |
| GET/POST /tariffs | Effective-dated tariff |
| GET/PATCH /notification-preferences; POST/DELETE /push-registrations | Optional notices |
| GET /activity | User-readable relevant events |
| GET /health/live; GET /health/ready | Process/dependency health |

All mutation routes validate ownership and input. Creation/enrollment retries use idempotency. Optional controller/arrival/automation APIs are namespaced/capability-gated; they are not onboarding prerequisites. Route naming can be refined consistently in the code handoff/OpenAPI.

Illustrative normalized reading, not a native Shelly payload:

~~~json
{
  "schema_version": 1,
  "device_id": "meter_demo_fridge",
  "sample_id": "capture-001",
  "measured_at": "2026-10-18T14:00:00Z",
  "received_at": "2026-10-18T14:00:01Z",
  "power_w": 92.5,
  "energy_total_wh": 104250.8,
  "origin": "simulated",
  "quality": []
}
~~~

Summary responses include interval start/end, timezone, energy/cost amounts and status, monitored channel count, contributing/fresh channel counts, coverage/allocation flags and last update. Do not encode unavailable cost as zero. Demo mode is a server-enforced environment/tenant boundary, not a client-controlled live flag.

Errors use a stable code, safe actionable Indonesian message and trace_id. Log details securely with context; keep credentials and raw vendor secrets out of responses.

## 13. Security, reliability and operational expectations

- HTTPS for API and TLS/identity/ACL for exposed broker access; no home-router port forwarding.
- Server ownership checks for every read, mutation, subscription and optional command.
- Native refresh secrets in secure storage; bounded access-token life; revoke on logout and handle expired sessions without losing a user's current form unnecessarily.
- Per-device broker credentials or an equivalent authenticated mechanism; never trust a payload's device_id as authentication.
- Keep vendor credentials server-side; placeholder-only configuration examples.
- Retry safe transient reads with bounded backoff. Enrollment/mutation retries require idempotency; optional actuators require stricter unknown-outcome handling.
- Persistent ingestion/aggregation handles duplicate delivery and restarts.
- Liveness differs from readiness; record source, freshness, ingestion lag, quality failures and recommendation generation failures.
- No silent catch-and-continue that produces false success or a zero summary.
- Demo reset only affects its isolated dataset. No simulator code can choose a live adapter.
- Define a pilot retention default in configuration; avoid indefinite raw-data retention by accident. Data deletion/export policy for a public release is a later decision, not a new MVP UI project.

## 14. Canonical demo and state fixtures

All values below are synthetic and intended to make screen relationships testable.

Freeze default virtual time at October 18, 2026, 21:00 Asia/Jakarta. Seed at least 30 prior days and four categories. Default week window: October 12, 00:00 through October 18, 21:00 local time. Values represent complete usable coverage within that elapsed window.

Illustrative manual tariff: Rp1.500/kWh. It is a demo input, not a claimed official PLN rate.

| Appliance | Week energy | Week estimated cost |
|---|---:|---:|
| AC Kamar | 14.0 kWh | Rp21.000 |
| Kulkas Dapur | 8.4 kWh | Rp12.600 |
| Komputer Kerja | 5.6 kWh | Rp8.400 |
| TV Ruang Tamu | 2.0 kWh | Rp3.000 |
| Monitored total | 30.0 kWh | Rp45.000 |

Default “today” fixture: AC 2.0 kWh, refrigerator 1.2 kWh, computer 0.8 kWh, TV 0.3 kWh; total 4.3 kWh and Rp6.450. Generate bucket histories that reconcile exactly to their selected-period totals. Counts, cards, charts and detail must derive from shared data, not separate hardcoded values.

Example refrigerator insight: comparable elapsed-week energy 8.4 vs 7.0 kWh, +1.4 kWh / +20%, with matched usable coverage. Wording: “Konsumsi Kulkas Dapur naik 20% dibanding periode pembanding.” Explain conditions may have changed; no fault claim or OFF button.

Example TV insight: a completed 3-hour session against a 2-hour median across 12 valid comparable sessions over at least 7 days. Explain usage may be intentional. Do not compare today's incomplete session against a completed-session baseline as if equivalent.

Scenario controls, outside ordinary product navigation: normal, empty, cold start, no tariff, stale meter, partial coverage, connection failure/retry, notification denied, long-name/large-text, and reset. All use a shared virtual clock. Optional AC scenarios are a separate secondary fixture pack.

## 15. Acceptance tests

The meanings below are v3 definitions; older files with the same IDs are superseded.

| ID | Scenario | Expected result |
|---|---|---|
| AT-01 | Demo with no credentials | P01–P05 playable; visible simulation label |
| AT-02 | Select TP-Link | Coming soon; no fake live binding |
| AT-03 | Add Shelly and a second appliance | Ordered setup, independent names/categories; no controller/schedule required |
| AT-04 | No first reading / setup retry | Waiting/expired/retry is clear; no false connected state or duplicate creation |
| AT-05 | Duplicate/reset/out-of-order readings | Correct segments and totals; no negative/doubled energy |
| AT-06 | Gap across midnight/tariff boundary | Total segment evidence retained; uncertain allocation/cost marked partial |
| AT-07 | No tariff/weather | Energy and relevant insights work; no fabricated money/weather context |
| AT-08 | Cold start | Available measured summary plus learning; no invented personal baseline |
| AT-09 | Refrigerator runs continuously | No extended-duration OFF recommendation |
| AT-10 | TV session extends | Category-appropriate evidence, duration uncertainty, no occupancy claim |
| AT-11 | Read-only recommendation | Complete explanation and optional feedback with no actuator |
| AT-12 | Multiple meters / duplicate binding | Reconciled monitored totals; no overlap/double counting |
| AT-13 | Meter or phone offline | Cached/last known data, timestamps, retry; absent is not zero/OFF |
| AT-14 | Notifications denied | In-app Saran and every core task remain available |
| AT-15 | Long names and large fonts | UX-07–UX-09 met; full information/actions reachable |
| AT-16 | Back/keyboard/failed submit | Inputs/context preserved; no trapped flow |
| AT-17 | Other user's resource ID | Read/mutate/subscription denied without leaking data |
| AT-18 | Baseline/optional ML | Readiness/coverage tested; chronological evaluation if a model is trained; honest labels |
| AT-19 | Simulator and reset | Same domain path; no live side effect; deterministic shared time |
| AT-20 | Core-only install/run | Native app target and server demo work without Tuya/sensor/LLM/weather |
| AT-21 | Optional AC control enabled | Tested capabilities; accepted differs from observed/verified |
| AT-22 | Optional arrival enabled | Review/edit/cancel/expiry; missing sensor gives estimate only |
| AT-23 | Optional auto-OFF enabled | Opt-in, three confirmed-received unanswered windows, countdown/cancel/guards |
| AT-24 | Optional provider fails | Honest status; monitoring and read-only insights unaffected |

AT-01–AT-20 and UX-01–UX-12 gate Tier A. AT-21–AT-24 gate Tier B only if implemented/enabled. Simulated success is not live verification.

### Usability research protocol

Recruit five representative nontechnical phone users when available. Use neutral tasks without pointing to buttons:
1. “Tambahkan alat bernama TV Ruang Tamu pada demo.”
2. “Cari alat dengan estimasi biaya paling besar minggu ini.”
3. “Jelaskan apa arti saran untuk Kulkas Dapur.”
4. “Cek kapan terakhir data alat yang terputus diterima.”
5. “Ubah tarif, lalu kembali ke ringkasan.”

Record completion, time, wrong turns, moderator assistance, and what users misunderstood. Target 4/5 on tasks 1–3, including the 30-second task 2. Prioritize fixes that prevent successful tasks; retest changed paths. If participants are unavailable, deliver a test script and an explicit “not yet user-tested” status. A heuristic inspection is not a participant study.

## 16. Delivery sequence and definition of done

M0 — Scope, contracts, mobile navigation, deterministic multi-appliance fixtures.
M1 — Accounts/demo, catalog/enrollment, telemetry, aggregation, tariff and core screens.
M2 — Category-aware insights, explanations, feedback, in-app notices and optional push adapter.
M3 — Recovery/accessibility/usability iteration and core acceptance verification.
M4 — Optional AC module only after M3; live hardware spike remains separately gated.
M5 — Reproducible runbook, status report and handoff.

Tier A done:
- React Native/Expo source runs in the tested mobile environment; state which Android/iOS executions were actually performed.
- Server stack starts reproducibly; migration/seed/reset/run commands documented.
- Four-category demo and P01–P05 work without paid services/hardware.
- Important calculation, ownership, data-quality, category and navigation checks pass.
- UI is Indonesian, understandable and aligned with UX-01–UX-12.
- Source/API/configuration/runbook are complete; no real secrets.
- Status report separates tested, simulated, implemented-unverified, blocked and not run.

Live monitoring additionally requires a real configured Shelly and physical sample validation. Live optional control requires separate provider/AC/sensor tests. No publication, store submission, hardware purchases or public production deployment is part of this documentation task or automatic implementation scope.

## 17. Reference documentation and uncertainty

Implementation choices are specification decisions. Verify exact SDK versions and vendor behavior during implementation rather than pinning assumptions from historical discussion.

| Reference | Use |
|---|---|
| https://docs.expo.dev/ | Shared JavaScript/TypeScript native application development |
| https://reactnative.dev/docs/getting-started | Native mobile component/runtime guidance |
| https://docs.expo.dev/versions/latest/sdk/securestore/ | Native storage adapter for session secrets |
| https://docs.expo.dev/versions/latest/sdk/notifications/ | Platform/build-specific notification integration |
| https://shelly-api-docs.shelly.cloud/gen2/Devices/Gen3/ShellyPlugPMG3/ | Selected meter model and available components |
| https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/PM1/ | Measurement API and field normalization |
| https://developer.tuya.com/en/docs/cloud/ir-control-hub-open-service?id=Kb3oe2mk8ya72 | Optional IR-service integration |
| https://faq.bardi.co.id/Faq/search/0 | Historical BARDI integration guidance to verify |
| https://pureportal.strath.ac.uk/en/datasets/plegma-dataset/ | Research dataset candidate; inspect license/schema |
| https://doi.org/10.6084/m9.figshare.23686476 | CN-OBEE research candidate; inspect actual suitability |

The Expo overview, SecureStore, Notifications and selected Shelly model pages were consulted when preparing v3. This is documentation review, not device testing or proof of SDK behavior on a project build. Older price/trial/dataset statements in the context are historical leads, not current purchase/entitlement guarantees.


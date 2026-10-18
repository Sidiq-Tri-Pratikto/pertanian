# HematRumah — Claude Design Context and Execution Plan
## Version 3.0: an easy-to-use, playable mobile experience

Date: October 18, 2026. Development language: English. Product UI: Indonesian.
This new standalone file includes the design plan, full consolidated product context, and the complete v3 PRD.
Read this plan, Appendix A and Appendix B before building. Do not require the other two files.

## 1. Outcome and priority

Build a polished, interactive mobile prototype for household electricity monitoring and useful recommendations across appliances. A meter alone provides the core experience. A read-only recommendation is a complete outcome.

The main design must feel simple to a resident who knows nothing about electricity integrations. Show what matters first: selected-period energy/estimated cost, contributing devices and a clear explanation of a relevant observation.

Implement the target experience of a React Native + Expo application. Prefer a native-capable preview if available. If the tool supports only browser React, build a phone-oriented interactive simulation and state that limitation. Keep layouts/components transferable to React Native. A browser runtime does not make a desktop website/PWA the product target.

Deliver working interactions, not a mood board, slideshow or disconnected screens.

## 2. Locked scope

Required: P01–P05, S01–S10 as relevant to those journeys, FR-01–FR-11 and UX-01–UX-12 in the embedded PRD.

Three bottom tabs only: Beranda / Perangkat / Saran.
Profile/settings is secondary. No desktop sidebar, central chatbot, dense analytics console, prominent AC remote or mandatory controller flow.

Use TV, refrigerator, computer and AC as ordinary monitored loads. Shelly Plug PM Gen3 is the initial meter; TP-Link is coming soon.

AC control, arrival preparation and three-reminder auto-OFF remain an optional secondary module. Default this design iteration to the core experience; include at most a quiet optional entry in AC details, hidden or disabled until explicitly selected in a secondary demo scenario. A missing controller is not an error badge on Home.

Schedules, tariff, weather, notifications, city and controller setup are optional. Keep the UI Indonesian, including all errors, evidence labels, empty states and permission explanations.

## 3. Visual and interaction direction

Use a calm, readable mobile utility design. Give the overview breathing space and a clear reading order. Prefer familiar named icons and short labels over decorative illustrations or technical jargon.

Starting design tokens, subject to contrast/layout verification:
- Light neutral background with high-contrast dark text.
- One restrained brand accent for the primary action and selected navigation.
- Distinct success/warning/error treatment, always paired with text/icon.
- A small spacing scale, consistent radii, 48-unit minimum touch areas.
- Body text around 16 logical units; captions used sparingly, not for essential data.
- A plain bar/line chart with a text summary rather than complex dashboards.

A card's tappable purpose should be obvious. Do not stack many equal-weight CTAs. Avoid nested clickable regions that accidentally open a device when the user tries to change a setting. Use a sheet for a short choice, a screen for a complete task, and a dialog only for a necessary confirmation.

Support one-hand use, safe areas and vertical scrolling. Verify 360/390/430 widths, a small-height phone, long Indonesian names, keyboard avoidance and approximately 200% font scaling. No hover-only action.

Each task must have visible feedback and a sensible escape/back path. Preserve input and context. When a simulated save completes, say so; when it fails, retain the form and offer a meaningful retry.

## 4. Screen-by-screen contract

| Screen | First things the resident sees | Behavior |
|---|---|---|
| Welcome | Brief benefit, “Mulai”, “Coba demo” | Demo works immediately and stays labeled |
| Empty Home | Explanation of adding a meter | Add-device CTA; no fake zero bill |
| Home | Period + monitored cost/energy, simple contribution preview, one insight | Period changes all linked data; device/insight opens in ≤3 taps |
| Devices | Familiar appliance names, category/icon, energy/cost and data status | Open detail; add another device |
| Setup: brand/model | Shelly enabled; TP-Link “Segera hadir”; monitoring capability | Coming-soon notice returns to choices without losing progress |
| Setup: connection | Plain guidance; waiting/retry/success | Never “connected” until simulated valid first reading |
| Setup: name/category | Examples across categories; sensible input labels | Back/retry preserves values; no AC default for all appliances |
| Device detail | Selected-period summary, simple history, related insight | Technical data secondary; no OFF for monitoring-only devices |
| Suggestions | Observations in plain language | Open evidence; empty/learning state useful |
| Insight detail | What changed, comparison, coverage/limitation, optional advice | Useful/not relevant/dismiss/snooze optional; no mandatory actuator |
| Settings | Tariff and notification preferences, account | Skippable tariff; denied notifications do not interrupt core |
| Device settings | Name/category, meter info, remove | Confirm removal and show meaningful state change |

The optional AC module is not a substitute for an operational core screen.

## 5. Stateful prototype implementation

Use a single shared data store and virtual clock. Cards, totals, charts, explanation percentages, device status and unread counts must agree. Do not independently hardcode each screen.

Minimum state includes:
- demo mode and current scenario;
- selected period and virtual now;
- catalog, enrollment draft/status, appliances/bindings;
- reading/aggregate fixtures and freshness/coverage;
- tariff, recommendations and feedback/snooze;
- cached/offline/permission state;
- tab and navigation history.

Use the canonical numerical fixtures from PRD section 14. Generate reconciled chart buckets. The primary populated scenario has four devices, week energy 30.0 kWh and estimated cost Rp45.000 with a synthetic Rp1.500/kWh tariff. Missing tariff is unknown cost, not Rp0.

Provide a discreet “Skenario demo” entry and reset control outside normal product navigation. It can open a tester sheet. Do not expose debug JSON, simulated broker settings or virtual-time jargon inside ordinary product tasks.

Scenario changes update the shared state atomically. Scenario reset restores the documented starting point. Avoid long real waits; explicit tester controls may advance virtual time or complete simulated connection.

Every primary visible action must work. Secondary technical/support links can open an explanatory sheet if their external destination is outside the prototype, but label that honestly. No empty click handlers disguised as finished behavior.

## 6. Playable journeys and verification

| Flow | Start and actions | Required outcome |
|---|---|---|
| P01 | Demo → empty Home → add Shelly → connection → TV name/category → success; go back once and retry once | First-use flow is understandable and preserves inputs |
| P02 | Populated Home → this week → highest contributor → history; switch today/week | Values reconcile and context is retained |
| P03 | Saran → refrigerator insight → evidence and practical suggestion | Read-only value, matched comparison, no turn-off CTA |
| P04 | TV insight → useful/not relevant → dismiss/snooze → return | Feedback persists across screens, does not erase history |
| P05 | Toggle cold start, no tariff, stale meter, partial coverage, denied notifications and retry | Clear explanation, cached/unknown values treated honestly |
| P06, optional | Explicit secondary AC scenario | If included, follow conditional FR-12–FR-14; never block P01–P05 |

For P01, a newly added TV can coexist with the seeded “TV Ruang Tamu”; avoid accidental name/ID duplication in the standard fixture. Use an empty scenario for first-device onboarding and populated fixtures for comparison tasks. Name duplication by the user is permitted if IDs remain distinct.

Validate all tab/back paths, scrolling, keyboard submission, modal dismissal, focus order and reset. If a browser preview cannot reproduce native back/keyboard behavior, document that limitation and still implement the equivalent visible behavior.

## 7. Copy requirements and examples

Use these as seeds, adapting to actual scenario data:

| State | Example Indonesian copy |
|---|---|
| Overview | “Estimasi biaya perangkat dipantau” |
| Monitoring scope | “Ringkasan ini hanya mencakup perangkat yang terhubung.” |
| No tariff | “Tambahkan tarif untuk melihat estimasi biaya.” |
| Learning | “Sedang mempelajari pola penggunaan. Pemakaian yang tercatat tetap bisa dilihat.” |
| Stale meter | “Data meter belum diperbarui. Terakhir diterima pukul 20.45.” |
| Partial period | “Sebagian data belum tersedia. Angka ini mencakup data yang berhasil dicatat.” |
| First-reading wait | “Menunggu data pertama dari meter.” |
| Retry | “Belum berhasil terhubung. Periksa koneksi meter, lalu coba lagi.” |
| Refrigerator insight | “Konsumsi Kulkas Dapur naik 20% dibanding periode pembanding.” |
| Limitation | “Data listrik belum dapat menjelaskan penyebab perubahan ini.” |
| Optional feedback | “Bermanfaat” / “Kurang sesuai” |
| Simulated mode | “Demo · Data simulasi” |

Never show “Perangkat mati” merely because the meter is offline. Do not claim “hemat RpX”, an equipment fault, a room's occupancy or measured comfort unless actual supporting data is present. No literal vendor error codes in core copy.

Tips without personalized evidence say “Saran umum”. Display comparison dates/coverage accessibly; do not hide every limitation behind a tooltip.

## 8. Usability and accessibility review

Apply every UX-01–UX-12 check in the PRD. Provide a short results table with pass/fail/not tested and observed limitations.

Walk through with a keyboard and available screen-reader/accessibility tooling; test font scaling and contrast. A chart must have a readable text equivalent. Navigation and state must not depend on color. Motion is subtle and respects reduced-motion where supported.

Prepare the five-participant neutral test from the PRD. If no participants are available, provide the script and a pending research status. Never invent a 4/5 result or claim user-friendliness has been validated from visual polish alone.

Fix task-blocking issues before adding decoration or optional screens. Proposed refinements must stay within the monitoring/recommendation scope.

## 9. Execution plan

D0 — Read the entire handoff; extract scope, navigation and main tasks. Resolve routine design choices without expanding scope.
D1 — Define tokens, components, phone shell, screen map and shared fixture/state.
D2 — Build Home, Devices, device detail, Suggestions and insight detail.
D3 — Build first-use/enrollment, settings and feedback. Complete back/retry/period behavior.
D4 — Add state scenarios and shared virtual-time controls; verify consistency.
D5 — Audit accessibility, language and task simplicity; fix P01–P05 and UX issues.
D6 — Deliver the playable artifact and handoff notes. Only then consider an optional secondary AC preview if requested.

Do not stop after D0/D1 or ask for approval merely to proceed with reversible design work.

## 10. Required deliverables

- A playable artifact/preview and its source as supported by the tool.
- A screen map and concise component/token specification.
- A 3–5 minute walkthrough focused on P01–P05 and multiple appliances.
- A state/interaction verification checklist with actual results.
- A usability test script; actual study findings only if observed.
- React Native implementation notes: hierarchy, navigation, data/state, labels and remaining runtime limitations.
- Explicit status: simulated data/actions; no hardware or live usability claim.

Do not buy hardware, request vendor credentials, call live actuators, publish a site or submit an app. This is a design prototype.

## 11. Ready-to-run prompt

Copy the following prompt and attach this file.

~~~text
Read this entire v3 handoff, including the consolidated conversation context and full PRD. Treat the latest mobile/product corrections as binding.

Build a polished, interactive, playable MOBILE prototype of HematRumah. The intended implementation is React Native + Expo + TypeScript for Android/iOS. If your runtime only runs browser React, create an honest phone-oriented design simulation with native-friendly patterns.

The core is monitoring electricity and reading useful evidence-based recommendations across TV, refrigerator, computer and AC. Meter-only use must be complete. AC controls, arrival planning and auto-OFF are optional secondary extensions and must not dominate this iteration.

Use Beranda, Perangkat and Saran as the only main tabs. Keep all product copy Indonesian. Implement P01–P05, the specified screens and UX-01–UX-12 with working navigation, periods, onboarding, feedback, back, retry and settings. Schedules, tariff, weather, notifications and controller setup are optional.

Use the canonical fixtures and one shared store/virtual clock. Totals, costs, charts and evidence must reconcile. Clearly label simulation. Include empty, learning, no-tariff, offline, partial-data, denied-notification and connection-error states. No dead primary buttons, fake whole-house bills, missing-as-zero data or refrigerator turn-off recommendations.

Continue until the core prototype can be played. Verify the task paths, narrow screens, large text, safe areas and recovery states; fix problems. Deliver the playable artifact, source where supported, screen map, tokens/components, short walkthrough, results checklist, usability-test script and React Native handoff. State what was not tested. Do not operate hardware, publish or add further enhancements.
~~~

---

# Appendix A — Consolidated conversation context and decision history

## A1. Purpose and limits

This is a comprehensive development-oriented reconstruction of the product conversation available in the source files and the user's latest corrections. It preserves the substantive requests, decisions, examples and unresolved dependencies; it is not a verbatim export of every chat message or web search. Unrelated personal information and operational chat/tool details are excluded.

The active requirements are the v3 plan and embedded v3 PRD. Historical options below are explanatory records. Each topic states its current disposition so an implementation agent does not revive superseded requirements. No historical discussion establishes physical hardware testing.

## A2. Original problem and household focus

The idea began with IdleWatch: finding electricity use outside operational needs, initially discussed for industry. The user asked to explore individuals separately: a meter between socket and appliance, measurements flowing into software, and understandable saving recommendations.

The user emphasized software as the main solution and affordable, available supporting hardware. AC was initially an example, with weather/outdoor temperature considered as context. The user wanted simple stories and advice based on data actually available, because residents may not understand electricity.

Current decision: the product is for household/individual use. Multiple appliance categories are core now; AC is one category. Enterprise/industrial management and industrial models are outside this release.

## A3. Understanding household meter data

The user asked for concrete datasets and examples of what a home watt meter produces. Discussion distinguished timestamp/device identity, instantaneous power and cumulative energy.

Historical arithmetic example: a valid cumulative counter increase from 100,000 Wh to 104,000 Wh indicates 4 kWh across that interval if no reset occurred. A single instantaneous watt reading is not the energy consumed overnight.

Plegma and CN-OBEE were proposed as research leads, with HIPE as an industrial comparison. They are not proof that an industrial model transfers to a home, and are not prevalidated project training data. Inspect schema, license, channels and relevant context before replay/training.

Current decision: support normalized power/energy time series, honest coverage and reset handling. Synthetic data is sufficient for initial development. Dataset replay has its own provenance and is not live hardware.

## A4. Accessible hardware and collection path

The user wanted meters available in Indonesia, affordable for individuals, and a clear path from appliance measurement to the phone. Historical candidates included Tapo P110, Shelly Plug PM Gen3 and Shelly EM Mini Gen4 for fixed wiring.

Historical price examples were approximately Rp159–166 thousand for Tapo, Rp419 thousand for Plug PM Gen3, and Rp359 thousand for EM Mini Gen4 before installation. These are archived research examples, not current prices, stock, purchasing recommendations or purchase authorization.

A historical public Tapo P110M log example contained current_power=5330, today_energy=78 and month_energy=3712. In that discussed endpoint, power was interpreted as mW and energy as Wh; the connected appliance was unspecified. It is not a project AC reading. Recheck units per actual API/firmware.

Shelly was chosen as the reference because of documented integration options. The proposed route uses direct outbound meter-to-server telemetry so the phone does not stay online as a collector.

Current decision: first meter target is Shelly Plug PM Gen3. TP-Link appears as coming soon; no live TP-Link work in Tier A. Do not claim affordability, load compatibility or live connectivity has been physically validated.

## A5. Plug-and-play clarification

The user asked whether meters could be inserted without dismantling a socket. Plug-in models were distinguished from fixed-wiring modules. A suitable plug/socket/load combination still needs initial Wi-Fi/integration configuration; a hardwired AC is not automatically suitable for a plug meter.

Current decision: use a plug-in meter pilot with actual model/load suitability checked. No DIY mains rewiring flow, hardware purchase, or technician-work simulation. Consumer onboarding must be simple and honest about pilot assistance.

## A6. Shelly API and meaning of “public”

The user selected Plug PM Gen3 as an example and asked whether its API was public. Discussion explained that public API documentation does not expose the user's device as a public internet endpoint.

Local PM1 measurement fields were discussed: apower in W, voltage in V, current in A and aenergy.total in Wh. Exact envelopes, time fields and firmware behavior must be checked during implementation. Proposed remote path: meter → authenticated MQTT/TLS broker → backend → mobile app.

Current decision: normalize actual source fields in an adapter. Do not put meter/cloud credentials in the app or expose home devices through router port forwarding. A developer-assisted pilot configuration is acceptable when clearly described.

## A7. Initial stack and technical explanation

The user requested a technical overview. An earlier proposal used Next.js/PWA, FastAPI, PostgreSQL, Mosquitto and a Python worker, with optional weather, ML and Tuya. Approximately 60-second sampling was a configurable engineering target, not a factory guarantee. Missing data, duplicate/reset handling and reproducible simulation were already important.

The early one-AC demo simplified discussion. It is not the current data-model or product limit. “Saving experiments” appeared as an idea; v3 does not require a separate experiments product feature.

Current decision: React Native + Expo replaces the web/PWA frontend. FastAPI/PostgreSQL/MQTT/worker remain the server approach. Multiple appliance profiles are required. Backend collection continues when the phone is closed.

## A8. Catalog order and recommendation method

The user explicitly requested brand → model → connection → appliance name, with Shelly enabled and TP-Link visible. The user also asked whether recommendations would use AI/ML.

Discussion proposed a hybrid: deterministic energy/cost math, statistical patterns and rules, optional regression such as Ridge, and understandable explanations. An LLM was never required to calculate electricity or allowed to independently operate hardware.

Current decision: add appliance category to naming, use category-aware baselines, preserve the ordered catalog flow and coming-soon behavior. Statistics/observations deliver core value; optional ML requires enough data and honest evaluation. Read-only advice is complete without any actuator.

## A9. User's four AC interaction requests

The user explored:
1. Whether the device could disconnect electricity/turn equipment off.
2. An arrival scenario: an explicit request to prepare a cool room before coming home, with timing learned from data.
3. Optional schedules rather than mandatory schedule input.
4. A neutral prompt when AC use is longer than usual, with opt-in automatic handling after three unanswered alerts.

The suggested prompt was: “Penggunaan Perangkat AC Kamar Depan lebih lama dari biasanya. Apakah kamar masih dipakai?”

Current disposition:
- Optional schedules remain a core principle.
- Meter data learns patterns, not occupancy.
- AC control, arrival planning and automatic remote-OFF are Tier B extensions.
- These do not determine core navigation, enrollment, main demo or success.
- A refrigerator must never inherit the AC duration/OFF rule.

## A10. Power supply versus AC ON/OFF

The user clarified that an arrival scenario needs real AC ON capability, and asked whether a meter can do it.

Discussion distinguished measuring power, switching mains and sending an AC command. Plug PM Gen3 is monitoring-only. Shelly Plug M Gen3 was an example of a different relay-equipped model; it did not replace the selected meter. Restoring supply does not guarantee the AC starts cooling.

Current decision: meter/controller/sensor are separate. Effective capabilities depend on model, supported integration and tests. No mains disconnection is offered for the selected configuration. Do not advertise a switch because a meter appears online.

## A11. Indonesian universal controller candidates

The user asked for a controller that could work with many ACs sold in Indonesia. Smart IR controllers were discussed, including BARDI with temperature/humidity, BroadLink RM4 Mini and Sensibo Air, with SwitchBot as another API example.

Historical price leads: BARDI with sensors about Rp314 thousand, without sensors Rp178 thousand; one BroadLink package about Rp732,400 on preorder; Sensibo about Rp2.2 million. These are historical, unverified purchase leads. No percentage proving coverage of a majority of Indonesian AC models was established.

Current decision: BARDI/Tuya is only an optional integration candidate. Actual AC/remote compatibility, ON/OFF/setpoint, sensor access, availability and cost need separate tests. Alternative providers are research context, not implementation requirements.

## A12. BARDI and Tuya integration

The user asked if the app can directly call a BARDI API. Historical research did not establish a BARDI-specific public API; its guidance pointed toward Tuya.

Target optional path: app → our backend → Tuya Cloud API → BARDI → infrared → AC. Credentials remain server-side. Candidate endpoint discussed:
POST /v2.0/infrareds/{infrared_id}/air-conditioners/{remote_id}/command

Current decision: verify the exact endpoint, account route, regional data center, IR service entitlement and payload using current official docs and the actual hardware. Do not assume BARDI OEM credentials link like Smart Life. Provider success means accepted request, not confirmed infrared reception. Room sensor readability is an independent gate.

## A13. Tuya trial and prototype architecture

The user asked whether BARDI plus Tuya trial was suitable for initial testing and requested the full architecture. Historical documentation examples mentioned trial limits of up to 50 connected and 10 controllable devices.

Current decision: those figures are historical leads, not v3 guarantees. Validate actual eligibility, quota, expiry and IR entitlement in the selected account/console only if Tier B is pursued. A trial does not prove every required service is available.

Shelly telemetry bypasses Tuya. Simulator development and core completion need no Tuya account. No project hardware, cloud account or service entitlement has been demonstrated by this conversation.

## A14. Reliability learned from the optional scenarios

Discussion introduced persisted plans, action expiry, idempotency, cancellation, confirmation, countdown, offline guards and a shared virtual clock.

Current decision: retain core identity/data integrity/retry requirements. Apply physical-action safeguards only to the optional module:
- Three ignored reminders must belong to one incident and actually have receipt evidence.
- Failed/unknown notification delivery is not user neglect.
- Manual response/override, stale data, ended sessions and disabled policy stop escalation.
- Remote OFF is not mains cutoff.
- Post-dispatch uncertainty is not a reason to blindly repeat an IR toggle.
- Fresh temperature evidence is required to verify room comfort.
- Restart delay is appliance-specific, not a universal constant from one brand.

These are conditional requirements, not an instruction to implement Tier B before the monitoring MVP.

## A15. Original document request

The user requested three files:
1. Full detailed PRD, limited to agreed features with other ideas under further enhancements.
2. Full consolidated context plus a plan for Claude Design.
3. Full consolidated context plus a distinct plan for Claude Code.

The user expected a playable design mockup, not screenshots, and asked for ready-to-use prompts. Handoffs must be independently usable and include a complete current PRD so only one file needs to be forwarded.

Current decision: exactly three new Markdown files with purpose-specific plans, shared context and identical v3 PRD snapshots in the two handoffs. This document task does not build or publish the application.

## A16. English development edition

The user requested English versions of every file and prompts for both execution tools.

Current decision: all development prose/prompts are English; actual app copy remains Indonesian. Common product labels are Beranda, Perangkat and Saran. UI failures/loading/permissions/explanations must also use Indonesian, not just the happy-path screens.

## A17. Explicit product correction after the mockup

The user observed that the generated mockup was too focused on web apps and on AC. The user expected a simpler React-based mobile app without separately developing Android and iOS.

The user clarified that AC ON/OFF is an additional feature. The central product monitors electricity through meters such as Shelly and recommends improvements; a recommendation need not trigger any action.

Current decision: React Native + Expo + TypeScript, three-tab mobile architecture, multiple appliance categories in the main experience, monitoring-only enrollment, and read-only recommendations as first-class outcomes. Browser preview is only a runtime accommodation for design. The implementation deliverable is native mobile source.

## A18. Latest UX emphasis and new-file request

The user explicitly wants a design that is easy to operate with good UI/UX and requested new files. This follows an earlier all-file revision request.

Current decision: create separate v3 deliverables; retain older files as historical artifacts. Use concrete UX-01–UX-12 requirements, P01–P05 core journeys, state/recovery behavior, accessible layouts, consistent synthetic data and a participant-study script. Do not merely add “user-friendly” to an old web/AC specification.

## A19. Open questions resolved as development assumptions

No additional product clarification is needed before building the core simulator:
- Product name remains a working name.
- Proposed collection/freshness/readiness thresholds are configurable pilot assumptions.
- Core demo uses four named appliance categories and synthetic data.
- Tariff is optional manual input, not an official default.
- Live meter provisioning can be pilot-assisted.
- Native build/push testing depends on available devices/tooling; report exactly what ran.
- Real model usefulness, compatibility and savings require a later local pilot.

Unresolved external dependencies are not permission to fabricate live results or to stop at scaffolding. Complete the design/core simulation and document the unmet live prerequisites.


---
# Appendix B — Complete current PRD, version 3.0

<!-- BEGIN CURRENT PRD SNAPSHOT v3.0 -->
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

<!-- END CURRENT PRD SNAPSHOT v3.0 -->


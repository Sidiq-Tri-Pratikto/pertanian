# TemuRiset prototype: design handoff

Stage 2 of the TemuRiset package. This is a stateful front-end simulation built from [02_Claude_Design_TemuRiset_EN.md](../02_Claude_Design_TemuRiset_EN.md) and PRD v1.1, using TemuRiset Design System 1.0.0-draft.

| Item | Value |
|---|---|
| Playable canvas | https://claude.ai/artifact/HMXtf8NFdYuhEjeKoq9ekJ (private). App files are at version 15, id `1793456672-6c1d`; later versions add only this document and `binding.json` |
| Source | `docs/generic/temuriset/app-prototype/project/` |
| Interface language | Indonesian |
| Binding record | [binding.json](binding.json) |
| Service oracles | [tools/domain.test.mjs](tools/domain.test.mjs), 39 of 39 pass |
| Rendered journey walker | [tools/journeys.browser.js](tools/journeys.browser.js), 155 of 155 pass on the local harness |
| Hosted editor Play | **BLOCKED**, see section 10 |

Nothing here proves production authorization, atomic booking, malware scanning, funding or accessibility conformance. All AC01 to AC72 production scenarios remain **NOT RUN**.

## 1. How it is built

- `Main.dc.html` is the playable artboard. It imports one artboard per screen and holds no state of its own.
- `domain.js` is the one service and state authority. Every mutation takes acting party, expected version and idempotency key.
- `views.js` holds hash routing, form state and one view model per screen. Screens read view models and never copy fixture text.
- Each `.dc.html` is markup only, and also renders alone on the canvas from a scripted preview state.

## 2. Running it

Service oracles:

```bash
node docs/generic/temuriset/app-prototype/tools/domain.test.mjs
```

Local source export. `.harness/` is gitignored. It needs the canvas runtime, which comes from the Design artifact type (`artifact-type/dc-runtime.js`, sha256 `b795ee21…`), saved as `.harness/project/support.js`.

```bash
cd docs/generic/temuriset/app-prototype
mkdir -p .harness/project/ds/temuriset/components
cp ../design-system/workbench/tokens.css .harness/project/ds/temuriset/
cp ../design-system/project/components/bundle.css ../design-system/project/components/bundle.js .harness/project/ds/temuriset/components/
cp project/*.dc.html project/*.js tools/journeys.browser.js .harness/project/
```

Then start `temuriset-prototype` from `.claude/launch.json` and open `http://localhost:8789/project/Main.dc.html`.

To repeat the rendered walk, load `journeys.browser.js` in that page, then run `await walk()`. `walkHelpers.audit()` checks overflow, `walkHelpers.a11y()` scans names, contrast and targets, and `walkHelpers.boards()` opens every artboard alone.

## 3. Routes and screens

The prototype uses hash routes because it runs inside a canvas. Each maps to the intended web route without the `#`.

| Screen | Hash route | Artboard | View model | FR | Main states |
|---|---|---|---|---|---|
| S01 Identity | `#/start` | Start | `vm.start` | 01, 02 | Persona choice, labelled demo account, zone |
| S02 Home | `#/home` | Home | `vm.home` | 10, 16 | Action queue, empty state, notifications |
| S03 Discovery | `#/discover?type=` | Discover | `vm.discover` | 08, 10 | Inventions, funding, partners, filters, empty |
| Inovasi Saya | `#/inventions` | Inventions | `vm.inventions` | 03 | Published, drafts, empty |
| S04 Detail | `#/inventions/:id` | Invention | `vm.invention` | 03–06, 19 | Owner, partner, unavailable |
| S05 Editor | `#/inventions/:id/edit?step=1..4` | Editor | `vm.editor` | 03–06 | Saved, unsaved, failed, conflict, upload axes, preview |
| S06 Support | `#/support-requests`, `/:id`, `/new` | Support | `vm.support` | 06 | List, gap, validation, noncash, activate |
| S07 Funding | `#/funding-requests/:id`, `/edit` | Funding | `vm.funding` | 07 | Read, edit, proposed entity, capability off |
| S08 Partner | `#/partners/:id` | Partner | `vm.partner` | 08, 09 | Own or other, external route, unconfirmed intake |
| S09 Mandate | `#/opportunities/:id/edit` | Opportunity | `vm.opportunity` | 09 | Edit, review, activate |
| S10 Matches | `#/matches?source=` | Matches | `vm.matches` | 11 | Loading, reasons, gap, excluded, abstain, external |
| S11 Preflight | `#/pitches/new?source=&target=` | Preflight | `vm.preflight` | 12, 13 | Ready, blocked, stale, lost response, duplicate, closed, AI off/down |
| S12 Lists | `#/pitches?box=` | Pitches | `vm.pitches` | 13–16 | Filters kept, empty, whose turn |
| S13 Workspace | `#/pitches/:id?tab=` | Workspace, Revisions | `vm.workspace`, `vm.revisions` | 14–16 | Decide, revise, documents, discussion, history, denied |
| S14 Schedule | `#/pitches/:id?tab=jadwal` | Schedule | `vm.schedule` | 17 | Propose, choose, conflict, expired, confirmed, replacement, outcome |
| S15 Relationship | `#/partnerships/:id`, `/new?pitch=` | Partnership | `vm.partnership` | 18, 19 | Propose, confirm, correct, restrict, contest |
| S16 Public profile | `#/profiles/:id` | Profile | `vm.profile` | 04, 19 | Published fields, consented fields only |
| S17 Review | `#/workspace/review-queue` | ReviewQueue | `vm.review` | 20 | Unavailable, empty, queued |
| S18 Settings | `#/settings` | Settings | `vm.settings` | 02, 22 | Preferences, report, privacy request |

FR21 (import/export), FR23 and FR24 have no screens. FR23 appears only as the composition switches in demo controls.

## 4. Components and tokens

All 26 contracted components plus NextStep, Steps, SummaryList and Screen are mounted as the real `window.TR` bundle. Icon is used through them. Colour comes only from `TR` components, type and layout classes (`tr-panel`, `tr-stack`, `tr-grid`, `tr-row`, `tr-section`, `tr-muted`, `tr-sys-type-*`) and one direct token, `--tr-sys-color-canvas`. No raw colour is authored in markup.

Deviations D1 to D5 are recorded in `binding.json`. The one that matters most is **D1**: `TemuRisetApp.Slotted` passes marked child elements into node props, because canvas markup can only supply children. It draws nothing, but it is a global the canvas instructions discourage. Everything it wraps stays real `TR` components and editable markup.

## 5. Service contract

Results are `{ ok: true, … }` or `{ ok: false, code, message, fields?, retryable?, unknown? }`.

| Code | Meaning in the prototype |
|---|---|
| `VALIDATION` | Field errors, nothing changed |
| `STALE_VERSION` | Expected version differs, local input kept |
| `IDEMPOTENCY_CONFLICT` | Same key with different content |
| `DUPLICATE` | Active pitch already exists, returns `pitchId` |
| `BOOKING_CONFLICT` | Half-open overlap for a required participant |
| `LOST_RESPONSE` | Committed, response dropped. Retry with the same key replays the result |
| `NETWORK` | Failed before commit |
| `NOT_FOUND` | Unrelated actor. No metadata returned |
| `FORBIDDEN` | Member lacks the capability |
| `CAPABILITY_UNAVAILABLE` | Disabled composition |

Matching follows PRD section 10. Results keep eligibility, readiness, score bounds and coverage separate, and a target with no topic overlap abstains even when its rules pass.

## 6. Fixtures, variants, clock and reset

F01 to F06, FRaise01 and Recipients A to D are the handoff fixtures. A2, A3, B2 and Recipient E were added and are listed in `binding.json`. All data is fictional, and amounts stay decimal strings with no conversion, valuation or derived percentage.

Demo controls sit in the collapsed panel above the app, labelled as not part of the product.

| Control | Effect |
|---|---|
| J01 to J05, DIRECT-APPROVAL, SCHED-72H, F01-DENIED, Akun kosong | Restores baseline, replays service calls to that point |
| F01-GAP, F01-SCAN, proposed entity | Variant, shown in the panel summary |
| F01-STALE, draft edit from another session | Bumps a version on demand |
| F01-TIMEOUT, failed draft save, failed slot confirmation | One-time fault |
| Organization review, calendar adapter, company funding, summarizer | Composition switches |
| Clock presets | Starts at 2 November 2026 08:00 UTC. Machine time is never used |
| Akun demo | Changes actor only, the case stays |
| Atur ulang demo | Removes `temuriset-demo-v1` from this browser and restores baseline |

State persists in `localStorage` for the Main artboard only. There is no cross-device sync.

Walking the main chain by hand: J01 needs Rani, then Mitra A. After approval, propose slots as Mitra A, pick 09:00 as Rani to hit the conflict, propose alternatives, and confirm 10:00 as Mitra A. Set the clock to 4 Nov 12.00, record the outcome as both parties, then propose the relationship.

## 7. Responsive decisions

- Below 48 rem the DS tab bar shows four destinations plus Lainnya. Above it, the top navigation shows all five.
- Scheduling is a workspace tab and relationships open from the pitch, so neither adds a destination.
- Grids use the DS `tr-grid` auto-fit rule, and all screens read as one column.

## 8. Mock versus server

| Behavior | Prototype shows | Production still needs |
|---|---|---|
| Persona and context | Navigation and selected fictional party | Real authentication, membership and session enforcement |
| Private files and grants | Selected-version UI, denial and redaction | Gateway authorization, storage policy, secure download |
| Upload, security, extraction | Independent status axes on timers | Real validation, quarantine, malware handling, parsing limits |
| Matching and brief | Deterministic reasons and template | Corpus permissions, ranking benchmark, model validation |
| Submission, retry, version | Shared service result, retained intent | Database idempotency, constraints, audit and outbox |
| Booking | Conflict and replacement UX in one thread | Race-safe booking across participants |
| Email and calendar | Honest unavailable state, internal slots, ICS | Approved provider and delivery tests |
| Relationship | Same-version consent intersection and projection | Server authority, identity, agreement procedures |
| Deletion and reporting | Request acknowledgement | Retention, holds, backups, operator handling |

Everything here ships in one browser bundle, so the fictional private text is present on the client. Denial screens demonstrate policy, not confidentiality.

## 9. Export inventory

| Output | Status |
|---|---|
| Playable canvas | Published, private |
| Source (`project/`) | In the repository, uncommitted |
| Interactive source run outside the editor | Harness, PASS |
| Canvas Share or Export formats | BLOCKED, page not reachable from this session |
| Next.js build | Not produced and not claimed |

## 10. Validation results

Surface for all harness results: `project/` at canvas version 15 served from 127.0.0.1:8789 with the same runtime file the artifact type publishes, in the desktop Browser pane, on 31 October 2026. Checks use synthetic data. Simulation is provenance only, so PASS below means the UI expectation held on that surface.

| ID | Result | Evidence |
|---|---|---|
| UX-01 | PASS | Rani and Investor B work with no organization; persona switch walked |
| UX-02 | PASS | Acting party shown on preflight, decision, slot confirmation and relationship |
| UX-03 | PASS | Failed save keeps values, retry, stale conflict, step navigation |
| UX-04 | PASS | Saat ini and Direncanakan on detail, editor, workspace and brief; "Disediakan, belum diperiksa" shown |
| UX-05 | PASS | Target and contribution labelled separately with currency, period and scope |
| UX-06 | PASS | One funding card, second link reaches existing pitch |
| UX-07 | PASS | Reasons, visible gap, score behind Disclosure, stated as not a probability |
| UX-08 | PASS | Recipient, versions, files and send effect shown before commit; file must be chosen |
| UX-09 | PASS | Error summary receives focus, values retained |
| UX-10 | PASS | F01-SCAN and rejected upload show independent axes |
| UX-11 | PASS | Required gate, honest inability, failed upload keeps answers, prior submission retained |
| UX-12 | PASS | Whose-turn band correct for both parties through all journeys |
| UX-13 | PASS | 16.00 WIB and 17.00 WITA shown; selection labelled unconfirmed; no meeting before confirmation |
| UX-14 | PASS | Conflict, expiry both ways, replacement keeps old meeting until accepted |
| UX-15 | PASS | Correction clears confirmations; one confirmation shows no mutual badge |
| UX-16 | PASS | Amount hidden from public view, narrowing immediate, seen as unrelated user |
| UX-17 | PASS | Stale preflight keeps brief; lost response retry yields one pitch |
| UX-18 | PASS | Review on/off and blocked disable, funding off, summarizer off/down, calendar on/off |
| UX-19 | PASS for samples | Real keys: dialog focus, trap, Escape, return; tab arrows and Home; skip link; form order at 360. Keyboard-only full journeys are **NOT RUN** |
| UX-20 | PASS for text | Rendered text scan on 22 routes, no failures. Control and focus contrast rely on DS token checks; no dedicated rendered measurement here |
| UX-21 | PASS | 25 routes at 320, 360, 768 and 1280 show no page overflow; root text at 200% clean at 320. Browser zoom itself was not used |
| UX-22 | PASS for samples | Labels, duplicate ids, one h1 and 24 px targets clean on 22 routes; all buttons at least 44 px. Screen reader and reduced-motion runs are **NOT RUN** |
| UX-23 | **BLOCKED** for editor Play, PASS for harness | The built-in browser shows the claude.ai sign-in page and credentials must not be entered by the agent. All 22 artboards render on the harness with no console errors |
| UX-24 | PASS | `binding.json` and this file |

Hosted evidence is limited to publish results: all files stored, and DS byte counts match the repository. Rendering on the hosted canvas was never observed. It uses a different origin and sandbox, so `location.hash`, `localStorage` and file download there remain unverified, though each is guarded.

The journey suite, overflow, accessibility and standalone-artboard checks all reran on the final code. The real-key samples ran one edit earlier, before two hand-built bands on Preflight and Partnership became `TR.NextStep`; those samples did not touch the bands.

At 320 px the overflow audit flags one element on `home`: the closed body of the demo panel. The page has no horizontal scroll there, and the element is not product UI.

## 11. Defects found and fixed during validation

| Defect | Fix |
|---|---|
| `Object.assign` froze the `state` getter, so reset and presets left readers on stale state | Defined as a live property, regression oracle added |
| Journey presets kept the old hash, so reload could land on the wrong screen | Presets now set the hash |
| Success notice survived an account switch and appeared to the other party | Cleared on account and tab change |
| A target with no topic overlap appeared first with a green check | Abstains into the not-recommended group; green no longer used for computed matches |
| Completed meeting still showed the proposal form and a second primary action | Added a completed panel |
| Counterparty could not accept a replacement proposal | Meeting and slot choice now show together |
| No viewport meta, so narrow screens laid out at 980 px | Added to every artboard. The first 320 and 360 audit was invalid and was rerun |
| "Temukan" broke across lines at 320 px | Local override D2 |

## 12. Known limitations

- Organization review returning a pitch sets WITHDRAWN instead of the previous state.
- The default five-pitches-per-day limit, member invitations, FR21 import/export and operator queues are not implemented.
- Returning from a detail page restores filters but sends focus to the main region, not the original card.
- Loading is shown on Matches and on busy buttons. Other screens render immediately because the service is local.
- Answer review offers accept or ask for detail. A further question needs a new revision round.
- Upload is simulated with timers. No file is read.
- Print uses the browser dialog, and a canvas sandbox may block it.
- The design system is a draft, not owner-approved. D2 should be fixed there.
- No participant sessions were run. All learning goals in PRD section 20 are untouched.

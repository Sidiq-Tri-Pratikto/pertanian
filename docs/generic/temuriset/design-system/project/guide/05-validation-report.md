# Validation report

Release 1.0.0-draft, checks run 31 October 2026 (Asia/Jakarta). Results are PASS, FAIL, NOT RUN or BLOCKED. Every preview uses fictional fixtures ("Demo · Data fiktif") and simulated services; that is provenance, not a result. Token arithmetic, a rendered browser check, an export inspection and a participant session are different evidence, and none stands in for another.

## Test surfaces

| Surface | What it is | Used for |
|---|---|---|
| A. Token build | `node tools/build.mjs` (Node 25.2.1) over `tokens.json`, `bundle.css`, `bundle.js` | Integrity, aliases, computed contrast, raw-value scan |
| B. Local workbench | `workbench/index.html` (frame per preview, width, text and motion controls, audit) and `workbench/frame.html?<Preview>` (one preview at the real viewport), served by `python3 -m http.server` from the same `project/` files | Rendered contrast, targets, overflow, keyboard, focus, status, recovery |
| C. Browser | Claude desktop built-in browser, Chrome 152.0.7977.167 engine, Linux x86_64, viewport emulation 320–1280 CSS px, no assistive technology | Runs B |
| D. Artifact page | The private design-system page on claude.ai | See DS-10 |
| E. Logic script | Node VM run of `bundle.js` with 13 assertions on `TR.format` and `TR.effectiveFields` | Money, zones, half-open intervals, consent intersection |

## Gates

| ID | Gate | Expected | Actual | Result |
|---|---|---|---|---|
| DS-01 | Identity and capability honesty | Real surface, version and mode stated | Claude Code desktop session. `DesignSync` exists but needs the user-started `/design-sync` flow, so it was not used. A private artifact was made from the Design System type. Mode: portable local reference mirrored to that artifact. Registration in a design picker is not verified | PASS |
| DS-02 | Token authority and schema | Complete valid export, no false DTCG claim | Surface A: 0 integrity errors, 104 tokens, every alias resolves, no cycles or duplicates, no raw colours in bundle files, every `var(--…)` defined. Export parses as JSON and declares `temuriset-tokens/1` as custom with a DTCG conversion note. DTCG is not claimed | PASS |
| DS-03 | Rendered colour and focus | Real combinations checked | Surface A: 47 of 48 token pairs meet their minimum; the decorative border fails as intended and is used only between groups. Surface B/C: every visible text node in 37 previews at 320, 320 with 200% text, 360, 768 and 1280 px: 185 runs, 3,115 elements, 0 contrast failures. Focus on a real keyboard return measured a white 2 px gap and `rgb(0,95,204)` 2 px ring. Limit: the audit reads text against the nearest opaque background; icon and ring adjacency rest on the token pairs and on inspection of *Foundations* | PASS |
| DS-04 | Primitive interaction | Anatomy, keyboard, focus, errors, loading, disabled reasons | Real key events: Tab then Enter opens `TR.Dialog`; ArrowRight and End move `TR.Tabs`, selection follows, Tab enters the panel. Busy button exposes `aria-busy`. Disabled reason visible and linked. Each primitive has a preview and usage page | PASS |
| DS-05 | Domain meanings | Financial basis, one raise with two inventions, current/planned and requirement distinctions | P01 script: one funding card, target appears once, contribution once, "2 inovasi terkait". F01 shows CURRENT 10 L/jam and PLANNED 20 L/jam. Three outcomes render "Siap dikirim", "Perlu konfirmasi", "Tidak cocok untuk mitra ini". Surface E: null reads "Belum ditentukan" and explicit zero reads `USD 0` | PASS |
| DS-06 | Focus and recovery | Error summary, dialog containment and return, retained input, status changes | Real keys: invalid step 3 focuses the summary, keeps `-1`, sets `aria-invalid`; following the link focuses the field. Dialog: initial focus on the title, Tab wraps Tutup to the last action and Shift+Tab wraps back, Escape closes without sending and returns focus to the opener. `TR.SaveState` is `role="status"`; a failed save kept the text and retry reached saved | PASS |
| DS-07 | Responsive and larger text | 320 reflow, 360, 768, 1280 and 200% text | 185 runs: 0 horizontal overflow, 0 targets under 24 px, 0 unnamed controls. Under 44 px only text links and the *Foundations* specimen links. 200% text at 320 px is root font-size in the frame. At 360 × 740 with 200% text the tab bar goes static and causes no overflow. Long words such as the page title may break at that size. Focus checked against the sticky bar on P01 and P04 at 360 × 740: only the tab panel, taller than the viewport, overlaps it. A last top-bar layout change, wide screens only, was rechecked on the five `TR.Screen` previews at 768 and 1280 px with 0 issues | PASS |
| DS-08 | Four assemblies | P01–P04 operable with labelled fixtures | Scripted clicks on surface C. P01: send, stale preflight kept the edited message and sent nothing, rechecked, sent. P02: save failure, retry, missing budget blocks send with its reason. P03: required answer enforced, "Belum dapat dipenuhi" accepted, 09:30 slot "Waktu sudah bentrok", 10:00 slot allowed, selected is not booked, failed replacement keeps the meeting and the selection. P04: v1 confirm publishes nothing, correction clears confirmations, v2 needs both, amount stays private, hide narrows at once | PASS |
| DS-09 | Independent state axes | Required combinations operable | *StateAxes* buttons produce quarantined file with saved answer; AVAILABLE scan with manual extraction and unreviewed content; UNKNOWN in a saved draft; stale preflight with retained message; confirmed relationship with private amount. Each changed only its own axes | PASS |
| DS-10 | Export inspection | Editor and exports checked separately | Local exports inspected: tokens JSON, manifest JSON, single-file guide, bundle, CSS, types, previews. Publish to the private artifact succeeded (version id 1793451079-003c); an agent read of the published manifest returned fingerprints equal to local `tokens.json`, `bundle.js`, `bundle.css` and `index.d.ts`. The page itself was not seen: see below | PASS for local exports; artifact page BLOCKED |
| DS-11 | Real consumption | Two primitives and a domain assembly, controlled token change | `consuming-sample/index.html` loads the same files and uses `TR.TextField`, `TR.Button`, `TR.InventionCard`; binding line reports 1.0.0-draft, "cocok". Setting `--tr-sys-color-action-primary-background` to `#7c2d12` moved both the primitive button and the card's button from `rgb(15,118,110)` to `rgb(124,45,18)`, and removing it restored both. Applied as a runtime CSS override. This is an imported reference, not inheritance. The pane was hidden during the check, so the transition did not tick; values were read with transitions off | PASS |
| DS-12 | Complete delivery | Manifest, inventory, validation, update procedure | Manifest with fingerprints, 31 component ids, this report and *Release and consuming* | PASS |

## Not run or blocked

| Check | Status | Why |
|---|---|---|
| Screen readers (NVDA, VoiceOver, TalkBack) | NOT RUN | No assistive technology here. Names, roles and states were checked in the DOM only |
| Status announcements as heard | NOT RUN | `role="status"` presence verified, spoken output not |
| Participant comprehension and task time | NOT RUN | Needs a study; no usability result is claimed, including for the UX principles |
| Real `prefers-reduced-motion` | NOT RUN | The workbench class applies the same rules: transitions 0 s observed. The media query itself was not emulated |
| Browser zoom and OS text-size settings | NOT RUN | 200% was tested as root font-size only |
| Forced colours | NOT RUN | A transparent outline exists for it; not exercised |
| Rendering and keyboard on the artifact page | BLOCKED | The built-in browser showed "Sign in to view this page" for the private artifact. No sign-in was attempted. The owner should open the link and check that the previews render |
| Firefox, Safari, real phones | NOT RUN | One engine only |
| Dark and client themes | NOT RUN | Deferred by the handoff |
| 72 product acceptance scenarios | NOT RUN | Need the application and server. This system does not pass them |

## Known limits

- These components display what they receive. They enforce no authorization, file scanning, booking or consent rule.
- Sessions without `sessionStorage` lose `TR.Disclosure` memory; it falls back to `defaultOpen`.
- P01 places three fixtures on one page to show three outcomes at once. The application shows one source request.
- Native radio and checkbox glyphs are sized in rem through CSS, but the row stays the real target.

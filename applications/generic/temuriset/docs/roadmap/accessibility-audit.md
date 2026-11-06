# Accessibility audit of assembled journeys

## Run and coverage

The local run on 6 November 2026 used the integrated worktree based on `485028dbf28d9d755c2cf1462e9afb2778ea68bd`, Next.js 16.4.5 production build, the development API and worker at Alembic `0014`, composition `generic-base`, and a disposable PostgreSQL database with synthetic accounts and files. The browser was Chromium 156.0.8078.4 on macOS 27.2 (26B123), ARM64. The default local mode was 100% browser zoom, viewport height 800 CSS px, and no assistive technology. In the tables, **L** means that build and environment. Viewports are CSS px. **PASS** applies to the checkpoints in its row. **NOT RUN** identifies an available state with no observation. **BLOCKED** identifies a missing environment, feature or pairing. This record supports individual checks towards the WCAG 2.2 AA target.

| Surface | Local fixtures and baseline |
|---|---|
| J01, S03/S10/S11 | [matching.spec.ts](../../applications/temuriset-web/e2e/matching.spec.ts), Rani's synthetic project need and a partner mandate. Repair the unknown range, recheck the match, review the brief and submit to the partner. |
| J02, S07/S10/S11 | [needs.spec.ts](../../applications/temuriset-web/e2e/needs.spec.ts) and [j02-company-raise.spec.ts](../../applications/temuriset-web/e2e/j02-company-raise.spec.ts), Bima's one company raise with two linked inventions, matched against an equity mandate. |
| J03, S12/S13 | [j03-revision.spec.ts](../../applications/temuriset-web/e2e/j03-revision.spec.ts), requester and recipient, required revision, two versions of a synthetic PDF, resubmission, answer review and decision modal. |
| Settings and privacy | [privacy.spec.ts](../../applications/temuriset-web/e2e/privacy.spec.ts), synthetic private reporting, retained categories, deletion confirmation and export authorization. |
| J04 and J05 | J04 discussion and scheduling requires 027–029. J05 relationship and public projection requires 030–032. The available pitch approval view opens discussion as a state. |

The [003 route suite](../../applications/temuriset-web/e2e/routes.ts) used [axe](../../applications/temuriset-web/e2e/axe.spec.ts) and [overflow](../../applications/temuriset-web/e2e/overflow.spec.ts) at 320, 360, 768 and 1280 CSS px. [Keyboard](../../applications/temuriset-web/e2e/keyboard.spec.ts) ran at 360. Text-only scaling ran at 320 with the root font size set to 200%. The complete local Chromium run recorded 400 passes and 398 planned viewport skips. Two axe trace outputs collided with an independent audit process. Both affected tests passed in isolation with separate output directories. The flow-level checkpoints below use the actual synthetic journeys, including the `Temukan` navigation label at mobile widths and `Temukan Investor/Mitra` at wider widths.

## UX-19 Keyboard, focus and dialogs

Environment L. Representative controls were focused, traversed with Shift+Tab then Tab, and checked for a focus indicator and a visible center unobstructed by the sticky bar. Modal traversal used five Tabs followed by five Shift+Tabs. Expected dialog focus stayed inside the open dialog. Remaining end-to-end actions in the browser suite include pointer and programmatic form interactions. A wholly keyboard-only traversal of every step remains NOT RUN.

| Surface | Widths at 100% | Result and evidence |
|---|---|---|
| J01 | 320, 360, 768, 1280 | PASS. Enter opened discovery from the main navigation. The range repair link, minimum input and send button were reachable with visible, unobstructed focus. The run saved a range and ended with a submitted pitch visible to the recipient. |
| J02 | 320, 360, 768, 1280 | PASS. Prepare, send and existing-pitch links or buttons retained visible focus. Following the duplicate warning opened the existing pitch. |
| J03 | 320, 360, 768, 1280 | PASS. Required question and file-version controls were reachable. Sending without an answer focused the error summary. Approval modal cycled among Tutup, Setujui untuk diskusi and Batal. Escape closed it and focus returned to the opener. |
| Settings/privacy | 320, 360, 768, 1280 | PASS. Missing report reason focused its error summary. The deletion dialog cycled among Tutup, Ajukan penghapusan and Batal. At 320, Enter opened it and Escape restored focus, including in the text-only scaling check. |
| J04 | — | BLOCKED on 027–029. |
| J05 | — | BLOCKED on 030–032. |

## UX-20 Rendered contrast and information independent of color

Environment L at 100% zoom. Recorded the CSS color, first opaque ancestor surface, border, adjacent surface and outer focus shadow for each rendered checkpoint. Ratios use WCAG relative luminance. The sampled text uses the normal-text threshold of 4.5:1. Large text has a 3:1 threshold and essential graphics, control edges and focus indicators have 3:1 where applicable. Transparent button borders are decorative where the fill provides the button boundary. The RGB pairs below are listed as hex. [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

| Surface | Widths at 100% | Result and measured checkpoints |
|---|---|---|
| J01 | 320, 360, 768, 1280 | PASS. Repair and send labels use white on teal `#0f766e`, 5.47:1 or higher in sampled states. Minimum field text is `#0f172a` on white, 17.85:1, and its boundary `#64748b` on white is 4.76:1. The mobile discovery icon `#475569` on white is 7.58:1 and has an accompanying label. `Perlu konfirmasi` and `Siap dikirim` are written out. The published source uses separate `Saat ini` and `Direncanakan` labels, 17.85:1 and 7.58:1 on white. |
| J02 | 320, 360, 768, 1280 | PASS. Prepare and send labels are white on `#0f766e`, 5.47:1. The underlined existing-pitch link is `#115e59` on warning `#fffbeb`, 7.31:1. Company identity and the duplicate-pitch warning are written out. |
| J03 | 320, 360, 768, 1280 | PASS. Revision question text `#0f172a` on white is 17.85:1 and field boundary `#64748b` on white 4.76:1. The required-answer summary has `#0f172a` on `#fef2f2`, 16.32:1, with a visible border and explanatory text. The attachment uses a checked control and explicitly names version 2. The approval consequence is plain text, 17.85:1. |
| Settings/privacy | 320, 360, 768, 1280 | PASS. The report reason has black text on white, 21:1, and the sampled border `#767676` on the adjacent surface is at least 4.54:1. Error summary text `#0f172a` on `#fef2f2` is 16.32:1. Confirm deletion uses white on `#b91c1c`, 6.47:1. Report receipt and retained categories have textual labels. |
| Focus states on all four surfaces | 320, 360, 768, 1280 | PASS. Blue outer ring `#005fcc` against white is 5.98:1, 5.77:1 against the warning surface and 5.74:1 against the selected checkbox surface. |
| Unreached icon, error and state variants | — | NOT RUN. The sample covers enabled and focused controls, selected versions, current/planned facts and the named error, confirmation and success states. Remaining variants require individual checks. |
| J04 | — | BLOCKED on 027–029. |
| J05 | — | BLOCKED on 030–032. |

## UX-21 Reflow, text size and browser zoom

| Surface | Mode and viewports | Result and evidence |
|---|---|---|
| J01 | L, 100%, 320/360/768/1280 CSS px | PASS. Repair, form and preflight reflowed with matching document and viewport widths at measured checkpoints. Submission was operable at each width. |
| J02 | L, 100%, 320/360/768/1280 CSS px | PASS. Match, preflight and duplicate-return views reflowed without horizontal scrolling. Send and existing-pitch actions remained operable. |
| J03 | L, 100%, 320/360/768/1280 CSS px | PASS. Revision question, required-answer summary, attachment and approval modal fit the viewport at measured checkpoints. Review and approval completed. |
| Settings/privacy | L, 100%, 320/360/768/1280 CSS px | PASS. Report error, deletion confirmation and retained categories fit the viewport. Report and export worked. |
| 003 base routes and settings | L, 200% text-only, 320 CSS px | PASS. `overflow.spec.ts` checked scroll width and unobscured primary controls. The privacy dialog remained operable and returned focus. The test applies a root font-size change. |
| J01, J02, J03 and settings entry routes | L, 200% browser zoom, 800 → 400 CSS px | PASS. Chromium's browser zoom API returned factor 2 and device-pixel ratio increased from 1 to 2. Discover, support requests, pitches and settings each had a 400 px viewport and 400 px scroll width. The settings confirmation was operable by keyboard. |
| J01–J03 and both privacy flows | L, 200% browser zoom, 640 → 320 CSS px | PASS. Five flow tests passed in isolated browser profiles using the browser zoom API. All 18 measured checkpoints had DPR 2, a 320 px viewport and 320 px document scroll width. Range repair and pitching, duplicate return, revision and approval, private reporting, and deletion/export completed. |
| J04 | — | BLOCKED on 027–029. |
| J05 | — | BLOCKED on 030–032. |

## UX-22 Labels, status, targets and motion

Environment L at 100%, using Chromium roles, accessibility-tree snapshots and reduced-motion media emulation. Touch and desktop pointer geometry is in CSS px. Applicable targets measure at least 24×24 CSS px or qualify for a measured exception. [W3C target size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

| Surface | Widths | Result and evidence |
|---|---|---|
| J01 | 320, 360, 768, 1280 | PASS for sampled controls. Minimum field exposes `Biaya minimum` and associates its hint. Navigation measured 64×68 at 320, repair link 202×44 and send 254×63. Axe checked the actual preflight page. |
| J02 | 320, 360, 768, 1280 | PASS for sampled controls. `Siapkan pitching` and the recipient-named send button expose names and meet minimum size. The 168×18 existing-pitch link qualifies by spacing. At the closest sampled width its center was 380 px from the nearest other target and 522 px was the minimum center distance to another undersized target across widths. |
| J03 | 320, 360, 768, 1280 | PASS for sampled controls. The question is named `Pertanyaan (wajib)`, error summary receives focus, and the checkbox name includes version 2. The checkbox drawing is 20×20 inside its clickable 254×65 label at 320 and ≥294×44 at wider widths. The approval modal exposes its heading as the name. Axe checked the recipient's document tab. |
| Settings/privacy | 320, 360, 768, 1280 | PASS for sampled controls. The reason exposes its required label, `aria-invalid=true` and a reference to the corresponding field error. The submitted report receipt exposes role `status`. The reason and deletion confirmation measure 254×36 and 189×44 at 320. |
| All four local surfaces | 320, 360, 768, 1280 | PASS for sampled controls under `prefers-reduced-motion: reduce`. Chromium reported a matching media query and zero transition and animation duration on the sampled focusable controls. Actual announcement speech and other status transitions remain NOT RUN. |
| J04 | — | BLOCKED on 027–029. |
| J05 | — | BLOCKED on 030–032. |

## External conditions

| Surface | Staging UX-19 | Staging UX-20 | Staging UX-21 | Staging UX-22 | NVDA with Firefox | VoiceOver with Safari |
|---|---|---|---|---|---|---|
| J01 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | NOT RUN |
| J02 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | NOT RUN |
| J03 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | NOT RUN |
| Settings/privacy | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | NOT RUN |
| J04 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| J05 | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED |

Staging requires an approved HTTPS origin, deployed digests, approved synthetic authentication and completed journey fixtures. Browser, zoom and device versions remain unrecorded there because no session was run. NVDA requires a Windows test environment with Firefox and a human-observed or captured screen-reader session. Safari was installed on the macOS host, but the headless test process did not exercise interactive VoiceOver navigation or speech. J04 and J05 additionally need their missing runtime features.

## Failure disposition

The measured local checkpoints above produced no reproduced product failure. The two initial axe errors came from shared trace output and passed on the same build with independent output directories. The first narrow J01 automation attempt used the desktop navigation label. The mobile retest used the visible `Temukan` link and passed the full synthetic flow. An unexecuted check remains open for later verification in its named condition.

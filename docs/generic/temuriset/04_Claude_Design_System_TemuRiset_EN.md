# TemuRiset — Claude Design System handoff

Handoff version 1.0 · 31 October 2026 · Asia/Jakarta.

Product authority: TemuRiset generic PRD v1.1. Product and modular-monolith/reuse direction are accepted. The requested system is **TemuRiset Design System**, initially **1.0.0-draft**. Its existence, registration, component implementation, rendered accessibility and consumption have not been established by this document.

**Attach this file alone for stage 1.** It contains the product context, foundations, component contracts, fictional examples, validation gates and ready prompt needed to create the system. No repository, earlier chat or additional PRD attachment is required for this stage. Create the system, interactive workbench, four bounded pattern assemblies and a small consuming sample. The complete application is stage 2.

## 1. Outcome and authority

Make a small, coherent product system that helps people understand what they can do next and what the current evidence means. It must support independent inventors and individual investors as comfortably as organizational teams. Build reusable controls and patterns from common tokens; avoid screen-specific copies that drift between personas.

The system serves a responsive web product. The accepted engineering direction is a modular monolith with a maintained core, validated configuration, tested capabilities, concrete adapters and shared releases. Next.js/TypeScript, FastAPI/Python, PostgreSQL and private storage are initial implementation choices. A design artifact is neither that server implementation nor a production authorization boundary. Component contracts should be portable to semantic HTML and a React web implementation without assuming a particular editor export is already production-ready.

Use English for documentation and stable identifiers, and natural Indonesian for every product example. Create a single light theme first. Branding variants can later replace approved visual values while preserving semantic identifiers, accessibility and business meaning. System version, PRD version, product configuration, source release and database schema are separate identities.

Complete reversible private design choices without repeatedly requesting approval. Record consequential assumptions, unresolved questions and unavailable platform features. Do not initiate publication, organization-wide defaults, service deployment, account connections or migration of existing projects. Those actions are not required to produce the requested private system/reference.

## 2. Product context the system must preserve

TemuRiset helps inventors find investors and partners who can advance an invention. An invention can be hardware, software, a process, a material, a formulation or another applied solution. The product label does not certify novelty, patentability, rights or commercial value. The first useful outcome is a qualified discussion with an understood support request, appropriate evidence and a next step.

There are exactly two public onboarding personas: **Inovator** and **Investor/Mitra**. A reviewer or moderator is a scoped capability, not a third market persona. An account can act in a personal or authorized organization context. The working context is visible before submission, decision, disclosure and confirmation. Do not force an individual to create a fictitious company or institution.

An Invention has a responsible managing context, contributors, versions, current/planned capabilities, evidence and deliberately public fields. Creator, manager, asserted rights holder and authorized representative can differ. A patent, formal readiness scale, company, video or institutional affiliation is not a universal prerequisite. A recipient can state a particular requirement for its opportunity and stage; the interface must show that requirement and its reason.

A SupportRequest concerns a selected development outcome, such as validation, manufacturing assistance, licensing or project finance. Its ProjectBudget has a currency, period, scope and estimate date. A FundingRequest concerns one venture/company raise, optionally linked to several inventions. Company financing stage is distinct from invention maturity. A proposed entity must be labelled honestly, and a confirmed equity relationship needs an identified actual legal entity. An investor's contribution range is not automatically the entire raise target.

The normal flow is prepare portfolio → select support or company request → discover an appropriate recipient → inspect requirements → review preflight and brief → submit → decide or request revisions → answer and resubmit → agree a meeting → record the outcome → separately propose and confirm a relationship. The visible interface should emphasize the next action and whose turn it is. Keep numerical ranking, detailed provenance and advanced filters behind secondary disclosure, while leaving blocking gaps visible.

These distinctions must survive every component and theme:

| Distinction | Required product meaning |
|---|---|
| CURRENT / PLANNED / REQUESTED | A planned capability cannot satisfy a requirement for something that exists now |
| Source-reported / provided / reviewed | A claim or upload does not become verified evidence because it appears in a styled card |
| PASS / FAIL / UNKNOWN / NOT_APPLICABLE | Unknown or insufficiently reviewed evidence is neither a confirmed failure nor a pass |
| Eligibility / readiness / gaps | Recipient fit, permission to submit, evidence coverage and later commercialization work are separate outputs |
| Project / company / license amounts | Scope, currency, period and financial subject remain visible; no automatic valuation or share inference |
| Draft / saving / saved | Local work is not server-saved merely because a checkmark is drawn |
| Pitch approval / relationship | Approval means willingness to discuss, not funding, licensing or partnership |
| Slot selection / acceptance | Selecting a proposed time is temporary until explicit acceptance succeeds |
| Confirmation / disclosure | Both parties confirm the same summary and proposed disclosure ceiling; effective public fields are their consent intersection, reduced by live restrictions |

Documents default private. Sharing selects named recipients and specific versions, not an entire portfolio or all future revisions. Revocation blocks new protected retrieval and dependent disclosures; it cannot recall prior recipient copies or bytes already in flight. A historical snapshot preserves an event without granting perpetual access to confidential facts. Do not expose a protected title in an access-denied example.

## 3. Actual Claude surface and binding contract

Inspect the authoring surface and supplied inputs before building. Current official documentation describes Design artifacts and several system/import/export routes, with separate plan and permission prerequisites for system features. Do not hardcode a fragile menu sequence or assume that every account has the same library functionality. [Claude Design getting started](https://support.claude.com/en/articles/14604416-get-started-with-claude-design), [system setup](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design).

Choose and report the actual mode:

| Mode | Evidence required | Honest claim |
|---|---|---|
| Registered Claude system | Actual created/selected system identifier, version, component references and consuming result | The named system is supplied through the observed system mechanism |
| Imported component source | Actual source/artifact, import or synchronization method and inspected consuming components | The supplied revision is imported; future changes require an observed update |
| Portable local reference | Actual guide/tokens/component source or local mapping plus a runnable workbench | A portable reference was used; registration and automatic inheritance are unverified |

If registration is unavailable, continue with a useful portable system and workbench, label the limitation and provide the actual consumption procedure. Do not substitute another organizational default silently. A visually similar screenshot is not binding evidence. Existing designs can retain their own copies; component updates need explicit re-sync/rebinding and checks. [Claude system tutorial](https://academy.claude.com/tutorials/create-a-design-system-with-claude), [prototype tutorial](https://academy.claude.com/tutorials/using-claude-design-for-prototypes-and-ux).

The system editor and the generated web content are different test surfaces. Official setup guidance records limitations on reaching live system previews with Tab. If that prevents a check, provide a separately runnable workbench, test it there and mark the host-only check BLOCKED. Never infer accessible generated content from an accessible editor, or the reverse.

## 4. Visual and information direction

Use a calm, light teal/slate utility aesthetic. The product should feel clear, dependable and comfortable to read. Give the task room to breathe without giant empty hero areas. Prioritize problem, current solution, support sought, financial scope, evidence and responsible parties. Let a short reason and direct action carry a card rather than a dense collection of badges.

Use one primary action per task region. Primary actions describe effects: “Siapkan pitching,” “Kirim pitching,” “Setujui untuk diskusi,” or “Konfirmasi waktu.” Secondary actions allow inspecting evidence, editing an answer or returning to a list. A destructive action needs an appropriate explanation, but ordinary reversible navigation should stay lightweight.

Provide meaningful product images if supplied. Otherwise use a restrained category illustration with a textual label; an absent image is not a blocked invention. No invented product photo, investor credential, funding-progress chart, rating, follower count or trend. Do not require ornamental dashboards, gradients, animated counters, excessive shadows or nested cards around every paragraph.

On desktop, place the active task before supporting timeline or context. On narrow screens, preserve that reading order and stack supporting detail below. A summary list suits submitted answers; a task list suits resumable work. A fixed-order editor uses steps, not an unordered checklist. This applies established question/review guidance to this product rather than claiming one layout is universally best. [GOV.UK question pages](https://design-system.service.gov.uk/patterns/question-pages/), [check answers](https://design-system.service.gov.uk/patterns/check-answers/), [task list](https://design-system.service.gov.uk/components/task-list/).

## 5. Token authority and exchange format

Use three proposed logical layers: TR.ref for primitives, TR.sys for semantic roles and TR.comp for component-specific aliases only when needed. A component consumes an alias rather than owning a copied raw color or spacing constant. Semantic names remain stable across a supported brand theme. Theme values can change; an error cannot become indistinguishable from success and a funding request cannot change meaning through a theme.

Logical examples such as TR.ref.color.teal.700 describe hierarchical paths. If exporting DTCG, represent these as nested JSON groups; literal token/group keys cannot contain periods, braces or start with a dollar sign. DTCG 2025.10 is a stable Final Community Group Report, not a W3C Standard. Use that pinned published format if supported, declare the implemented types/modules and validate references, cycles, units and types. Otherwise export explicitly labelled custom JSON with its own schema/version and a conversion map. Valid JSON alone is not format-conformance evidence. [DTCG reports](https://www.designtokens.org/technical-reports/), [Format Module 2025.10](https://www.designtokens.org/tr/2025.10/format/).

Required seed color roles are below. They are proposed starting values, not an already approved visual system. Produce the full machine-readable registry from the same authority used in components.

| Semantic ID | Seed value or alias | Usage |
|---|---|---|
| TR.sys.color.canvas | #F8FAFC | Application canvas |
| TR.sys.color.surface | #FFFFFF | Primary content surface |
| TR.sys.color.surface.subtle | #F1F5F9 | Secondary grouping |
| TR.sys.color.text.primary | #0F172A | Main text |
| TR.sys.color.text.secondary | #475569 | Supporting text with adequate contrast |
| TR.sys.color.action.primary.background | #0F766E | Primary action |
| TR.sys.color.action.primary.hover | #115E59 | Hover/pressed starting reference |
| TR.sys.color.action.primary.foreground | #FFFFFF | Text/icons on primary action |
| TR.sys.color.action.secondary.foreground | #115E59 | Secondary action on light surface |
| TR.sys.color.selected.surface | #F0FDFA | Selected contextual surface |
| TR.sys.color.border.decorative | #CBD5E1 | Nonessential dividers only |
| TR.sys.color.border.control | #64748B | Required control boundary |
| TR.sys.color.focus | #005FCC | Visible focus on a light surface |
| TR.sys.color.danger.text | #B91C1C | Error text |
| TR.sys.color.danger.surface | #FEF2F2 | Error background |
| TR.sys.color.success.text | #166534 | Success text |
| TR.sys.color.success.surface | #F0FDF4 | Success background |
| TR.sys.color.warning.text | #92400E | Warning/unknown text when appropriate |
| TR.sys.color.warning.surface | #FFFBEB | Supporting warning surface |

Create matching primitive references for these values, then alias semantic roles. TR.comp.button.primary.background aliases TR.sys.color.action.primary.background; TR.comp.field.border aliases TR.sys.color.border.control; TR.comp.field.focus aliases TR.sys.color.focus. A token's group is not its semantic meaning. Keep usage and prohibited combinations in the human registry, including where a decorative border must not be the only control boundary. Stable role-based tokens follow established design-system practice; this particular TR taxonomy is a product decision. [USWDS tokens](https://designsystem.digital.gov/design-tokens/), [Carbon themes](https://www.carbondesignsystem.com/building-blocks/foundations/themes/overview).

Other required seeds:

| Token family | Starting contract |
|---|---|
| TR.ref.space | 4, 8, 12, 16, 24, 32, 48, 64 CSS px equivalents; expose rem mappings |
| TR.sys.space.controlGap | 8 px equivalent; increase where touch separation needs it |
| TR.sys.space.section | 24 px mobile, 32 px desktop starting values |
| TR.sys.layout.gutter | 16 px narrow / 24 px wide |
| TR.sys.layout.contentMax | 1,200 px starting maximum |
| TR.sys.layout.readingMeasure | About 60–70 characters for long prose |
| TR.ref.radius | 6 px controls, 8 px ordinary surfaces, 12 px large dialogs |
| TR.sys.type.body | System sans-serif stack, 1rem/1.5, normal weight |
| TR.sys.type.label | 1rem/1.4, medium weight |
| TR.sys.type.support | 0.875rem/1.5; never the sole carrier of a primary action or critical gap |
| TR.sys.type.heading | Restrained 1.25rem, 1.5rem and 2rem steps with appropriate line height |
| TR.sys.size.controlComfort | 44 px minimum proposed height for common primary controls |
| TR.sys.size.icon | 18–20 px glyph within a suitably sized target |
| TR.sys.motion.feedback | Up to 150 ms for useful state feedback; 0 ms for reduced motion |

Use a system stack initially; do not silently depend on a downloaded or licensed font file. Typography sizes are design choices, not WCAG minimum-font-size rules. Keep numeric amounts and units together, align comparable money values consistently, wrap long titles and preserve legibility at enlarged text. Render focus with a visible outer ring and light separation where needed; check every adjacent color rather than assuming the ring works on all surfaces.

### 5.1 Document-level contrast calculations

The following seed pairs were calculated on 31 October 2026 with sRGB channels normalized to 0–1, linearized at 0.04045, relative luminance weights 0.2126/0.7152/0.0722, and ratio (Llighter + 0.05)/(Ldarker + 0.05). Values are rounded for display; threshold decisions use unrounded values.

| Foreground / background | Calculated ratio |
|---|---:|
| #0F172A / #FFFFFF | 17.8525:1 |
| #475569 / #FFFFFF | 7.5777:1 |
| #FFFFFF / #0F766E | 5.4733:1 |
| #FFFFFF / #115E59 | 7.5835:1 |
| #005FCC / #FFFFFF | 5.9849:1 |
| #64748B / #FFFFFF | 4.7588:1 |
| #B91C1C / #FEF2F2 | 5.9146:1 |
| #166534 / #F0FDF4 | 6.8117:1 |
| #92400E / #FFFBEB | 6.8370:1 |

These calculations establish only the listed opaque color pairs. They do not test actual font rendering, transparency, overlays, focus adjacency, icons, hover/selected states or complete pages. All rendered gates remain NOT RUN. Recalculate every changed theme and inspect the actual rendered combinations. Do not present a palette calculation as WCAG conformance. [WAI contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

## 6. Accessibility and responsive interaction contract

Target WCAG 2.2 AA on complete rendered pages and journeys, including all applicable A/AA requirements. The following is a focused execution checklist, not a replacement for the full standard. Normal text needs 4.5:1 contrast; qualifying large text can use 3:1. Required control/state/graphic information needs 3:1 where applicable. Exceptions such as inactive/incidental content must not become an excuse for unclear product copy. [WCAG 2.2](https://www.w3.org/TR/WCAG22/).

Test 200% text resizing, 320 CSS px reflow, and ordinary 360 px, 768 px and 1,280 px layouts. A genuine two-dimensional comparison can have bounded local scrolling; the whole application must not acquire unnecessary horizontal scrolling. Sticky navigation and action bars must not entirely obscure focused controls under AA; the stronger product preference is full active-control/help visibility.

AA target size is 24 × 24 CSS px with specified spacing, equivalent-control, inline, user-agent and essential exceptions. Use comfortable 44 × 44 areas for common touch actions where practical; that is a stronger product preference, not a universal AA minimum. Icons inside a target do not define its hit area. [Target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), [focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).

Use semantic controls with accessible names, associated visible labels, help and inline errors. After invalid submission, retain values, focus a concise error summary and link each item to the relevant field. Do not rely on a disappearing toast. Announce meaningful saving/status changes without moving focus or announcing every keystroke. Status and requirements always have text, with color as supporting information.

Dialogs need a label, sensible initial focus, contained Tab/Shift+Tab, Escape/close behavior and logical focus return. Prefer an ordinary page for lengthy multi-step work. A recoverable error should not reopen a dialog repeatedly or discard entered text. Confirming a destructive action and confirming disclosure are distinct tasks. [GOV.UK error summary](https://design-system.service.gov.uk/components/error-summary/), [WAI modal pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).

Avoid nonessential motion and respect reduced-motion preferences. This is an explicit product policy beyond the relevant AA minimum; interaction-animation disablement is addressed by a AAA criterion. Keep useful loading/saving text available without depending on animation. Do not claim reduced motion alone establishes accessibility. [WAI animation guidance](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html).

## 7. Component inventory and usage contracts

The following 26 proposed identifiers are the shared inventory. Implement the needed components once, then compose them. Record implemented source names and mappings if the authoring runtime cannot use literal namespace syntax. A row defines a contract, not proof the component already exists.

| ID | Anatomy, inputs and behavior |
|---|---|
| TR.Button | Visible action label, optional supporting icon and loading text. Inputs include intent, disabledReason and busy. Use button semantics; Enter/Space works. Prevent repeat intent while pending without losing the prior result. A disabled action explains why near the action, and never masquerades as a link. |
| TR.Link | Descriptive text, optional external-route indication and destination. Use link semantics and normal browser navigation. Contextual change links name the field they edit. An external application route does not imply an in-app pitch was submitted. |
| TR.TextField | Visible label, optional hint, value, requiredness and inline error. Support text, email and decimal input appropriately. Keep an explicit empty value separate from zero; retain nonsecret input on error. Do not use placeholder text as the only label. |
| TR.TextArea | Label, hint, retained multiline value, optional limit/count and error. Fit the task rather than forcing long answers into a tiny box. A counter is supporting feedback, not the only limit explanation; preserve text after retry or version conflict. |
| TR.Select | Visible label, current selection and options with understandable empty choice. Prefer established browser selection behavior for simple sets. Show a disabled option's reason where meaningful; do not silently choose a sector, currency or company. |
| TR.ChoiceGroup | Fieldset/legend with mutually exclusive radio choices, hints and errors. Supports support type, relationship type and current/planned choice. Arrow/Tab behavior follows semantics; changing purpose reveals relevant fields without deleting unrelated saved drafts silently. |
| TR.Checkbox | Clear individual label and optional group legend/hint. Space toggles it. Disclosure consent is unchecked unless an actual saved decision exists. Do not use a prechecked blanket private-file or publication permission. |
| TR.FieldError | Plain correction message associated with its field and repeated consistently in the summary. Receives stable error code and safe human text; never stack traces or another party's data. It does not erase the value or use color alone. |
| TR.ErrorSummary | Focusable heading and linked field/error list after failed submission. Link text identifies the failed answer. Global retry errors without field targets offer a direct recovery action. Repeated background saves should not continually steal focus. |
| TR.Dialog | Labelled dialog, structured body, explicit primary/secondary effect and close action. Owns focus containment/return, not business authorization. Long summaries can initially focus a heading. Escape returns safely without an unintended commit. |
| TR.Disclosure | Descriptive toggle, expanded state and associated region for evidence, score detail or supporting information. Enter/Space operates it. A blocking gap remains visible even when detail is collapsed. Preserve expanded state when returning from a supporting page. |
| TR.Tabs | Named tabs for related pitch workspace content, selected state and associated panels. Keyboard behavior is implemented and documented. Each panel has a logical heading; focus is not lost when data loads. Narrow layouts keep every tab reachable. |
| TR.Status | Concise visible label, optional icon, semantic tone and explanatory text. Receives the actual domain result; it never determines PASS or approval from color. Status changes use appropriate programmatic semantics without unnecessary focus movement. |
| TR.EmptyState | Relevant reason, context and a useful next action. Distinguishes no published inventions, no matching targets, closed intake and denied access. It does not fabricate zero money, trends or recommendations to fill a layout. |
| TR.SaveState | Local-change, saving, saved-with-time, failed and stale-version states. In a browser demo it says the draft is saved in that demo context, not a production server. Retry retains values; losing network does not display a saved checkmark. |
| TR.ContextSwitcher | Current personal/organization party, authorized choices and clear acting-context label. Selection cannot grant membership. Disabled/denied context has a safe reason. Before send/decide/confirm, show the context the action will use. |
| TR.InventionCard | Category/image fallback, title, problem/current solution, maturity, support request, scoped financial summary, short reasons/gap and one action. Inputs are authorized projections and explicit source labels. Planned functionality and unreviewed facts stay labelled. |
| TR.FundingRequestCard | One funding request, company/proposed-entity label, financing stage, total target, desired contribution, purpose and linked invention count. It never repeats a whole raise per invention, assumes a formed company or derives shares. |
| TR.FinancialScope | Explicit financial subject, basis, currency, range, period, estimate date, assumptions and optional editable fields. Renders project total, company target, contribution or license terms distinctly. Null means unknown; noncash scope can work without invented money. |
| TR.RequirementRow | Requirement label, stage, mandatory/preference, verification mode, result, reason/source and next action. PASS, FAIL, UNKNOWN and NOT_APPLICABLE use readable text. Future commercialization work is not styled as an immediate submission blocker. |
| TR.FactSource | Current/planned/requested status plus source-reported/self-declared/provided/reviewed provenance. Shows review scope/version where known and a permitted source link. A source link cannot reveal protected titles or contents to an unauthorized user. |
| TR.DocumentItem | Safe title when authorized, version, file availability/security, extraction state, evidence review and recipient grant separately. A cleared scan can be available with manual extraction. Sharing controls select a named version and recipient; revocation has truthful limits. |
| TR.RevisionItem | Round/item heading, reason, required/optional flag, due date, retained answer, response option, attachments and review result. “Perlu diskusi” and “Belum dapat dipenuhi” are valid answers, not approvals. One upload failure cannot clear other answers. |
| TR.ScheduleSlotList | Two to five proposed slots with full date, local time, duration and IANA-derived zone label; selected/confirmed distinction and explicit accept/alternative actions. Supports pending, expired, conflict, cancellation and replacement states while preserving agenda. |
| TR.PartnershipConsent | Same-version summary, relationship/entity scope, proposed public-field ceiling, party-specific choices, effective intersection and confirmation status. One confirmation is pending. Material edit/expansion needs new confirmation; live narrowing hides fields immediately. |
| TR.VersionConflict | What became stale, current allowed version and retained local draft. Offers compare/refresh or copy/retry as appropriate. It must not silently merge consequential changes or disclose protected actor/source metadata. |

For every implemented component document token aliases, semantic element, accessible name, focus order, keyboard behavior, minimum/maximum content, narrow-layout behavior and relevant states. Standard states are default, hover, focus, active/selected, disabled-with-reason, loading, validation error, recoverable failure and success where meaningful. Domain states are passed explicitly. Do not invent every state for a control where it has no meaning.

## 8. Independent state axes and copy

Use the following state axes in workbench controls. Changing one does not imply changes in the others.

| Axis | Values/examples | Required presentation |
|---|---|---|
| Draft saving | Local changes, saving, saved, failed, version conflict | Retained input and accurate save location/time |
| File availability/security | CREATED, UPLOADING, QUARANTINED, AVAILABLE, REJECTED | File presence cannot bypass quarantine |
| Extraction | NOT_REQUESTED, PENDING, RUNNING, SUCCEEDED, FAILED, NEEDS_MANUAL_INPUT | A safe available scan stays available even when OCR is absent |
| Review | PROVIDED_UNREVIEWED, REVIEWED_SUPPORTED, REVIEWED_UNSUPPORTED, NEEDS_CLARIFICATION, EXPIRED, SUPERSEDED | No automatic verified badge from upload or extraction |
| Requirement | PASS, FAIL, UNKNOWN, NOT_APPLICABLE | Reason, applicable stage and actionable gap |
| Pitch | Submitted, under review, revision requested, approved for discussion, rejected, withdrawn, closed | Approval remains a discussion state |
| Scheduling | Open proposal, selected locally, accepted, expired, superseded, cancelled; confirmed meeting/replacement | No booking until acceptance succeeds |
| Relationship | Draft, pending counterparty, changes requested, declined, confirmed | Exact version and separate public projection |
| Disclosure | Proposed ceiling, per-party subset, effective intersection, restriction event | No field appears beyond mutual/current permission |

Required combined examples include a saved answer with a quarantined attachment; an AVAILABLE scan with NEEDS_MANUAL_INPUT extraction and unreviewed content; an UNKNOWN requirement in a healthy saved draft; a stale preflight with retained message; and a confirmed relationship whose amount remains private. A failed notification does not reverse an approved discussion. The workbench should make these combinations operable.

Use a small shared Indonesian glossary:

| Meaning | Product copy |
|---|---|
| Main personas | Inovator; Investor/Mitra |
| Portfolio/navigation | Inovasi Saya; Temukan Investor/Mitra; Pitching dan Diskusi |
| Financial subjects | Dukungan Proyek; Pendanaan Perusahaan; Target Pendanaan; Kisaran kontribusi per investor |
| Action responsibility | Menunggu Anda; Menunggu pihak lain |
| Draft status | Belum tersimpan; Menyimpan; Tersimpan di demo ini; Gagal menyimpan |
| Evidence | Dilaporkan sumber; Disediakan, belum diperiksa; Diperiksa untuk kriteria ini; Belum diketahui |
| Capability timing | Saat ini; Direncanakan; Diminta |
| Pitch decisions | Setujui untuk diskusi; Minta revisi; Tolak |
| Revision responses | Dapat dipenuhi; Perlu diskusi; Belum dapat dipenuhi |
| Scheduling | Pilih waktu; Konfirmasi waktu; Usulkan waktu lain; Waktu sudah bentrok |
| Relationship | Kerja Sama; Menunggu konfirmasi; Dikonfirmasi kedua pihak |
| Company status | Perusahaan belum didirikan; Badan usaha telah disebutkan, status pemeriksaan ditampilkan terpisah |

Write short sentences. Explain an unfamiliar term near its first necessary use. A pending action explains who acts next. Do not put internal enum names, HTTP codes, model names or backend architecture in business screens; those belong in the engineering handoff.

## 9. Fictional fixtures and four pattern assemblies

All names, evidence, amounts and activity below are fictional DEMO contracts. They are not actual customers, investor interest, reviewed inventions or funding outcomes.

| Fixture | Exact facts for system examples |
|---|---|
| F01 ClearSpring | Independent water-filter inventor, no company/patent; prototype CURRENT 10 L/hour, PLANNED 20 L/hour. Function file available but initially unreviewed. Six-month validation project USD 20,000–30,000; same-scope partner USD 15,000–40,000. DOCUMENT_PRESENT can pass; a reviewer-confirmed criterion is UNKNOWN until actual review in the fixture. |
| F02 FieldDry | Community agricultural drying process at pilot stage. Seeks noncash test facility; rights authority unconfirmed. A target requiring reviewed authority before submission yields UNKNOWN/needs information. |
| F03 QueueNest | Software team with functioning offline export, PLANNED SSO. Target requires CURRENT SSO at submission, so the known capability mismatch is FAIL. |
| F04 LoopMaterial | Materials prototype managed by fictional Demo Circular Materials Ltd. Company pre-seed is distinct from technology prototype maturity. FRaise01 target USD 500,000, desired contribution USD 50,000–100,000, partial/syndicated finance accepted; individual investor equity checks USD 50,000–150,000. Compare contribution ranges, not the entire round. |
| F05 ReFormPress | Manufacturing invention of the same company, linked to FRaise01. One raise card and one active funding pitch can have two invention links. |
| F06 GridShare | Community energy solution at idea stage; nonprofit team, cash unknown and legal-entity status unconfirmed. Mentoring recipient accepts early concepts; incorporated-equity criterion is UNKNOWN from the stated entity facts. |

Format displayed money unambiguously in Indonesian, for example “USD 500.000” and “USD 50.000–100.000,” while preserving exact underlying decimal values/currency. No automatic foreign-exchange conversion, funding progress or percentage shares. A null amount reads “Belum ditentukan.” Keep project duration beside its range.

P01 **Discovery and preflight** composes InventionCard/FundingRequestCard, FinancialScope, FactSource and RequirementRow with a brief review summary. Show one compatible opportunity, one known mismatch and one unknown gap. A funding card has two invention links without duplicate amounts. Technical score detail can show 71.72–80.00 only as a review-priority index when source features are supplied; it is not a funding probability.

P02 **Portfolio and deliberate disclosure** demonstrates four ordered groups: basics; current solution/evidence; support/financial scope; public preview. Use F01 with an explicit missing-budget variant, retained save failure and an AVAILABLE scan awaiting manual extraction. Review selected public fields and one document/version/recipient before an explicit send. Do not build the full portfolio application during this system stage.

P03 **Revision and schedule** demonstrates a required pilot-budget question, an optional planned-feature question, retained item answers and a proposal of three slots. “Belum dapat dipenuhi” can be resubmitted after all required items are answered. Use 09:00 UTC as 16:00 Asia/Jakarta and 17:00 Asia/Makassar. A 09:30–10:30 UTC request conflicts with an existing 09:00–10:00 booking; 10:00–11:00 is nonoverlapping under half-open intervals. Show a selected-but-unconfirmed slot and a failed replacement that leaves the original meeting intact.

P04 **Relationship consent** demonstrates a project relationship version 1, correction to version 2 and two confirmations of version 2. The proposed public ceiling contains partner name, type, scope, date and amount; if only one party permits amount, it stays private. Narrowing a live permission hides the field without pretending to recall downloads. A project relationship does not create equity, even if a monetary amount exists.

Pattern controls may simulate state changes in a local workbench; label that provenance. They do not prove real file scanning, grant enforcement, simultaneous database booking or legal authority.

## 10. Workbench and evidence protocol

Organize a navigable workbench by foundations, primitives, domain components and P01–P04. Include a short usage page for each component with its anatomy, inputs, do/don't examples and state controls. Make those controls keyboard-operable, not a gallery of screenshots. Keep scenario/reset controls secondary and scoped to fictional demonstration state.

Check error recovery while an input is focused, at enlarged text and on a narrow screen. A save failure should preserve the value and place focus logically; it should not hide the error beneath a sticky bar. A dialog returns focus to its trigger or a sensible next target. A permission-denied state has a safe return/request-access path. Run a full keyboard pass on the separately runnable generated surface if the host preview is limited.

Record expected result, actual result, artifact/version, surface, viewport/text zoom, input method and evidence. Results are PASS, FAIL, NOT RUN or BLOCKED. Synthetic data and mocked services are separate provenance fields. Neither “simulated” nor “looks correct” is a result. Document-level contrast arithmetic is a distinct evidence type from a rendered browser check.

A small consuming sample must use at least two primitives and one domain assembly from the actual supplied source/reference. Demonstrate a controlled semantic-token adjustment reaching both a primitive and a pattern, then restore the intended seed. Record how it was applied; manually matching colors is not registered-system inheritance. Verify any exported version independently because editor Play and an opened export can behave differently. Established systems distinguish adoption from in-context quality; component presence alone proves neither usability nor accessibility. [USWDS maturity model](https://designsystem.digital.gov/maturity-model/), [GOV.UK readiness criteria](https://design-system.service.gov.uk/community/contribution-criteria/).

## 11. Outputs, versioning and consumption

Produce the following actual outputs in the future Claude session, adapting packaging to supported capabilities and reporting unavailable outputs precisely:

| Output | Required content |
|---|---|
| System/reference | TemuRiset Design System, real version/status, actual artifact or source identity when available |
| temuriset-design-system.tokens.json | Complete typed values, aliases, units and declared format/schema/version, with no unresolved references |
| System guide | Token roles, type/layout rules, 26 component contracts, P01–P04, Indonesian copy and accessibility instructions |
| temuriset-design-system.manifest.json | System/PRD identities, actual source/export format, schema, component IDs, theme, status, source fingerprint if available, limitations |
| Component source/inventory | What was actually implemented/exported, dependencies and stable TR mapping; no invented code export |
| Workbench and consuming sample | Runnable or supported interactive artifacts, reset instructions and inspected exports |
| Validation record | DS-01–DS-12 expected/actual evidence and current limitations |
| Consumption/update guide | Exact actual supply/select/import method, binding record and re-sync/migration steps |

The binding record must state system name/version, review status, actual source/artifact identifier or “not available,” supplied files, mechanism used, token/component inventory, consuming artifact/version, deviations and tested result. Do not fabricate an artifact URL, component package or reviewer approval. If portable source was used, identify it as portable source. If only local mapping was possible, identify it as a local draft.

Version token/component public-contract changes and keep deprecated aliases mapped until consumers migrate. Theme changes require pair/state rechecks. Do not assume publishing new source updates past projects; record each consuming revision and perform an observed update. Keep privacy and domain meanings invariant across clients. A client theme cannot change UNKNOWN into FAIL or disclose a funding amount.

## 12. Build order and acceptance gates

Proceed in this order: inspect runtime/inputs → establish identity and output mode → create token authority → implement primitives → implement domain components → assemble P01–P04 → run available checks → inspect exports → verify consumption → deliver binding and update instructions. A missing export surface does not justify abandoning all useful work; provide the available artifact and a precise limitation.

Every gate below starts **NOT RUN** in this repository handoff.

| ID | Gate | Required evidence |
|---|---|---|
| DS-01 | Identity and capability honesty | Actual surface, system version/status, supplied inputs and registered/imported/portable mode |
| DS-02 | Token authority and schema | Complete valid export, resolved aliases/types/units, declared format and no false DTCG claim |
| DS-03 | Rendered color and focus | Actual text/control/icon/focus/state combinations checked; seed calculation distinguished |
| DS-04 | Primitive interaction | Implemented primitive anatomy, keyboard, focus, errors, loading and disabled reasons |
| DS-05 | Domain meanings | Financial basis, one raise/two inventions, source/current/planned and requirement distinctions |
| DS-06 | Focus and recovery | Error summary, dialog containment/return, retained input and accessible status changes |
| DS-07 | Responsive and larger text | 320 reflow, 360/768/1,280 layouts and 200% text with actual surface evidence |
| DS-08 | Four assemblies | P01–P04 operable using exact labelled fixtures and meaningful outcomes |
| DS-09 | Independent state axes | Safe scan/manual extraction, saved/unknown, stale preflight and pending consent combinations |
| DS-10 | Export inspection | Editor and supported exported workbench checked separately; unavailable formats recorded |
| DS-11 | Real consumption | Two primitives plus a domain assembly use the supplied revision; controlled-token-change evidence |
| DS-12 | Complete delivery | Actual manifest/source inventory, validation, known issues and exact update/binding procedure |

Rendered accessibility, participant usability and production backend acceptance remain unverified until appropriate tests run. Creating the system does not pass the product's 72 runtime acceptance scenarios.

## 13. Source and execution boundary

Research sources were opened on 31 October 2026. They support standards distinctions and authoring patterns; token names, layout, components and fixture assemblies here are TemuRiset design decisions. Official Claude behavior can change, so check the actual surface at execution time. No design system, consuming project, live import, export, participant session or rendered accessibility test has been performed by preparing this file.

The following ready prompt is identical to the marked prompt in file 05.

## 14. Ready English prompt

<!-- BEGIN READY DESIGN SYSTEM PROMPT -->
Create **TemuRiset Design System**, initially version **1.0.0-draft**, using the attached self-contained system handoff. Read the complete handoff before choosing foundations. Start with a brief execution map, then build the system and interactive component/pattern workbench to completion. This stage creates the reusable system, four bounded pattern assemblies and a consuming sample; the full application follows in the next stage.

TemuRiset helps inventors find investors and partners across sectors. Preserve two public personas, personal and organization contexts, project support versus company fundraising, one company raise linked to several inventions, current versus planned capabilities, source-reported versus reviewed evidence, UNKNOWN versus FAIL, pitch approval versus partnership, proposed versus confirmed meetings, and exact-version two-party confirmation. Public relationship fields are limited to the parties' consent intersection and current restrictions. Patents, institutions and incorporated companies are not universal entry requirements. All product examples must use natural Indonesian; system documentation and stable identifiers are English.

Use the handoff's calm light teal/slate starting direction, one semantic token authority and the specified TR component identifiers. Build practical typography, spacing, focus and responsive rules, reusable primitives, domain components and all applicable interaction states. Keep draft saving, file availability/security, extraction, evidence review, requirement result and consent independent. Do not turn a pending state into success through color, an icon or a copied badge. Use the exact fictional amounts, units, dates and uncertainty labels from the brief. Do not invent funding, verification, investor activity or legal outcomes.

Inspect the actual Claude authoring capabilities first. State whether the result is a registered Claude system, imported component source or a portable local reference. Record the actual name, version, supply method and source/artifact identifier when one exists. If system registration is unavailable, complete a clearly labelled portable system and workbench rather than stopping or claiming registration. Never silently substitute an unrelated default. Existing copies need an explicit verified update; do not promise automatic inheritance or synchronization.

Implement and exercise keyboard, dialog focus, errors, save/retry, selected/disabled-with-reason, unknown, stale-version and permission states. Target WCAG 2.2 AA with accurate exceptions; use 44 px comfortable controls as a product preference, not a universal AA rule. Check contrast, 200% text, 320 CSS px reflow, 360 px and desktop views, visible focus, non-color cues, status announcements and reduced motion. If the host's component preview cannot accept Tab, use a separately runnable workbench and name the tested surface. Seed color calculations alone do not prove rendered accessibility.

Deliver the actual private system/reference, complete valid token JSON with its declared format, human guide, manifest, component inventory and source where supported, workbench, four pattern assemblies, consuming sample, validation record and exact consumption/update instructions. Claim DTCG 2025.10 compatibility only after format validation; custom JSON must say custom. Inspect available exports separately from editor previews. Record expected and actual results as PASS, FAIL, NOT RUN or BLOCKED, with synthetic/mock provenance separate from test outcome.

Continue through reversible design decisions and document assumptions. Ask only when missing information materially changes product behavior. Keep this work private; publication, organization defaults, external account connections and deployment are outside this stage. Finish with the real binding record, unresolved limitations and the files needed to use this same system in the application stage.
<!-- END READY DESIGN SYSTEM PROMPT -->

# UX and accessibility for TemuRiset tasks

Research completed 31 October 2026, Asia/Jakarta. Ten primary pages were opened. The product baseline read was [TemuRiset generic PRD](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md), including its FR01–FR24, interface, architecture and fixture contracts. These notes propose a design and verification contract; no prototype, participant session or accessibility assessment was executed. WCAG 2.2 is normative where stated; WAI Understanding pages and the ARIA Authoring Practices Guide are explanatory or implementation guidance. GOV.UK patterns are evidence-informed service-design guidance, not universal legal requirements for this product.

## How should the product simplify complex work without losing its meaning?

### Takeaway

Make the next useful task visible and ask for information in a purposeful sequence. Keep the base PRD's domain distinctions in the data and copy, while avoiding a screen full of every internal score, state and permission at once.

### Cited Findings

- GOV.UK question-page guidance recommends knowing why each question is asked, requesting only needed information, allowing uncertainty where valid, reusing previous answers and preserving the browser-back experience. It starts with one focused question per page and permits progress indication when research supports it. This is a pattern recommendation, not a WCAG rule. Accessed 31 October 2026. — [Question pages](https://design-system.service.gov.uk/patterns/question-pages/).
- GOV.UK's check-answers pattern places a review before submission, groups relevant answers, provides contextual change links and returns users to the review after editing. The final action should describe its actual effect. The pattern supports both smaller transactions and section-level review for larger ones. Accessed 31 October 2026. — [Check answers](https://design-system.service.gov.uk/patterns/check-answers/).
- The TemuRiset baseline already separates personal and organization contexts, invention maturity and company financing stage, project costs and company raises, unknown and failed evidence, and pitch approval and a relationship. These are inherited product constraints rather than external research findings. — [Product contract](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md).

### Inferences

- Retain four portfolio groups: basics; what exists and evidence; requested support and financial scope; public preview. Treat each group as a focused activity, with short related inputs. Do not create a separate page for every tiny field merely to imitate a government form. Test whether users need a visible four-step indicator and provide understandable back/continue controls. This applies the question-page principles to the existing editor. — [Question pages](https://design-system.service.gov.uk/patterns/question-pages/).
- A returning inventor's home should list outstanding tasks such as a revision response or incomplete saved draft. A partner starts with useful discovery and explicit active needs. Use “Menunggu Anda” and “Menunggu pihak lain” to express responsibility. Counters and charts need an actual decision to support; avoid an ornamental executive dashboard. This is proposed TemuRiset information architecture, grounded in its task flow. — [Product contract](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md).
- In funding forms, first ask what support is sought. For project funding show scope, duration and project amount. For company fundraising show company/proposed entity, total round target and desired individual contribution as distinct labelled fields. Reuse known invention details; never require the same company raise to be re-entered for a second linked invention. This is a product-specific application of avoiding redundant questions. — [Question pages](https://design-system.service.gov.uk/patterns/question-pages/), [product contract](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md).
- Discovery cards can show problem, existing solution, support sought, stage, a few reasons, a principal gap and one next action. A secondary detail explains rules, score bounds and evidence. Progressive detail must not conceal a blocking condition or important financial basis. — [Product contract](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md).

### Gaps

- No primary source establishes that exactly four steps or one fixed navigation layout is best for all inventors. The step grouping follows the PRD and needs formative testing with its users.
- No research here measures investor willingness to use this marketplace. Visual clarity cannot substitute for a genuinely useful supply-and-demand cohort.

## Which accessibility requirements and stronger product choices should be explicit?

### Takeaway

Target WCAG 2.2 AA for the rendered web experience and identify stronger product preferences separately. A token palette, screenshot or automated scan alone cannot establish conformance of complete pages and journeys.

### Cited Findings

- The opened WCAG 2.2 Recommendation is dated 12 December 2024. Relevant requirements include keyboard operation (2.1.1), non-color-only information (1.4.1), 200% text resizing (1.4.4), reflow at 320 CSS px for vertical content with a meaningful two-dimensional-layout exception (1.4.10), and 3:1 contrast for required control/state/graphic information with exceptions (1.4.11). Status messages need programmatic semantics without focus (4.1.3). AA conformance covers all A and AA criteria on full pages, rather than a handpicked checklist. — [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
- Normal text requires at least 4.5:1 contrast; large text permits 3:1. Inactive, incidental and logo text have specified exceptions. Large text is generally at least 18 pt, or 14 pt bold; a calculated ratio just below a threshold does not pass by rounding. — [Understanding contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
- AA criterion 2.5.8 has a 24 by 24 CSS px target minimum with spacing, equivalent-control, inline, user-agent and essential exceptions. Larger targets help usability; a 44 by 44 target belongs to the enhanced criterion and can be chosen as product guidance. — [Understanding target size minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
- AA focus-not-obscured requires a focused component not to be entirely hidden by author-created content. Avoiding any obscuration is a stronger outcome; sticky headers, footers and overlays need particular attention. — [Understanding focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).
- Disabling nonessential interaction-triggered motion is SC 2.3.3 at AAA. WAI describes eliminating unnecessary animation and honoring a reduced-motion preference as approaches; this criterion must not be described as an across-the-board AA rule. — [Understanding animation from interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html).

### Inferences

- Specify comfortable 44 px primary touch areas where practical, while testing the actual AA target rule and exceptions accurately. Compact secondary actions still need sufficient separation and a usable accessible name. Do not force crowded 24 px controls simply because that can meet a minimum. — [Target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
- Test common task views at 360 px and desktop 1280 px, plus the separate 320 CSS px reflow condition. Convert multi-column summaries into a reading order; keep date, amount, unit and status together. A wide evidence comparison table may have justified local two-dimensional scrolling, but that is not a justification for horizontal overflow of the whole application. — [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
- Name semantic color pairs and validate their actual combinations, including hover, focus, error and selected states. Do not use green/amber/red alone for PASS/UNKNOWN/FAIL. Use concise visible text and relevant icons; attach machine-readable status semantics to genuine changes. — [Contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
- Make reduced motion a TemuRiset requirement even where it exceeds AA: no parallax, decorative counters or animated page stacks; simplify transitions under the user's preference. Maintain useful saving/loading feedback as text instead of relying on movement. — [Motion guidance](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html).

### Gaps

- These notes do not assess a rendered implementation, screen-reader compatibility, translated content or a complete WCAG claim. The handoff should preserve PASS, FAIL, NOT RUN and BLOCKED as evidence states.
- An attractive disabled state may technically fall within a contrast exception yet remain hard to understand. Product testing still needs to explain why an action is unavailable.

## How should review, errors, dialogs and saved drafts behave?

### Takeaway

Treat review and recovery as part of the primary flow. Keep entered work, make errors addressable, and make consequential actions describe what will actually happen.

### Cited Findings

- GOV.UK's error-summary component calls for a focused summary linked to problematic answers, consistent messages beside those answers and concise explanations. Its particular component pattern uses the summary even for one validation error. That instruction belongs to this pattern rather than being a universal WCAG wording requirement. — [Error summary](https://design-system.service.gov.uk/components/error-summary/).
- The WAI modal-dialog pattern describes moving focus into a labelled dialog, containing Tab/Shift+Tab, Escape to close, an available close control and a logical focus return. Long structured content can initially focus a static heading; difficult-to-reverse actions may favor the least destructive option. The APG is implementation guidance, not automatic conformance evidence. — [Modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).

### Inferences

- After a failed form submission, keep values and move focus to a concise error summary with links to fields. Associate help and inline errors programmatically, use the same error wording in both locations and explain corrective action. Do not clear a multi-step editor or make users rediscover the failed step. — [Error-summary pattern](https://design-system.service.gov.uk/components/error-summary/).
- Autosave should expose “Menyimpan”, “Tersimpan” and “Belum tersimpan — Coba lagi”. Announce significant state changes without moving focus away from typing. A transient success toast is insufficient evidence of a committed save; draft failure must remain discoverable. This applies the PRD's save contract and WCAG status-message requirement. — [Product contract](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md), [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
- Preflight should review recipient/context, purpose, source versions, exact shared documents, financial basis and unresolved requirements. Provide direct change links returning to the same review context. The final button says “Kirim pitching”, with approval explicitly meaning discussion only. — [Check answers](https://design-system.service.gov.uk/patterns/check-answers/).
- Use a modal for a bounded confirmation, not a complete portfolio editor. A private-file sharing confirmation needs a labelled recipient and version list; it should not be a nested chain of dialogs. Preserve a logical return path when the initiating element disappears after withdrawal or archive. — [Modal-dialog guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).
- In relationship review, show the shared summary version, proposed public-field ceiling, each party's consent and the resulting intersection. Expansion and narrowing have different effects; the interface must not suggest that one party's confirmation can expose a disputed amount. This is the PRD's consent contract presented as a review task. — [Product contract](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md).

### Gaps

- Focus management must be checked in actual browser/assistive-technology combinations. A static mockup can document intended behavior but cannot prove that a modal traps focus or that a status change is announced.

## How should revisions and meeting negotiation remain understandable on small screens?

### Takeaway

Show the question, responsible actor and next action together. Keep complex business state in a coherent workspace instead of adding separate navigation destinations for every variation.

### Cited Findings

- The product contract requires itemized revision rounds with required/optional labels, honest inability/discussion answers, and recipient review. It also requires 2–5 proposed meeting slots, explicit acceptance, UTC storage, IANA display zones, alternatives and recoverable booking conflicts. — [Product contract](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md).
- GOV.UK's review pattern recommends relevant grouped content and edit links that return to the review. It does not prescribe a calendar grid or complex card dashboard for these tasks. — [Check answers](https://design-system.service.gov.uk/patterns/check-answers/).

### Inferences

- Give each revision item a clear heading, why it is requested, required/optional label, saved answer and selected evidence. Allow “Perlu diskusi” and “Belum dapat dipenuhi” without converting either into approval. Preserve other answers if one upload or validation fails. This applies grouped, correctable review to the PRD's itemized workflow. — [Product contract](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md).
- Use a readable slot list with full date, local time, duration and timezone. Distinguish temporary selection from “Konfirmasi waktu”. On a cross-zone preview, show the recipient's equivalent time as supporting information; do not show an unlabeled 09:00. After conflict, retain agenda and alternatives while offering a fresh selection. — [Product contract](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md).
- On mobile, stack the main task before the timeline and secondary evidence. Keep floating bars from obscuring fields or controls when the keyboard or zoom is active. Focused components must remain visible; the stronger product goal is to keep the whole active control and its help visible. — [Focus-not-obscured guidance](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).

### Gaps

- No source reviewed proves a particular slot-list layout best for this audience. The list is a bounded design recommendation based on the small 2–5-slot product contract, to be compared through task testing.

## What evidence should validate the design and what must remain unclaimed?

### Takeaway

Combine component checks, complete task walkthroughs and formative sessions with likely users. Keep measured observations separate from prototype simulations, engineering guarantees and population claims.

### Cited Findings

- GOV.UK describes moderated usability testing as observing people attempting specific tasks, often with think-aloud. It recommends likely users, clear neutral tasks that do not reveal the answer, a discussion guide and accessible sessions. It notes that dummy data can provide useful findings while missing contextual engagement, and that assistive-technology users often benefit from their own setup. The page was published 21 February 2017 and updated 3 October 2017; opened 31 October 2026. — [Moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing).

### Inferences

- Use the PRD's initial 5–8 participants as a formative plan, covering personal inventors, startup managers and investors/partners. It is a recruitment proposal, not a claim that this number discovers all problems or provides a statistically reliable completion percentage. Include keyboard, magnification and mobile conditions appropriate to recruited users. — [Moderated-test guidance](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing).
- Define tasks with observable outcomes: find a suitable investor, distinguish a company raise from a project budget, correct a missing preflight item, answer an unfulfillable revision honestly, negotiate the same instant across zones, and limit public relationship fields. Measure unassisted completion, errors, assistance, time and comprehension of approval-versus-funding. State sample sizes and incomplete outcomes. — [Moderated-test guidance](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing), [product contract](../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md).
- Design-system gates should test primitives and assembled patterns; application gates should rerun the full consuming journeys and exported artifact. A component passing contrast checks does not establish the placement, copy or focus order of a complete page. Record artifact/version, viewport/zoom, input method, expected result, actual evidence and limitation. — [WCAG conformance requirements](https://www.w3.org/TR/WCAG22/).

### Gaps

- No participants, task timings, device tests, source-code accessibility audit or exported interaction checks were performed. Nothing here supports a claimed funding conversion uplift or an achieved conformance level.
- Synthetic prototype actions cannot establish server authorization, atomic booking, idempotency, malware inspection or actual identity verification; those remain separate implementation acceptance evidence under the PRD.

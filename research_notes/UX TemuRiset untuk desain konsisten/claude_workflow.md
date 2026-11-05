# Claude Design workflow and evidence boundaries

Research accessed **31 October 2026, Asia/Jakarta**. Scope: official Claude/Anthropic documentation for a private TemuRiset design-system stage followed by a stateful responsive-web application prototype. Seven official pages were opened, including both Help Center and Academy explanations. The existing TemuRiset PRD supplies the product contract; these sources establish authoring-tool behavior, not product validation or proof that any artifact has been created.

## What does current Claude Design actually support?

### Takeaway

Write a capability-aware brief for the actual Claude surface the user opens. Current documentation describes Design artifacts in Claude conversations, the Artifacts area and Claude Code; an older standalone project workflow is no longer the only route. Design availability, design-system availability and organizational publishing permission are distinct. — [Claude Design getting started](https://support.claude.com/en/articles/14604416-get-started-with-claude-design); [design-system setup](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design).

### Cited Findings

- The getting-started guide describes conversational design generation, interactive prototypes, canvas iteration, reference uploads/codebase context and design-system import. It lists ZIP, standalone HTML and document-oriented exports, plus handoff to a local coding agent or Claude Code Web. These are documented offerings, not a guarantee that every export in a particular session preserves all interactions. — [Getting started](https://support.claude.com/en/articles/14604416-get-started-with-claude-design).
- The setup guide describes sources such as code, decks, brand files and product references. Existing React component systems can be brought in through `/design-sync`. Design systems are a beta capability with plan and administrator prerequisites, and administrators may limit publication/default-setting. Its older standalone instructions are explicitly marked as such. — [Set up a design system](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design).
- The migration article says standalone `claude.ai/design` closes on **14 December 2026**. Migration may involve organization-wide systems, preserve ownership/sharing settings and omit chats/comments. Its details are consequential and should not become an automatic step in a design-generation prompt. — [Move from standalone Design](https://support.claude.com/en/articles/17440474-move-from-standalone-claude-design-to-claude).
- General artifact documentation distinguishes current templates from legacy artifacts and documents export choices. It also notes that code execution/file creation capability is needed for artifacts. This supports checking the actual runtime rather than treating every chat as an identical design environment. — [What artifacts are](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them).

### Inferences

- Begin each TemuRiset prompt by asking Claude to report its actual authoring surface, supplied files and usable system/component mechanism. This is a proposed execution contract: continue with reversible private work when supported, and name unavailable capabilities precisely. Do not require the user to navigate a nonexistent screen or assert that a repository Markdown file registered a system. — Design recommendation informed by [getting started](https://support.claude.com/en/articles/14604416-get-started-with-claude-design).
- Keep three separate statuses: the product direction accepted by the user; the system/prototype authoring work requested in a future Claude session; and the runtime checks actually executed. For example, a private portable system can be usable even when a native Design-system artifact is unavailable, but its binding record must say portable reference rather than registered organizational default. — Proposed application of the capability distinctions in [setup](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design).
- The handoffs should not initiate migration, sharing, publication, organization-wide default changes or external service deployment. Those actions are outside this request to prepare reusable documentation. Mention the current migration page as a reference when applicable; avoid embedding a fragile click sequence into the main prompt. — Scope recommendation informed by the effects documented in [migration](https://support.claude.com/en/articles/17440474-move-from-standalone-claude-design-to-claude).

### Gaps

- No actual Claude account, plan, project or runtime was inspected. Capability visibility and successful imports/exports remain unverified. Documentation updates quickly; recheck the linked official pages if running the prompts later.
- These pages do not establish native mobile output, production server authorization, transaction safety or the availability of a general public Design API. The handoff should target the PRD's responsive web product and label backend simulation explicitly.

## How should the design-system-first handoff work?

### Takeaway

The system stage needs a short reusable overview, concrete token/component usage contracts, representative domain assemblies and a consuming sample. The later application must record which actual system revision it received. Visual similarity alone does not establish component reuse. — [Design-system Academy tutorial](https://academy.claude.com/tutorials/create-a-design-system-with-claude); [prototyping Academy tutorial](https://academy.claude.com/tutorials/using-claude-design-for-prototypes-and-ux).

### Cited Findings

- The system Academy tutorial documents an overview with an index, token and component reference files and machine-readable versions. It recommends a short overview with specific guidance in usage notes. It also describes actual component identification and says that previously created designs retain their own system copies until explicitly updated. These details justify a version/binding record rather than an automatic-propagation promise. — [Setting up a design system](https://academy.claude.com/tutorials/create-a-design-system-with-claude).
- The prototype tutorial distinguishes real components supplied to Claude from visually similar substitutes. It recommends naming components and pointing to the relevant source folder. Code-synced component copies need another sync after a library release. — [Using Claude for prototypes and UX](https://academy.claude.com/tutorials/using-claude-design-for-prototypes-and-ux).
- A newly created system is initially personal; organizational sharing/default-setting involves the organization's owner. The tutorial separates its default from a system already selected by a user. Therefore the presence of a default alone is insufficient evidence that the requested TemuRiset system is the selected one. — [Setting up a design system](https://academy.claude.com/tutorials/create-a-design-system-with-claude).

### Inferences

- Make the design-system handoff standalone: include TemuRiset's two personas, major objects, funding-versus-project distinction, evidence labels, disclosure/consent states, representative fictional data and the system's required patterns. It can summarize domain context without duplicating every backend endpoint. The application handoff should carry the complete canonical English PRD so it works without repository or earlier-chat access. This division is an authoring recommendation for this task.
- Request stable `TR.*` component identifiers and semantic tokens, usage notes, component/state inventory, a machine-readable token export, a manifest, a private workbench and validation results. These are proposed portable deliverables; they are not claims that a custom JSON schema is a Claude import standard or that all outputs can be registered automatically. Let the session adapt packaging to the actual supported surface. — Design application of the documented system/reference separation in [system Academy](https://academy.claude.com/tutorials/create-a-design-system-with-claude).
- Record system name, system version, source/artifact identifier when available, actual supply method, token/component inventory, supported theme, test status and deviations. A receiving app should report “registered system,” “imported source,” or “portable local reference” as applicable. If the intended artifact is missing, establish a clearly labelled local draft system before composing screens, with missing binding stated. Do not silently use a different organization default. — Proposed verification mechanism informed by [system setup](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design).
- Keep the system workbench bounded to primitives, domain components and pattern assemblies; it is not the full application. Use a representative discovery/preflight pattern, structured revision pattern, schedule negotiation pattern and relationship-confirmation pattern. These test whether visual states preserve the PRD's meanings without adding decorative analytics or a marketing website.

### Gaps

- No import format, bundled component implementation, token schema or artifact identifier has been produced in this task. Future output must document what was actually generated and successfully consumed.
- A named font is not proof that its file/license is supplied. A source component or token appearing in a manifest is not proof that the consuming prototype uses it. Both need inspection rather than assertion.

## How should the interactive application and exports be verified?

### Takeaway

Ask explicitly for a stateful working prototype, review complete journeys and test the exported result separately from the editor. Editor keyboard support, component-preview access and the generated application's accessibility are different surfaces. — [Prototyping tutorial](https://academy.claude.com/tutorials/using-claude-design-for-prototypes-and-ux); [keyboard/screen-reader guide](https://support.claude.com/en/articles/17457950-use-artifacts-with-a-keyboard-or-screen-reader).

### Cited Findings

- The prototype tutorial documents Play for clickable artboards and recommends whole-flow descriptions, empty/error/loading variants, clear artboard/component names and recorded design decisions for engineering. It describes continuing from actual designs in Claude Code and several export scopes. — [Using Claude for prototypes and UX](https://academy.claude.com/tutorials/using-claude-design-for-prototypes-and-ux).
- The setup Help page explicitly says live design-system component previews cannot be operated through Tab. This is a host limitation; it does not establish the keyboard behavior of a separately running generated component. — [Design-system setup](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design).
- Claude's keyboard guide describes navigation between the conversation, artifact panel and editor areas, including differences for legacy artifacts and browser shortcuts. The guide concerns the authoring host, not certification of content generated inside it. — [Keyboard and screen-reader guide](https://support.claude.com/en/articles/17457950-use-artifacts-with-a-keyboard-or-screen-reader).

### Inferences

- The application prompt should briefly map screens, then complete the agreed journeys without stopping at a plan: independent inventor→project pitch; startup→one raise supported by two inventions; partner revision→resubmission; slot alternatives/conflict recovery; relationship correction→both-party confirmation. Use the PRD's exact synthetic fixture values and statuses, not invented investors or outcomes. These are project-specific requirements from the local PRD.
- A mock service should provide one state authority for role changes, versions, decisions, grants and resets. Record which behaviors are simulated: email, login, file scanning, private downloads, background work, atomic booking and cross-user permission checks. A front-end permission-denied screen demonstrates the intended experience; it does not prove production enforcement.
- Request separate evidence records for editor Play, independently opened HTML/project exports, component binding and available accessibility checks. Each record needs expected result, actual result, tested surface/version and `pass`, `fail`, `not run` or `blocked`. Keep synthetic/mock provenance as a separate attribute; “simulated” is not a passing result.
- Use a separately runnable workbench or consuming prototype for keyboard/focus testing when the system editor cannot expose live previews to Tab. Mark inaccessible host-only checks blocked and continue the checks available in the generated web runtime. Do not claim that a screenshot, color calculation or an accessible editor proves rendered application compliance.
- Deliver routes/states/actions, component/token mapping, responsive behavior, the system binding/deviation record, mock-service ledger, fixture/reset instructions, export inventory and engineering notes. Portable source is requested where supported; PDF screenshots supplement rather than replace interactive output. This is an explicit handoff contract, not a guarantee that a particular export works without further checks.

### Gaps

- No prototype, export, usability session or accessibility test was executed. Backend guarantees and the product's 72 runtime acceptance scenarios remain untested by this research.
- Official product documentation does not guarantee that every editor interaction survives every export format or that an exported project is production-ready Next.js. Inspect the actual bundle, run its supported entry point and record any conversion required before engineering integration.

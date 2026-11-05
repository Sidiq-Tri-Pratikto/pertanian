# TemuRiset — reusable product base

TemuRiset helps inventors find investors and other partners who can advance their inventions. This package defines a generic base for independent individuals, startups, corporate teams, nonprofits, communities and researchers across sectors. It uses a reusable modular monolith and a lightweight product-family strategy: maintain common behavior once, then compose justified variations through configuration, capabilities and adapters.

The complete PRD is available in **Indonesian and English, version 1.1 dated 31 October 2026 (Asia/Jakarta)**. English is canonical for exact technical contracts; both editions represent the same requirements. The initial UI language is Indonesian and localization is configurable. The user has accepted the product and modular-monolith/reuse direction. Specific implementation defaults and unmeasured policies remain proposals where identified.

Each PRD contains 26 numbered sections, FR01–FR24 and AC01–AC72. All 72 runtime acceptance scenarios remain **NOT RUN**. The design-system handoff defines 26 component contracts and 12 gates; the application handoff adds 24 UX checks. These are future execution contracts, not completed components or passing tests. No TemuRiset system, prototype, backend, deployment, model benchmark or participant study was created by this documentation work.

## Design-system status

**Stage 1 now exists: TemuRiset Design System 1.0.0-draft** in [design-system](design-system/). It holds 104 tokens, the 26 contracted `TR.*` components plus five additions, four pattern assemblies, a workbench, a consuming sample and validation evidence. Start with the [brand book](design-system/project/README.md), the [UX principles](design-system/project/guide/02-ux-principles.md) and the [validation report](design-system/project/guide/05-validation-report.md). A private mirror is at [the artifact](https://claude.ai/artifact/KU4iHKHaVL7QgL8bhSgfWV).

It is a draft, not owner-approved, and a portable local reference rather than a registered Claude system. Screen readers, participants, the artifact page and every AC scenario remain unverified. To run the workbench from this repository:

```bash
python3 -m http.server 8788 --bind 127.0.0.1 --directory docs/generic/temuriset/design-system
```

Then open `http://127.0.0.1:8788/workbench/index.html`. After changing tokens, components or `tools/catalog.mjs`, run `node tools/build.mjs` in that folder.

## Application prototype status

**Stage 2 now exists as a front-end simulation** in [app-prototype](app-prototype/), with a private [playable canvas](https://claude.ai/artifact/HMXtf8NFdYuhEjeKoq9ekJ). It covers S01–S18, all five journeys and fixtures F01–F06 on one local service. Start with [DESIGN_HANDOFF.md](app-prototype/DESIGN_HANDOFF.md), which holds the route map, ledger and validation results. It has no backend. Hosted editor Play is unverified, and all 72 acceptance scenarios remain NOT RUN.

## Application base

The real application starts at [applications/generic/temuriset](../../../applications/generic/temuriset/README.md): a Next.js web client and FastAPI API generated from product-starter-wdd, with "Segera hadir" for every planned feature. Its [roadmap](../../../applications/generic/temuriset/docs/roadmap/README.md) splits the remaining work into specs 003–045, one pull request each.

## Package and reading order

| Document | Purpose |
|---|---|
| [PRD Bahasa Indonesia v1.1](01_PRD_TemuRiset_Generic_ID.md) | Complete Indonesian edition with the same domain, UX, API, architecture and acceptance contract |
| [Canonical English PRD v1.1](01_PRD_TemuRiset_Generic_EN.md) | Exact technical authority, accepted architecture direction and detailed implementation contract |
| [02 — Application handoff EN](02_Claude_Design_TemuRiset_EN.md) | Stage 2: all product context, screen/journey/state contracts, fixtures, mock ledger, UX checks and complete canonical PRD snapshot |
| [03 — Application prompt EN](03_Prompt_Claude_Design_EN.md) | Ready-copy prompt for the application stage after the system/reference is available |
| [04 — Design-system handoff EN](04_Claude_Design_System_TemuRiset_EN.md) | Stage 1: standalone product context, tokens, component/state contracts, workbench, patterns, validation and binding |
| [05 — Design-system prompt EN](05_Prompt_Claude_Design_System_EN.md) | Ready-copy prompt to create the system and bounded workbench using file 04 |

Read either PRD before design or implementation. The [client extension template](CLIENT_EXTENSION_TEMPLATE.md) records actual differences against a pinned base release. The [architecture discussion](../../../reports/Reusable%20TemuRiset%20invention%20platform.md) and [UX/design-system research](../../../reports/UX%20TemuRiset%20untuk%20desain%20konsisten.md) explain the decisions and evidence limits. Detailed notes are available for [product/reuse](../../../research_notes/Reusable%20TemuRiset%20invention%20platform/) and [UX/Claude workflow](../../../research_notes/UX%20TemuRiset%20untuk%20desain%20konsisten/).

## Claude Design execution order

1. **Create the system first:** attach only file **04**, then copy the marked prompt from **05**. Complete TemuRiset Design System, initially 1.0.0-draft, its token/component reference, four bounded pattern assemblies, workbench and consuming sample. This stage does not build the full application.
2. **Keep the actual result:** record system name/version, real source/artifact identifier when available, actual supply/import method, token/component inventory, review status and validation evidence. Export a portable guide/tokens/manifest/source where supported. Registration or an organization-wide default must not be assumed.
3. **Build the application:** attach file **02**, supply/select/import that actual system or portable reference using the session's supported capabilities, and copy prompt **03**. The application records its binding/version and any local components or deviations. If the intended system is unavailable, it establishes a clearly labelled local draft before screens and records the missing binding.
4. **Inspect both surfaces:** complete five connected journeys in editor Play and inspect supported exported artifacts independently. Record PASS, FAIL, NOT RUN or BLOCKED with actual surface/version evidence. Mock provenance does not mean a test passed, and a front-end journey cannot establish production ACL, file scanning or database booking.

The order is **04 + 05 → actual system/reference and version → 02 + 03**. File numbering keeps the package recognizable while the explicit order controls execution. File 04 is standalone for system creation; file 02 is standalone for product understanding. The actual preceding system is still needed to claim real component binding. Follow the Claude capabilities actually available rather than an assumed menu or automatic synchronization route.

The application handoff embeds the complete canonical EN v1.1 byte-for-byte, including the final newline, between marked snapshot boundaries. Its source SHA-256 is **df0af1a6cad4857681bdd548d62f6afe034fc37ae1a4bfa21a0dd50cbcd4ffa4**. The copied prompt blocks also match their separate prompt files exactly. Preparing those copies does not register a system or create a prototype.

## What was generalized

The available earlier PRD already had strong generic workflows: portfolios, needs, matching, preflight, briefs, decisions, itemized revisions, discussion, scheduling and separate relationship confirmation. Its institution-first pilot, sector-specific examples, review gates and demonstration assumptions did not constitute a standalone cross-sector base. The new PRD removes those assumptions from the product definition and replaces them with optional organization review, governed requirements and fictional multi-sector acceptance fixtures.

The product now explicitly supports personal inventor and individual investor contexts without mandatory institutions or companies. Two public personas remain: Inventor and Investor/Partner. Moderation and review are scoped permissions. Creator, managing party, claimed rights holder, legal entity and authority to act remain separate. A patent, video, maturity scale, revenue figure or registered business is not a universal prerequisite; a particular recipient can state justified requirements for its own opportunity.

Investment discovery is first-class. Partners publish mandates, offered support, accepted stages, active intake and preferred routes. Company financing stage is separate from invention maturity. A FundingRequest represents one venture/company raise and can reference several inventions, while ProjectBudget belongs to a particular development scope. The platform compares investor check ranges with intended contribution ranges where known, rather than rejecting a suitable contributor because its check cannot cover the whole round. Money never implies valuation or an equity percentage.

The detailed contract preserves unknown versus failed evidence, current versus planned functionality, pitch approval versus partnership, proposal versus booking and source-reported versus reviewed claims. It adds explicit confidentiality behavior for search, AI, caches, queued work and exports. Historical snapshots retain truthful context without granting permanent access to revoked evidence.

## Why this architecture fits

The accepted direction is **a reusable invention-partnership core implemented as a modular monolith**. A product-family strategy describes maintained reuse across related offerings. White-label describes another brand presenting the product. SaaS describes hosted service delivery. Multitenancy describes runtime customer sharing/isolation. These decisions can coexist but do not require one another; the architecture report provides the supporting sources and tradeoffs.

The base uses one server authority for evidence, monetary semantics, matching, decisions, booking and consent. A web client, imports and optional workers call its use cases. The initial proposal uses FastAPI/Python, Next.js/TypeScript, PostgreSQL and private object storage. Internal module boundaries and contracts matter; a service for each module, dynamic plugin loader and universal workflow language are unnecessary starting obligations.

Concrete variation examples are a brand/locale change through validated configuration; a repeatable organization-review gate through a tested capability; a catalog or calendar provider through an adapter; and a sector checklist through governed versioned data. Changes to private-file authorization or the meaning of company equity are base-contract changes, never client toggles. An unrelated future product can share proven technical components without inheriting the invention domain.

## How to extend and keep fixes shared

Start from one maintained source release and a client addendum. Describe the user problem and exact changed requirements, classify each difference and add only the required configuration, capability or adapter. Define prerequisites and disabled behavior, then test the base invariants and the client's complete journey. Avoid client-name branches inside rules and permanent source copies that silently stop receiving fixes.

A shared fix is reviewed, tested against supported compositions, released and deliberately rolled out to each environment. Record code/configuration/adapter/schema versions, migration evidence, deployment owner and rollback or forward-repair plan. Separate client deployments can share source while keeping identities, data and secrets separate; they do not automatically share a marketplace. Pooled SaaS or federation requires an explicit later design.

For cloud/local continuity, keep the PRD, addendum, implementation decisions and release inventory in the repository at a known commit. Commit/push/pull transfers the maintained files; a chat attachment is not a source dependency. No Git commit or push is part of this package creation, so review and synchronize the resulting working-tree changes through the normal repository workflow.

## Source provenance and assessment limits

The available baseline was **TemuRiset PRD v1.0, 20 October 2026**, attached to chat **6ad6f1b2-f904-83ec-9bd2-0794754bc8b1**. Its SHA-256 is **ee847e2a91a68afa27abce9eca02810476bc1c3d6421cd660b985ac0c9129b61**. This generic document is self-contained and does not require that temporary attachment to be present.

The audit inspected current branch f/init-base-hemat-daya at **1637a2d8af2dc8daf95a1441ba3a8158db21e481**, freshly fetched main at **3604916702dbe6aca20b9bbeac0da03121edcb48**, and freshly fetched chore/init-kartika at **569234f49381ce13f371f74b16bc82ab05648180**. None contained a TemuRiset PRD filename. A proposal/style mention in another project's documentation is not a TemuRiset product specification. The package therefore does not claim to update a newer repository PRD or preserve an unavailable version. No branch switch or merge was needed.

The linked HematDaya discussion and existing architecture research informed the reuse approach. The subsequent accepted-direction revision produced complete PRD ID/EN v1.1 and the design-system-first package. UX research on 31 October 2026 used opened primary W3C/WAI, GOV.UK, USWDS, Carbon, DTCG and official Claude sources. They support standards distinctions and authoring patterns, not market demand, investment performance or production readiness. The main outstanding evidence is the first actual system/prototype, inventor–investor cohort, operational policy, implementation tests and one genuine client variation.

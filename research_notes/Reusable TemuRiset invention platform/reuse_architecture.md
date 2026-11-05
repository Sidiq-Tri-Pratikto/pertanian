# Reusable TemuRiset invention partnership architecture

Research date: 31 October 2026 (Asia/Jakarta). All external sources below were opened on that date. This is architectural research and a proposed design, not a code audit or proof that any reusable TemuRiset implementation already exists. The earlier HematDaya architecture report supplied background questions; the primary sources cited here were checked again.

## What kind of reuse system fits this goal?

### Takeaway

Describe TemuRiset as a **reusable invention-partnership product core**, implemented initially as a **modular monolith**, with a lightweight **product-family strategy**. White-label branding, hosted SaaS delivery, and multitenancy are independent choices rather than alternative names for the same architecture.

### Cited Findings

- SEI defines a software product line through related systems, managed common features, common core assets, and a prescribed production approach. Its material includes domain scoping, requirements, architecture, configuration management, and management responsibilities. The definition concerns deliberate, maintained reuse rather than similarity between independently developed applications. — [SEI, Software Product Lines Curriculum](https://www.sei.cmu.edu/library/software-product-lines-curriculum/)
- Shopify describes white labeling as another business selling a supplier's product under its own brand, including software whose core capabilities are repackaged by other companies. This establishes commercial terminology, not a security or deployment specification. — [Shopify, White Label Guide](https://www.shopify.com/blog/white-label)
- Microsoft distinguishes SaaS as a business and delivery model from multitenancy as architectural sharing between tenants. A SaaS vendor hosts and maintains its product; a multitenant design shares at least some components, and can exist outside SaaS. — [Microsoft, SaaS and multitenant solution architecture](https://learn.microsoft.com/en-us/azure/architecture/guide/saas-multitenant-solution-architecture/)
- GitHub repository templates generate a new project's files and structure. A generated repository begins with one commit, whereas a fork carries its parent's commit history; template-generated branches have unrelated histories. — [GitHub, Creating a repository from a template](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)

### Inferences

- **Recommended product boundary:** reusable behavior means helping invention owners and potential supporters discover one another, disclose information with consent, evaluate a collaboration, negotiate next steps, and record an agreed relationship. A school research office, independent inventor community, incubator, and company innovation program can be variants when these jobs and their fundamental meaning remain the same. This boundary is our design recommendation, applying SEI's related-product criterion; it does not promise universal reuse across every future challenge. — [SEI](https://www.sei.cmu.edu/library/software-product-lines-curriculum/)
- A client changing the product name, logo, colors, domain, or contact copy creates a white-label presentation. A client adding a technical-review gate changes a workflow capability. Neither automatically requires multiple customers to share a database or a runtime. Keep these decisions separate in the PRD. — [Shopify](https://www.shopify.com/blog/white-label); [Microsoft](https://learn.microsoft.com/en-us/azure/architecture/guide/saas-multitenant-solution-architecture/)
- Use one maintained source release for related variants. A template is appropriate for an intentionally independent future product, but must not be advertised as a continuing dependency that automatically receives fixes. A permanent client fork requires explicit maintenance and backport ownership. — [GitHub](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)
- Reuse HematDaya's delivery discipline, configuration separation, and modularity ideas. Do not force electricity-accounting entities or rules into an invention marketplace. For an unrelated future challenge, reuse proven technical components or a starter separately, and establish that product's own domain model. — [SEI](https://www.sei.cmu.edu/library/software-product-lines-curriculum/)

### Gaps

- No source establishes a percentage of TemuRiset code that will be reusable or a minimum number of clients at which a product-family framework becomes worthwhile. Neither financial savings nor faster delivery has been measured for this project.
- White-label is useful business vocabulary, not evidence that licensing, intellectual-property ownership, client support, or hosted-service responsibilities have already been agreed.

## How should the shared application and client variation be structured?

### Takeaway

Build one application with enforced internal domain boundaries and a small, versioned composition definition. Add an ordinary module, adapter, or configuration entry for a demonstrated variation; avoid a universal workflow language or dynamic plugin marketplace.

### Cited Findings

- Simon Brown distinguishes modularity from deployment units and illustrates components with narrow public interfaces and hidden repositories/implementation details. His examples show how language visibility can prevent unrelated code from bypassing a component boundary. Folder names alone are insufficient evidence of that boundary. — [Brown, Modular monolith](https://simonbrown.je/modular-monolith/)
- Fowler argues that microservices carry an operational premium and that stable service boundaries are difficult to identify initially. His monolith-first advice is explicitly based on anecdotal evidence and is tentative; a monolith cannot be assumed easy to decompose later. — [Fowler, Monolith First](https://martinfowler.com/bliki/MonolithFirst.html)
- Microsoft advises a common codebase and consistent automated deployment even when tenant resources are dedicated. Its deployment guidance distinguishes temporary feature rollout flags from persistent customer entitlements. — [Microsoft, Deployment and configuration approaches](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/deployment-configuration)

### Inferences

The following is a proposed TemuRiset decomposition, not a source-mandated module list:

1. **Identity and access:** accounts, organization/workspace membership, capabilities, authorization policy and access grants.
2. **Invention portfolio and evidence:** invention identity, immutable submitted versions, contributors, declared ownership/authority, public summaries, private evidence, and scoped budgets.
3. **Discovery and matching:** published opportunity profiles, eligible catalog projections, explicit requirements, reproducible ranking runs, reasons and gaps.
4. **Pitch collaboration:** submission snapshots, decisions, itemized revisions, discussion tasks and meeting negotiations.
5. **Partnership records:** the separate proposal/confirmation process, legal-entity references where applicable, publicity consent and history.
6. **Operations and integrations:** notifications/outbox, import/export, storage, model/provider adapters, audit and retention operations.

Dependencies should follow declared use-case interfaces. Domain modules own their rules; HTTP handlers, workers, importers, and scheduled tasks call those same use cases. The optional worker can run separately for long jobs while shipping the same application source and release. This is deployment composition, not an obligation to create a network service for each module. Architecture checks must prevent cross-module repository access or cycles where the implementation language cannot prevent them directly. — Design synthesis from [Brown](https://simonbrown.je/modular-monolith/)

Separate three types of variation:

- **Configuration:** branding, supported locale/currency, enabled tested capabilities, approved taxonomy/checklist identifiers, review-policy selection and adapter selection. Validate a schema and reject incompatible combinations at startup or publication.
- **Capability module:** a repeatable business variation such as organization publication review, structured technical diligence, or a program-specific application gate. It has explicit prerequisites, versioned contract, tests, owner, and defined disabled behavior.
- **Adapter:** a concrete boundary to an identity provider, institution catalog, file store, email service, model runtime, or calendar. Normalize provider details before domain use; do not let provider responses mutate business states without validation.

Store secrets in deployment secret storage and refer to them by identifiers; a composition file is not a place for credentials. Record source release, composition/schema version, enabled module versions, adapter versions, and database migration level for each environment. Feature visibility is not authorization: server use cases must independently reject disabled or unauthorized operations. Persistent client access should not depend on temporary rollout flags. — Original design proposal informed by [Microsoft deployment guidance](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/deployment-configuration)

For a new requirement, classify it before changing the core: data/content only; brand/configuration; optional reusable capability; external adapter; or a different product. A sector-specific checklist is data governed by an accountable reviewer. It must not make an academic affiliation, patent, universal readiness scale, or one jurisdiction's regulatory evidence mandatory for all inventors. Preserve shared invariants while allowing justified requirements for a particular opportunity. — Proposed product-family application of [SEI](https://www.sei.cmu.edu/library/software-product-lines-curriculum/)

### Gaps

- This research has not inspected TemuRiset implementation code, dependencies, import graphs, module visibility, existing CI, or operational load. Module names and stack details remain proposals to validate through the first working slice.
- No evidence currently justifies microservices, a public plugin SDK, dynamic arbitrary code loading, a generalized no-code workflow engine, a package registry, or separate release machinery for every internal module.

## How do deployment isolation and marketplace sharing coexist?

### Takeaway

An organization is a business actor; a workspace is an operational collaboration context; a tenant is a deployment/customer isolation boundary chosen by the delivery model. Public discovery and authorized two-party collaboration must be explicitly modeled rather than accidentally permitted or prohibited by a simplistic organization filter.

### Cited Findings

- OWASP requires server-verified context, resource authorization, and isolation across database, cache, queues, files and logging. It recognizes intentionally global resources and explicitly authorized cross-tenant paths; client-supplied tenant selectors and opaque IDs are not authorization proof. — [OWASP, Multi-Tenant Application Security](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)
- Microsoft's tenancy guidance leaves the tenant definition to the product's business model; shared architecture need not mean every component is pooled. — [Microsoft, SaaS and multitenant solution architecture](https://learn.microsoft.com/en-us/azure/architecture/guide/saas-multitenant-solution-architecture/)

### Inferences

For the initial product, specify one marketplace deployment with many independent inventors and organizations, plus object-level authorization. Calling every organization a mutually sealed tenant would conflict with the very purpose of browsing published inventions and collaborating across organizations. The correct rule is intentional visibility: approved public catalog projections can be discoverable, organization-private work stays private, and a pitch room grants only its defined parties access to selected information. — Proposed policy derived from [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)

Keep `Account`, `Organization`, `Membership`, `Workspace`, `CatalogVisibility`, and `AccessGrant` conceptually distinct. This does not require six new services or a separate database for every concept. A single person may belong to several organizations; changing the selected organization does not automatically grant access to every invention or document. Independent inventors must have a supported personal ownership context. — Proposed domain design, applying [Microsoft tenancy definitions](https://learn.microsoft.com/en-us/azure/architecture/guide/saas-multitenant-solution-architecture/)

For a client requiring an isolated deployment, run the same supported source release with separate database/storage/secrets and client composition. That deployment is a separate information universe by default: an investor account, listing, private room or permission in another deployment must not magically appear there. Cross-deployment discovery/federation needs a later explicit contract for owner consent, publication scope, provenance, identity mapping, updates and withdrawal. Do not promise a global network simply because all deployments reuse code. — Proposed boundary, informed by [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)

If pooled hosted tenants are later commercially justified, make the boundary explicit in queries, retrieval indexes, derived previews, AI inputs, job payloads, cache keys, idempotency records, exports, audit permissions and restores. Recheck current permission for delayed work. Add negative tests across two tenants and positive tests for the precise publication and collaboration paths intentionally allowed. — Proposed acceptance requirements based on [OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)

### Gaps

- The desired hosting model, regional requirements, tenant billing, client contracts, identity federation, and cross-deployment catalog economics are unknown. No capacity, price or isolation claim is validated.
- Dedicated deployment is a pragmatic starting option for distinct clients, not proof of security. Its organization-private paths, backup operations and external sharing still require access controls and tests.

## How does a new client receive capabilities and later fixes safely?

### Takeaway

Maintained reuse needs an explicit derivation and upgrade process. Sharing source is only the beginning; each supported configuration must remain testable, deployable, migratable and observable.

### Cited Findings

- Microsoft advises planning customer update policies, supported-version limits, emergency security fixes, rollback responsibility, and health monitoring. It also calls for visibility into deployed code/infrastructure/features and describes progressive rollout strategies. — [Microsoft, Updating a multitenant solution](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/updates)
- Semantic Versioning requires a declared public API and immutable released versions. Major, minor and patch changes communicate incompatible changes, compatible functionality and compatible bug fixes respectively. Version numbering does not itself perform upgrades. — [Semantic Versioning 2.0.0](https://semver.org/)

### Inferences

Use this proposed process for the next related challenge/client:

1. Write a short requirements delta against the generic PRD. Identify preserved invariants, actual workflow changes, data owners and integration permissions.
2. Choose an existing supported composition where possible. Add the smallest missing configuration, capability or adapter on a normal short-lived development branch; do not create a permanent client fork as the default delivery mechanism.
3. Create a named client composition and representative fixtures. Its private secrets and private production data stay outside source control.
4. Run core invariants, authorization negatives, adapter contract fixtures, and end-to-end journeys for each officially supported composition. Reject unsupported combinations instead of advertising every possible permutation.
5. Build an immutable release, document migration prerequisites, rehearse migrations and recovery against a protected copy, and record the exact deployed version inventory.
6. Roll out to a test deployment and then the chosen client window, checking health and critical journeys. A source-level fix is not delivered until deployment verification succeeds.
7. Keep a documented support window and emergency security-update policy. Capture client feedback as shared product changes when the behavior belongs in the family.

This process is original operational synthesis of [Microsoft update guidance](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/updates) and [Semantic Versioning](https://semver.org/), not a claim those sources prescribe this exact seven-step workflow.

For schema changes, prefer a staged compatible transition: add the new shape, deploy compatible reading/writing, backfill with verification, switch use cases, and remove obsolete shape only after all supported consumers have moved. A destructive migration cannot safely be undone merely by rolling back the application binary. Define recovery/forward-fix procedures and test a backup restore before production reliance. Keep migration level and composition compatibility in the release inventory. — Proposed project acceptance criteria; [Microsoft's update guidance](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/updates) establishes the need to plan code/schema updates and rollback, not the exact database sequence.

Start with one complete vertical slice—publish an invention, discover a compatible partner, submit a scoped pitch, answer revisions, confirm a meeting and separately confirm a partnership—and a second genuinely different configuration. Demonstrating unchanged domain rules and a clean extension in those two compositions is stronger evidence of reuse than extensive abstraction diagrams. Extract independently versioned shared packages only if another independently released application actually needs that boundary. — Design recommendation informed by [Brown](https://simonbrown.je/modular-monolith/) and the limits in [Fowler](https://martinfowler.com/bliki/MonolithFirst.html)

### Gaps

- Migration compatibility, deploy/rollback scripts, restoration, application behavior, cross-organization authorization, and configuration combinations have not been executed or verified by this research.
- No source establishes a universally safe support window, client-count trigger for pooling, or numerical point at which a module must become a microservice. Use measured operational and ownership needs rather than arbitrary thresholds.

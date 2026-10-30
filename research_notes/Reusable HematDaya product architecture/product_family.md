# Product family taxonomy for a reusable HematDaya base

## Which label best describes the intended reuse?

### Takeaway
Recommendation: describe the immediate technical goal as **a reusable, modular application base**, with **a product-family strategy** for related future products. “Software product line” is the closest established engineering concept once the team deliberately maintains common assets and derives variants through agreed variation points; white-label, SaaS, and multitenancy describe other dimensions and need not be implemented to achieve reuse.

### Cited Findings
- The Software Engineering Institute (SEI) defines a software product line through related systems, shared and managed features, common core assets, and a prescribed production approach. It explicitly describes this as planned strategic reuse, rather than merely writing related applications. The curriculum includes core-asset development, product development, management, scope, and configuration management. Published November 20, 2020; opened October 21, 2026. — [SEI, Software Product Lines Curriculum](https://www.sei.cmu.edu/library/software-product-lines-curriculum/)
- White-label describes a supplier producing something other businesses offer under their own brands. Shopify specifically includes software: common capabilities can be repackaged and sold by other companies with their branding and potentially additional services. This source establishes the commercial usage, not an architectural standard. Updated September 18, 2026; opened October 21, 2026. — [Shopify, White Label Guide](https://www.shopify.com/blog/white-label)
- Microsoft distinguishes SaaS as a business/delivery model from multitenancy as an architectural concept. In SaaS the vendor hosts and maintains the application. Its architecture guidance defines multitenancy through sharing components across customer or organizational tenants; every component need not be shared, and multitenancy is possible outside SaaS. Updated December 16, 2025; opened October 21, 2026. — [Azure Architecture Center, SaaS and multitenant solution architecture](https://learn.microsoft.com/en-us/azure/architecture/guide/saas-multitenant-solution-architecture/)

### Inferences
- These terms are compatible rather than mutually exclusive: a product family may use a modular common base, offer white-label editions, and later be delivered as SaaS with shared or dedicated resources. Choosing one word does not determine all the other choices.
- HematDaya's stated goal—maintain one solid electricity monitoring/advice base, then adapt it for household, industrial, client, and challenge contexts—fits product-family thinking more closely than “white-label SaaS.” This is an interpretation of the goal against the SEI criteria, not a finding that the existing repository already implements a formal product line. — [SEI](https://www.sei.cmu.edu/library/software-product-lines-curriculum/)
- **White-label** becomes relevant when a client or partner wants to present the application under its own identity. Reusing the same backend for household and industrial workflows can involve functional differences beyond branding, so white-label alone understates the intended reuse. — [Shopify](https://www.shopify.com/blog/white-label)
- **Platform** can be useful informal language for the common foundation, but the reviewed sources do not establish that this goal needs an extensible platform product, public SDK, plugin marketplace, or platform team. For the current discussion, “reusable application base” makes a smaller and clearer commitment.
- A single codebase deployed separately for several projects is source reuse. It does not, by itself, demonstrate the component sharing between running tenants described by Microsoft, nor that the vendor operates a SaaS service. Use precise deployment descriptions if the project later reaches that point. — [Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/guide/saas-multitenant-solution-architecture/)

### Gaps
- No repository architecture audit was performed for this assignment, so modularity, present variation points, and readiness to share production code remain unverified.
- “Reusable modular application” and “lightweight product family” are practical descriptions in this recommendation, not asserted formal certifications. No primary source reviewed establishes a universal boundary where an ordinary reusable application becomes a product platform.

## How does maintained reuse differ from a template or fork?

### Takeaway
A template helps start another project; maintained common assets help improve several products together. The important decision is whether future projects should continue receiving the same fixes and capabilities, rather than whether their first commit comes from the same repository.

### Cited Findings
- GitHub templates generate new repositories from existing structure and files. A generated repository begins with one commit, while a fork includes its parent's commit history. GitHub describes templates as a fast start for a new project and forks as potentially a way to contribute to an existing one. Template-generated branches have unrelated histories. Opened October 21, 2026; the page does not display a publication date. — [GitHub Docs, Creating a repository from a template](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)
- SEI's product-line concept includes an ongoing managed common asset set and a defined approach for developing related products. This distinguishes a continuing family-development practice from merely taking a starting copy. — [SEI](https://www.sei.cmu.edu/library/software-product-lines-curriculum/)

### Inferences
- If a challenge project will quickly become unrelated and is expected to be maintained independently, a template or deliberate copy can be sufficient. Its value is setup speed; it should not be presented as automatically distributing subsequent fixes. This recommendation follows GitHub's template semantics. — [GitHub Docs](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)
- If future client applications should repeatedly receive bug fixes, security fixes, calculation changes, and shared UX improvements, prefer an identifiable maintained common source and an explicit way to consume its changes. A template alone does not supply that maintenance process. — [SEI](https://www.sei.cmu.edu/library/software-product-lines-curriculum/); [GitHub Docs](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)
- A fork can retain lineage and enable Git-based merging, but it still requires decisions about what stays shared and how divergent changes are reconciled. A growing set of permanent client forks should therefore be treated as a maintenance choice with costs, not the product-family strategy itself.
- There is no need to select a package registry, monorepo, plugin loader, or formal feature-model tool during this PRD discussion. First establish which behavior truly repeats, which differences are expected, and which party maintains each delivered project. Repository mechanics should follow those requirements.

### Gaps
- This research does not compare the repository's package tooling or release workflows, so it cannot choose between in-repository modules, versioned packages, or maintained forks for implementation.
- No justified numerical threshold for “enough projects to extract a shared package” was found. Any fixed count would be a heuristic rather than established evidence.

## What should a small team adopt now, and what should wait?

### Takeaway
Use product-line thinking now to clarify the common product and real differences. Implement only the reusable boundaries required by the first working application, then strengthen them when a concrete second use case reveals a real need.

### Cited Findings
- Martin Fowler argues that managing multiple services adds a premium that can slow simpler applications, and that service boundaries are difficult to identify at a project's start. He recommends initially learning boundaries inside a monolith. He also explicitly calls the evidence anecdotal and his advice tentative; modularity does not guarantee easy later decomposition. Published June 3, 2015; opened October 21, 2026. — [Martin Fowler, Monolith First](https://martinfowler.com/bliki/MonolithFirst.html)
- SEI's curriculum treats product-line practice as both business and engineering work and notes that the fundamentals should be adapted to the organization's context. It does not prescribe that every adopting team build a large framework first. — [SEI](https://www.sei.cmu.edu/library/software-product-lines-curriculum/)

### Inferences
- **Now:** make the generic PRD stand on the electricity-monitoring/advice problem, its intended users, outcomes, and acceptance criteria. Treat UII, a hackathon, or a particular challenge as one possible deployment/project context rather than the reusable product's defining requirement. This is an editorial recommendation from the assigned objective, not a claim from an external source.
- **Now:** describe a shared core plus narrowly defined variations. Potential categories to validate are branding/copy, demonstration data, data-source integration, and genuinely different domain workflows. These are candidates for discovery, not requirements to build all at once.
- **When a second real project appears:** check which behavior remains identical, which varies through simple data/configuration, and which deserves a separate domain module. Maintain a short record of these decisions and the shared release being used. This is the smallest practical application of SEI's managed commonality and defined production approach. — [SEI](https://www.sei.cmu.edu/library/software-product-lines-curriculum/)
- **When branding is requested:** add the specific branding variation and call that offering white-label if another business will present it as its own. Do not assume it requires pooled hosting. — [Shopify](https://www.shopify.com/blog/white-label)
- **When the business chooses ongoing hosted service delivery to distinct customers:** assess tenants, access isolation, operations, and whether resources should be shared or dedicated. That is the point at which SaaS/multitenancy decisions become necessary. They are separate from keeping a reusable source base. — [Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/guide/saas-multitenant-solution-architecture/)
- **Wait:** microservices, a general plugin framework, runtime tenant provisioning, billing infrastructure, broad feature-flag systems, and speculative industrial modules. None follows from the reuse goal alone; implement them only when a concrete requirement justifies their maintenance cost. The microservices caution is supported by Fowler's argument, with the anecdotal-evidence limitation retained. — [Martin Fowler](https://martinfowler.com/bliki/MonolithFirst.html)

### Gaps
- No measured cost, time saving, scale forecast, team-capacity estimate, or revenue forecast supports a detailed ROI claim for HematDaya. Do not transfer dramatic SEI case-study gains into this project's forecast.
- Household and industrial electricity use may require different domain and hardware validation; those details are outside this taxonomy assignment. A common codebase does not prove that one set of product assumptions is appropriate for both.
- PRD, source code, hardware integration, deployment, license ownership, and production security were not changed or validated here. The main risk is turning an appropriate reuse ambition into speculative infrastructure before a second concrete use case exists.

# Indonesian SNA implementations and reusable product options

Research cutoff: 26 October 2026, Asia/Jakarta. Sources were prioritised by proximity to the claim: institutional activity reports, vendors describing their own offerings, and author/institution research publications. “Not established in the pages reviewed” describes a public-documentation gap; it does not prove absence from private products or government systems. The five product designs are proposals, not observed deployments or measured results.

## Which SNA capabilities already exist in Indonesia, including TNI?

### Takeaway
Social Network Analysis is already offered commercially in Indonesia, studied in disaster communication and inter-organisational collaboration, and explicitly documented in TNI activity. A generic network map, community chart, influencer ranking or defence label is therefore weak differentiation. The narrower opportunity is an auditable workflow around observed relationships, data coverage, and defensible interpretation.

### Cited Findings

| Source and evidence grade | What the source establishes | What it does not establish |
|---|---|---|
| **TNI/Puspen activity report, 17 October 2023 — institutional operational report** | The AIS Forum taskforce report explicitly says Satgas Siber TNI was conducting SNA monitoring after the event. This is direct evidence that SNA activity was already used by TNI in a particular operation. The article also describes communications activities; those are context, not the recommended product workflow. [PPID TNI](https://ppid.tni.mil.id/view/32436996/ktt-ais-forum-telah-berakhir-namun-tidak-untuk-pengamanannya.html) | It does not identify software, graph construction, model accuracy, current deployment, contracts or access rights. Direct web fetch returned 502; the official indexed result provided the full article text and date. Avoid claiming a particular TNI software platform was verified. |
| **TNI AD/Dispenad, 10 July 2025 — institutional training/management statement** | Reporting on a 7 July evaluation meeting, the official article explicitly calls for personnel to master SNA to evaluate publication effectiveness. This confirms organisational recognition of the method and a public-communication use case. [PPID TNI AD](https://ppid.tniad.mil.id/index.php/i/26917/kadispenad-insan-penerangan-tni-ad-harus-selalu-update-dan-komunikatif) | A call to improve skills does not establish a newly deployed system or measured publication impact. No internal requirements were inspected. |
| **NoLimit, 9 October 2025 — vendor offering with dashboard illustration** | The vendor explicitly shows/describes SNA in its dashboard: conversation groups, central discussion accounts and propagation between communities. It defines accounts as nodes and interactions as edges. [NoLimit SNA article](https://nolimit.id/blog/social-network-analysis-untuk-melihat-hubungan-interaksi-di-sosial-media/) | Marketing language such as identifying influence does not prove causal influence, complete platform coverage or accuracy. It supplies no inspected calibration/coverage study. |
| **Kazee current Media Intelligence — vendor offering and vendor-named customer claims** | Its product page lists SNA, top influencers and buzzer tracking. Its own page names Polri and Bank Indonesia use cases. Those are vendor claims, not customer-side validation. [Product](https://kazee.id/platform/media-intelligence/id) | It does not prove all customer deployments, actual access to all platform content, ground-truth identification of malicious coordination, or comparative performance. |
| **Kazee technical/promotional article, 9 July 2023 — vendor description** | It explicitly describes social-connection visualisation and degree, closeness and betweenness centrality. Therefore basic centrality methods are not a novel local product proposition. [Kazee SNA article](https://blog.kazee.id/melacak-pengaruh-pengguna-di-sosial-medi-dengan-social-network-analysis) | Its equation of high centrality with influence is an interpretation, not causal validation. Political campaign examples in the article should not become the prototype's targeting workflow. |
| **Drone Emprit, 1 March 2020 — first-party published analysis** | The developer's COVID19 analysis displays direct networks and describes their connections. This is a concrete published application, stronger than merely listing a product feature, although the raw graph and construction quality were not audited. [Drone Emprit analysis](https://pers.droneemprit.id/covid19/) | It is a historical observed corpus, not population opinion or evidence of present API access. Do not infer friendship or credibility from a retweet/connection. |
| **Drone Emprit, 7 June 2020 — first-party published analysis** | The Indonesian New Normal/PSBB analysis describes an SNA map with conversation clusters. [Published analysis](https://pers.droneemprit.id/new-normal-dan-psbb-transisi/) | Its narrative interpretations and graph labels are author conclusions; no independent validation was performed here. Avoid using political labels in the proposed product. |
| **eBdesk current products — adjacent vendor offering** | The Indonesian provider markets cross-border Event Intelligence and a national-security AI framework. This establishes a substantial adjacent intelligence market. [eBdesk products](https://www.ebdesk.com/product.html) | This page does not itself establish a particular social-edge model or verified SNA deployment. Treat as adjacent competitive positioning, not direct proof of all graph features. |
| **Drone Emprit Academic discontinuation notice, 15 October 2024 — direct operational statement** | The provider says its free Academic service stopped in 2023 following the loss of free Twitter data access. This is important counterevidence to assuming a free live social graph can be acquired for the hackathon. [Provider notice](https://pers.droneemprit.id/layanan-drone-emprit-academic-berhenti/) | The notice does not settle today's paid API pricing or every other platform's policy. Do not extrapolate a universal prohibition; validate the chosen source. |

### Inferences

- “The first Indonesian SNA dashboard” and “SNA has not been implemented by TNI” are contradicted by public evidence. A narrower product claim could be “an evidence-linked way to replay observed information flow and show how incomplete data affects the conclusion.” Its commercial novelty remains unverified.
- Distinguish observed interaction from inference. A repost/reply edge records a documented platform action; a shared-URL similarity edge is a derived association; a co-mention of two organisations is a document relation and not proof of their social relationship.
- Basic metrics and a visually attractive graph are necessary building blocks, not sufficient user value. Identify a decision such as checking a cascade, validating a handoff, or deciding whether a network conclusion is stable enough to use.
- Defence can be one approved public-information or humanitarian-coordination workspace. The core should not encode political identity, loyalty, individual threat scores, or persuasion targeting.

### Gaps

- No authenticated product trials, private procurement records, internal TNI architecture, source-level accuracy studies or customer interviews were inspected. Vendor absence claims would be indefensible.
- Public documentation did not establish whether the reviewed tools provide edge-level evidence manifests, explicit observed-versus-inferred edge types, robust missing-edge sensitivity analyses, or complete audit histories for analyst corrections. These are candidate documentation gaps, with **low confidence as market gaps** until vendor demos are obtained.
- Access to a public page does not grant rights to redistribute its underlying social data. No licence review for a specific deployment was performed.

## Which Indonesian problems provide evidence for a useful reusable workflow?

### Takeaway
Indonesia already has research evidence for information-distribution and coordination questions in floods, early warnings and disaster-management collaboration. Those studies establish relevant analytical questions, not an empty market or proof that a proposed dashboard improves outcomes.

### Cited Findings

- A **January 2026 author-published study** analyses the KP2C flood-information account on X using interactions from January–March 2025 and Gephi. It describes distributed community networks and cross-cluster weak ties in crisis information. Its abstract reports coordination and timely-information challenges. This supports a provenance/coverage use case, but is one study rather than a national prevalence estimate. [Communio author article](https://ejurnal.undana.ac.id/index/index.php/JIKOM/article/view/9905)
- A **2019 UGM thesis** examines retweets/likes of BMKG Palu-earthquake posts across three weekly periods in September–October 2018. This is local evidence for temporal information-diffusion analysis. Its historical scraping method must not be recommended as a currently supported API or legal entitlement. [UGM repository](https://etd.repository.ugm.ac.id/penelitian/detail/181285)
- An **ITB 2024 thesis** maps inter-organisational pentahelix collaboration in Cilegon multi-hazard risk management, using degree, closeness and betweenness to discuss hubs and brokers across phases. This supports consented organisational-network analysis as an existing Indonesian research domain. The indexed institutional abstract was available; direct fetch of the entry timed out. [ITB repository](https://digilib.itb.ac.id/gdl/view/80997/25420011)
- A **University of Indonesia account of 2023 research** describes using SNA within a multi-method study of crisis/risk communication following the Sunda Strait tsunami. It recommends cross-agency and community participation in disaster communication. The institutional indexed text was accessible; the direct fetch timed out. [UI research account](https://fisip.ui.ac.id/sistem-komunikasi-krisis-dan-risiko-bencana-berbasis-media-sosial-di-indonesia/)

### Inferences

- Reusable jobs include reconstructing observed dissemination, checking whether participating organisations acknowledge information, and examining dependency on a small number of validated collaboration links. They apply to universities, public agencies, customer communities, volunteer groups and inter-company projects.
- A small, authorised graph is preferable to promising population-scale cross-platform access. An opt-in partner network or owner-exported community interactions can expose a real decision and permit ground-truth checks.
- For a hackathon, use a common edge-table schema: `source_node`, `target_node`, `relation_type`, `timestamp`, `evidence_id_or_url`, `observation_method`, and an observed/inferred marker. Preserve separate node and data-coverage manifests. Add confidence only where its meaning can be explained; a numerical score alone does not establish reliability.
- Do not import social-platform communities as geographic, political, religious or ethnic groups. Algorithmic clusters are simply groups under a chosen observed graph and algorithm.

### Gaps

- These studies do not supply a guaranteed, redistribution-cleared live dataset. Per-record social text and interaction rights must be checked independently.
- No representative statistic was verified for how many Indonesian organisations suffer network bottlenecks, how often coordination is deceptive, or how much time a graph dashboard saves. Those remain product-validation questions.
- No demographic representativeness or real information exposure can be inferred from public interaction data alone. Silence may mean a missing observation, a private channel, offline communication, or no recorded action.

## Which five distinct reusable products are worth evaluating?

### Takeaway
Recommend **CascadeLens** as the clearest SNA hackathon story **if direct, timestamped interaction edges can be obtained**. It replays observed information flow with inspectable evidence and explicit unknowns. **RelayResilience** is the practical alternative when an opt-in organisational partner can provide a complete small network. Treat the five below as alternative products; do not attempt to build them all.

### Cited Findings

The following are design inferences grounded in the existing commercial capabilities and Indonesian studies cited above. They are not claims of implemented systems, algorithmic invention, verified willingness to pay, or Indonesian firstness. Baselines already include [NoLimit's propagation/community visualisation](https://nolimit.id/blog/social-network-analysis-untuk-melihat-hubungan-interaksi-di-sosial-media/), [Kazee's centrality and network features](https://blog.kazee.id/melacak-pengaruh-pengguna-di-sosial-medi-dengan-social-network-analysis), and [Cilegon organisational SNA research](https://digilib.itb.ac.id/gdl/view/80997/25420011).

### Inferences

#### 1. CascadeLens — audit observed information flow

**Job:** “How did this message move through the interactions we can actually observe?” Search finds posts; a temporal graph connects documented actions and lets an analyst inspect paths, branching and cross-community transfers.

**Graph:** actor/account/organisation nodes; directed, timestamped repost, reply or forwarding edges. Every edge retains the underlying event and relation type. A reply is not endorsement. Root-only repost records do not reveal all intermediate exposure paths; do not fabricate a diffusion tree. Display earliest observed occurrence in this dataset rather than “true origin.”

**Reusable customers:** product-incident communication, owned customer communities, campus information, event organisers and researchers. Optional defence application: retrospective public emergency-information distribution or a public exercise announcement, without scoring individuals.

**Lean MVP:** one event, one authorised community export or appropriately licensed historical interaction corpus; validate identifiers and timestamps; build directed snapshots, weak components and observed shortest paths; optionally detect communities on a clearly labelled projection. The primary interface is a time slider plus an evidence drawer and exclusions/coverage panel. A second dataset uses the same pipeline and schema. Avoid automatic cross-platform identity fusion.

**Measure:** sampled edge precision, relation-type correctness, temporal consistency, correct retrieval of documented paths and analyst review time against a chronological list. Delete a controlled share of edges and show which conclusions change. True influence or exposure is not an acceptance metric because the data does not establish it.

**Domestic overlap/gap:** propagation maps already exist. The differentiating hypothesis is evidence-linked temporal replay, explicit missing links and correction history. **Market-gap confidence: low.** Biggest assumption: usable direct relation records exist; text similarity alone cannot replace them.

#### 2. PatternAudit — review repeated sharing patterns without attributing intent

**Job:** “Which repeated co-actions deserve inspection, and are they unusual relative to normal activity?” This can help audit duplicate syndication, disclosure compliance or data quality; it must not automatically label people bots, deceivers or hostile actors.

**Graph:** a bipartite network of pseudonymous actors and artefacts (canonical URL, identical public item or approved content identifier), with timestamped action edges. An actor–actor projection measures shared artefacts or co-action windows; those similarity edges remain explicitly inferred, not communication or organisational ties.

**Reuse:** publishers checking syndicated content, community moderators reviewing repetitive submissions, organisations auditing their own scheduled distribution. Optional defence application: an analyst-reviewed aggregate public-information integrity study. Routine official alerts and news syndication are essential benign controls.

**Lean MVP:** one channel, one artefact type and a known time window; canonicalise URLs conservatively, compare overlap and temporal repetition while accounting for high-activity accounts, and expose supporting events. Use activity-preserving time shuffles as a proposed comparison baseline, then require human disposition. No identity attribution or automated sanctions.

**Measure:** precision on analyst-confirmed repeated patterns, false alerts on benign scheduled activity, stability under time-window changes and review effort. Malicious-intent precision cannot be reported without an independently established intent-labelled dataset.

**Domestic overlap/gap:** Kazee already markets buzzer tracking and SNA, so basic “coordination detection” is not a credible local novelty. The bounded hypothesis is transparent null comparisons and evidence/review records. **Gap confidence: low.** Biggest risks are treating common interest as coordination and treating coordination as wrongdoing.

#### 3. CoverageMap — verify coverage inside a participating information network

**Job:** “Which participating organisations or channels have no confirmed information receipt?” The product checks a defined network, rather than claiming to measure who in the general population saw a post.

**Graph:** registered organisation/team/community-channel nodes; typed directed edges for observed forwarding and independently recorded receipt/acknowledgement. Keep “sent,” “forwarded” and “acknowledged” distinct. A complete participant roster is necessary to show genuine isolates; missing data is labelled unknown.

**Reuse:** event coordination, distributed campus notices, franchise operations, volunteer consortia and service outage updates. Optional defence application: approved civil–military disaster-information handoffs. No targeting based on inferred demographic or political communities.

**Lean MVP:** a consented 15–30-organisation exercise or synthetic exercise clearly labelled as such; two message rounds, timestamped acknowledgements and an administrative coverage dashboard. Connected components and validated reachability answer whether a documented route exists; the graph does not prove message comprehension or future delivery.

**Measure:** agreement with manually audited acknowledgements, false “unreached” flags, correct identification of unknown states and time to locate a broken handoff. Test withheld acknowledgements separately from genuine missing delivery.

**Domestic overlap/gap:** disaster communication networks are already researched locally, and standard messaging tools offer read receipts. The proposed value is cross-organisation, typed evidence with incomplete-observation reporting. **Gap confidence: low-to-medium for the narrow workflow, not absence.** Biggest assumption: participants accept the recording burden and distinguish acknowledgement from receipt/comprehension.

#### 4. RelayResilience — test organisational collaboration dependency

**Job:** “Does collaboration rely on a single validated liaison or team, and is there an agreed backup?” SNA matters because a set of good individual response times does not reveal a disconnected handoff structure.

**Graph:** teams/organisations as nodes; consented, validated working relationships or task-handoff edges, with direction, time and task class. Start with an opt-in survey plus confirmed handoff logs. Do not silently infer relationships from message volume or evaluate employee productivity.

**Reuse:** project consortia, research collaborations, customer escalation teams, volunteer networks and incident response. Optional defence application: non-sensitive inter-agency humanitarian coordination exercises. The ITB Cilegon thesis provides direct Indonesian research precedent, so the method is not new locally.

**Lean MVP:** one roster, one task and a confirmed edge list. Compute components, articulation points for an appropriate undirected projection, and validated directed reachability; let a reviewer simulate unavailable teams and document an approved backup. A counterfactual edge removal is a scenario, not proof an organisation will fail.

**Measure:** correctness on hand-checked graphs, agreement between detected dependencies and liaison validation, sensitivity to uncertain ties, and exercise time to recover a handoff. A simple table of dependencies is the non-graph baseline.

**Domestic overlap/gap:** organisational SNA research already exists; a repeated assessment workflow with evidence, permissions and accepted backup plans is a testable packaging opportunity. **Gap confidence: low-to-medium.** Biggest risks are private relationship exposure and confusing structural dependency with an individual's value or blame.

#### 5. GraphCheck — audit whether an SNA finding survives data uncertainty

**Job:** “Would this centrality ranking, community split or observed path change if collection were incomplete?” This is specialist quality tooling for SNA users, not another social-listening dashboard.

**Graph:** the same observed actor-interaction graph plus a coverage/provenance manifest; user-selected uncertain or inferred edges are typed separately. Compare alternative deduplication, identity-matching and time-window choices. Do not combine follower, reply, co-share and co-mention ties into one unexplained score.

**Reuse:** analysts, researchers, social-listening vendors and public agencies. Optional defence application: validating an unclassified assessment before using it in a briefing. It can audit other graphs but the initial product should remain specifically about social-interaction data.

**Lean MVP:** one static interaction corpus and synthetic graphs with known properties; report degree/ranking agreement, community stability and path changes under documented perturbations. Show source coverage and explicitly unsupported inferences. Choose a few meaningful perturbations, not a large algorithm laboratory.

**Measure:** whether known missingness/entity-merge failures are surfaced, metric correctness against hand-calculated graphs and whether users make fewer incorrect conclusions. Repeated edge deletion is a sensitivity test, not a calibrated estimate of real-world missingness unless a sampling design supports it.

**Domestic overlap/gap:** Gephi, standard graph libraries and researcher scripts already expose metrics. The narrow opportunity is a reproducible evidence-and-sensitivity review pack. Public competitor documentation did not establish equivalent workflow, but **market-gap confidence remains low**. Biggest assumption: buyers value methodological reliability enough to adopt a dedicated tool.

**Recommendation across the five.** CascadeLens has the most straightforward category fit and visible analyst story. Build one observed-edge replay with complete provenance and two small reusable datasets; do not add automatic bot, truth or threat labels. Select RelayResilience instead if the only reliable data source is a consenting organisational partner. GraphCheck is an attractive differentiator inside the acceptance test, not a second full product to build simultaneously.

### Gaps

- No proposed MVP has been coded or evaluated. Sample sizes and scopes above are planning suggestions, not measured power or performance claims.
- No foreign precedent should be inferred from the optional defence examples here; another researcher covers verified foreign cases and their maturity.
- No universally free social-platform graph API is assumed. The loss of free Drone Emprit Academic access reinforces that data access can determine feasibility. Retain a manual/authorised edge-CSV demo path and label synthetic records explicitly.
- The user wants later reuse, but competition IP, third-party dataset restrictions and customer permissions still need verification before any commercial reuse claim.

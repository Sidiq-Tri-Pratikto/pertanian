# Social network analysis competition guidance and winning precedents

Research cutoff: 26 October 2026, Asia/Jakarta. This review distinguishes social-interaction analysis, social-graph products, organisational relationship graphs, and adjacent knowledge graphs. Awards establish recognition; they do not establish independent accuracy or explain why a project won.

## What does the official Kartika guidance say about SNA?

### Takeaway
Social Network Analysis is explicitly an example under **Siber Sosial**, rather than a separate formal category. A reusable product can have one credible defence-related demonstration, although the published relevance criterion specifically refers to TNI AD IT/OT security needs.

### Cited Findings
- The Siber Sosial description covers monitoring/analysis of the social cyber domain, including disinformation, propaganda, buzzer activity and public opinion. Its examples explicitly include **Social Network Analysis**, Buzzer/Bot Detection, Hoax Classifier, Sentiment Analysis Dashboard and Early Warning Isu Viral. — [Official homepage, category section](https://kartikacyberhackathon.id/)
- Rubric: relevance/benefit 25%, technical innovation 25%, prototype functionality 25%, implementation feasibility 15%, documentation 10%. Relevance is worded as alignment with TNI AD IT/OT security needs. — [Official homepage, assessment section](https://kartikacyberhackathon.id/)
- Submission deadline is **15 November 2026**. Two lists request proposal, technical documentation and demo video; and accessible project link, presentation video and slides. Maximum three members, with individual registration expressly permitted. — [Official homepage](https://kartikacyberhackathon.id/)
- The format paragraph says final 20 November; timeline, event section and FAQ say **24 November**. The discrepancy remains unresolved. — [Official homepage](https://kartikacyberhackathon.id/)

### Inferences
- Describe the graph's real analytical job and an actionable, verifiable output. A force-directed visualisation alone does not show that an analyst's task is improved.
- Keep a generic data model and demonstrate a public-information, organisational-coordination or resilience use case. This is a proposed positioning based on the rubric, not an organiser endorsement or exemption from relevance requirements.
- Prepare the union of both submission lists until the authenticated participant guidance clarifies the exact files required.

### Gaps
- Dataset mandates, social-platform access, graph algorithms, originality, previous work, AI use, code publication and IP/reuse terms were not established from the public homepage. No authenticated participant dashboard or full guidebook was reviewed in this task.
- The webpage does not establish access to internal TNI data, system integration, adoption or procurement commitments.
- Keep cumulative paraphrase of the official homepage in the final report near its 200-word source limit. Do not repeat all administrative details from earlier reports.

## Which genuinely related hackathon winners can be verified?

### Takeaway
Five useful award precedents have primary evidence, but they are **not five pure social-interaction SNA dashboards**. Two directly construct/analyse social networks; one constructs a research/social graph; two are adjacent claim or organisational knowledge-graph products. Their distinction should remain visible in the final report.

### Cited Findings

1. **The Ultra Super Social Passport — HackwithBay 3.0, third place, July 2026 organiser report. Direct social-network product.** Neo4j's event report explicitly labels it third place and describes community detection and variable-length graph traversal between party participants. People are connected through voluntarily supplied interests/experiences; the blog describes a 193-guest demo and six groups. The linked project repository explains paths and provenance receipts behind recommendations; its later version uses 312 records, so counts are version-specific. — [Primary sponsor/organiser report](https://neo4j.com/blog/developer/graph-used-right-built-fast-neo4j-at-hackwithbay-3-0/); [project code and technical documentation](https://github.com/Jshengdev/ultra-super-party-passport)
   - **Nodes/edges:** Person, Interest, Activity, Party and contextual entities; person-to-interest, participation and explicitly declared seeking relationships. The repository describes constrained schema, path receipts, community grouping and a lexical TF-IDF fallback when embedding services failed. — [Project repository](https://github.com/Jshengdev/ultra-super-party-passport)
   - **Reusable lesson:** recommendations should explain which declared relationships support a connection. For our proposal use opt-in professional skills/interests and explicit collaboration; do not copy inferred personality/belief features or describe matching as proven actual influence. Algorithmic suggestions are not observed friendship ties.
   - **Evidence limit:** award high-confidence; technical behaviour is creator/sponsor documentation, with no independent test run. Current repository can include post-event changes. Do not report a formal Louvain/Leiden implementation: the reviewed documentation establishes community grouping but not a verified specific algorithm.

2. **ACTIVE Graph — HACKTIVE, September 2013, first place in the ACTIVE Staff division. Direct social/activity-graph application.** The organiser's developer blog clearly separates staff winners and labels ACTIVE Graph first place. It maps users, friends, interests and activities in Neo4j; demos recommended event meetups and activities through those relationships. This is not an undifferentiated overall first-place claim. — [Primary organiser announcement](https://developer.active.com/blog/read/ACTIVE_Networks_HACKTIVE_Hackathon_Winners)
   - **Nodes/edges:** users, friends, declared interests and activities; friendship, interest and participation relations. — [Organiser announcement and technical description](https://developer.active.com/blog/read/ACTIVE_Networks_HACKTIVE_Hackathon_Winners)
   - **Reusable lesson:** one activity/collaboration graph can support several applications. A real user decision is more important than a generic network map.
   - **Evidence limit:** old precedent; no current deployment or source repository verified, and no quantitative centrality/community algorithm or benchmark disclosed. Social-graph construction and recommendation are demonstrated; advanced analytical SNA is not established.

3. **Biotry — Solana Graveyard Hackathon, Tapestry social track, first place, March 2026. Social/research graph construction, adjacent to analytical SNA.** The track sponsor explicitly says it offered the social track and names Biotry first. Researchers become profiles, papers become content nodes, peer review becomes edges, with citation/funding/reputation relationships described. This is a **track victory**, not evidence of overall Solana first place. — [Primary track-sponsor results](https://blog.usetapestry.dev/p/solana-graveyard-hackathon)
   - **Nodes/edges:** researchers, publications, reviews and funding/reputation relationships. The winner is graph-based scholarly collaboration infrastructure; the inspected announcement does not establish centrality analysis, diffusion modelling or verified collaboration outcomes. — [Sponsor's project description](https://blog.usetapestry.dev/p/solana-graveyard-hackathon)
   - **Reusable lesson:** a collaboration/evidence graph can cross research, grant and professional communities. Blockchain is not required to copy the useful graph relationships.
   - **Evidence limit:** the linked live app failed to fetch. Project description is from the sponsor; implementation and data correctness were not tested. Do not transfer the sponsor's stated DAO turnout statistics or reputation effects as validated facts.

4. **ConspiracyGraph Agent — Neo4j Aura Agent Hackathon 2026, first place, announced 23 June. Adjacent claim/narrative knowledge graph, not observed social-propagation SNA.** The official organiser announcement names it first and explains its claim–narrative–entity–source–evidence model. Creator documentation uses Google Data Commons Fact Check / ClaimReview records and vector similarity plus Cypher templates. — [Primary winners announcement](https://community.neo4j.com/t/aura-agent-hackathon-winners-announced/79568); [creator technical submission](https://community.neo4j.com/t/start-here-register-get-aura-credits-aura-agent-hackathon/77191/35)
   - **Nodes/edges:** ClaimVariant, Claim, FactCheck, Publisher, Topic, NarrativeFrame and Entity; expresses, checks, published-by, uses-frame and mentions. The creator reports 1,282 nodes and 2,436 relationships. These edges explain semantic/evidence context; **they do not prove who transmitted a message to whom**. — [Technical submission](https://community.neo4j.com/t/start-here-register-get-aura-credits-aura-agent-hackathon/77191/35)
   - **Reusable lesson:** every derived relationship needs provenance and a clear meaning. Combine content evidence with actual timestamped reply/repost links only if a real propagation application has permitted interaction data.
   - **Evidence limit:** model enrichment can be inferred rather than observed. No independent benchmark or graph correctness test performed. Avoid importing sensitive person-level belief inference or treating every semantically linked claim as coordinated activity.

5. **Korca Triage Agent — Neo4j Aura Agent Hackathon 2026, third place, announced 23 June. Adjacent organisational/expertise graph.** The organiser names it third. Creator documentation and its linked repository show a graph of people, tickets, clients and skills used to recommend who should handle a support request. — [Primary winners announcement](https://community.neo4j.com/t/aura-agent-hackathon-winners-announced/79568); [creator technical submission](https://community.neo4j.com/t/start-here-register-get-aura-credits-aura-agent-hackathon/77191/23); [code](https://github.com/alterminder/korca-aura-agent)
   - **Nodes/edges:** User/Expert, Ticket, Client and Skill; resolved, human-confirmed-for, ticket-from-client, works-for hierarchy and has-skill. Uses similar-ticket retrieval followed by graph traversal/counts and client history. — [Creator documentation](https://community.neo4j.com/t/start-here-register-get-aura-credits-aura-agent-hackathon/77191/23)
   - **Reusable lesson:** observed collaboration, resolution and expertise relationships can make routing explainable across industries. The same core could support approved emergency-support requests or voluntary expert coordination.
   - **Evidence limit:** the creator claims real production data and 72% versus 93.4% top-1 routing on 485 confirmed tickets. Evaluation split/leakage/independent reproduction were not established; these are **self-reported project figures**, not our benchmark and not proof of causal business impact. The source's claim that equivalent SQL joins cannot be written should not be repeated; database choice is an implementation tradeoff.

### Inferences
- The most transferable winning pattern is **a graph that supports one concrete decision and explains the path**, rather than a large node-link diagram or arbitrary graph database requirement.
- For a strict SNA entry, make the primary graph an explicitly defined **social interaction or organisational collaboration graph**. A document co-mention or semantic-similarity graph is a different network and must be labelled accordingly.
- The winning examples support generic reuse, but their awards do not prove that any exact product is absent in Indonesia or likely to win Kartika.
- Borrow opt-in community matching from the direct social examples, evidence receipts from ConspiracyGraph, and a measurable routing decision from Korca. Do not combine all five into a single hackathon build.

### Gaps
- No four-to-seven pure observed social-interaction SNA hackathon winners were established in the bounded search. The five examples above deliberately expose adjacency instead of inflating the count.
- An Indonesian creator's site claims **Transactional Network Analysis** won first at Cloudera AI Hackathon 2025, and links code. The public event page confirms the competition but does not name that winner; therefore it is **not counted as organiser-verified** here. It is a transactional network, adjacent to SNA. — [Creator claim](https://adrian-maulana.com/projects/transactional-network-analysis/); [public organiser event page](https://www.clouderaaihackathon.com/)
- CriNet won an undergraduate research-conference presentation award, not a hackathon; Smart India Hackathon 2026 criminal-network submissions found lacked a verified award. Exclude both from a hackathon-winner list. — [UAEU conference-award report](https://www.uaeu.ac.ae/en/news/it/2014_news/nazar.shtml); [example submitted prototype without award proof](https://www.mlh.com/events/hacktoberfest-2026-aki-hacks-kolkata/submissions/01a139d9-81d8-b2d3-af95-0b2888119f79)
- Page limits: the shared Neo4j winners announcement covers two projects; keep cumulative derived prose near 200 words for that page, and use the separate creator submissions for technical explanations. The HackwithBay blog also documents unrelated winners VeriGraph/Constructor, but those were not needed for the shortlist and should not be promoted as SNA examples.

## What technical and product conclusions should the report retain?

### Takeaway
A reusable SNA product should have a transparent node/edge contract, temporal and sampling boundaries, provenance, and a measured task. Attractive visualisation is useful only when users can explain why an edge exists and how a result changes when observations are missing.

### Cited Findings
- Direct winners use observable or declared relationships to support recommendations: ACTIVE Graph's activity relationships and Social Passport's path receipts are documented in their primary descriptions. — [ACTIVE Graph](https://developer.active.com/blog/read/ACTIVE_Networks_HACKTIVE_Hackathon_Winners); [Social Passport code](https://github.com/Jshengdev/ultra-super-party-passport)
- Adjacent winners explicitly expose different kinds of evidence: ClaimReview/source relations for ConspiracyGraph and human-confirmed resolution relations for Korca. These relationships have different semantics and should not be collapsed into a single vague “connected” edge. — [ConspiracyGraph](https://community.neo4j.com/t/start-here-register-get-aura-credits-aura-agent-hackathon/77191/35); [Korca](https://community.neo4j.com/t/start-here-register-get-aura-credits-aura-agent-hackathon/77191/23)

### Inferences
- Minimal shared schema: stable node ID/type; edge source/target/type; timestamp or valid-time; source record and observation/derivation status. Preserve event evidence separately from any aggregated edge weight.
- Before calculating centrality/community metrics, specify whether graph is directed, weighted, temporal and bipartite; the meaning of the edge controls interpretation. A shared link or similar text is not proof of interaction, coordination, bot activity, friendship or intent.
- A credible MVP can replay consented collaboration data or permitted public reply/repost records, show source evidence for every edge, and compare one analyst decision with a spreadsheet baseline. A simulated perturbation is a stress test, not proof that removing a person changes real-world behaviour.
- Avoid political targeting, individual loyalty/threat scores and speculative account identity linkage. Generic collaboration, information provenance and public-resilience applications can demonstrate value without them.

### Gaps
- No winner software, current APIs, licensing, performance or datasets were executed/audited. No participants or organisers were contacted.
- Primary source evidence here supports award status and documented designs, not present-day deployment, privacy compliance, or production readiness.

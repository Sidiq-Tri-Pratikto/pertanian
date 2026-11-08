# Foreign defence precedents for reusable sentiment and narrative analysis

Research cutoff: 26 October 2026, Asia/Jakarta. All deployment conclusions below are limited to public evidence. Sentiment means evaluative polarity toward an object/aspect; stance means support/opposition toward a proposition; emotion means expressed affect; narrative analysis groups recurring interpretations. None establishes factual truth, hostile intent, population-wide opinion, or an individual's actual mental state.

## Which foreign defence examples have strong public primary evidence?

### Takeaway
Public defence work supports a generic product direction: combine topic/aspect sentiment, change over time, evidence-linked analyst review, and briefings. The evidence mixes actual exercise use, funded R&D, research platforms and benchmarks; these must not be presented as equivalent operational deployments.

### Cited Findings

- **United Kingdom / NATO: Dstl at Exercise Trident Juncture — actual use in a training exercise, reported 17 January 2019.** Dstl spent five weeks working with NATO's Public Diplomacy Division, Joint Warfare Centre and Allied Command Transformation. Its analysis included hashtags, sentiment, external media, and NATO's own communications; it informed changes to exercise communications. This is direct evidence that sentiment analysis was used for a defence public-engagement assessment. It is not evidence of a permanently deployed autonomous dashboard or independent causal evaluation. **Confidence: high** on exercise use, unknown on current deployment/software. [UK Ministry of Defence / Dstl](https://www.gov.uk/government/news/dstl-tests-natos-war-of-words)

- **United States: DARPA INCAS — selected research teams announced 2 September 2021.** The program sought tools to connect multilingual messaging and campaign indicators across time/platforms and quantify confidence, addressing the limitations of manual commercial social-listening workflows. It funded separate detection, analytic interface, testbed and evaluation activities. DARPA used future-oriented language about development; the announcement does not establish delivered or operational performance. Some program research concerns psychographic population segmentation, which is unnecessary for the proposed reusable product. **Confidence: high** that funded research existed; not proof of operational adoption. [DARPA primary announcement](https://www.darpa.mil/news/2021/incas-program)

- **Canada: DND/CAF IDEaS hostile-information challenge — funded development, official results page dated 6 October 2025.** The results list Mercur IT Solutions' **The Dark Crawler**, explicitly combining textual analysis, sentiment analysis and machine learning, with CAD 1,005,295.50. Other funded projects include semi-automated monitoring and visualization. This is a public development award, not a hackathon win and not evidence that a system was deployed successfully across the Canadian Armed Forces. The wider challenge includes goals beyond ordinary sentiment analysis; do not transfer all of them into a prototype. **Confidence: high** on award/name; performance and operational status unknown. [Department of National Defence results](https://www.canada.ca/en/department-national-defence/programs/defence-ideas/element/competitive-projects/challenges/detecting-responding-hostile-information-activities.html)

- **Australia: Adelaide University / Defence Science and Technology Group INSIGHT — research platform publicly described 16 September 2026.** Australian Defence says the partners developed an on-premises platform ingesting news, social feeds, reports and sensor outputs. It brings sources together, visualizes connections and creates briefings that update as data changes. It is a strong precedent for a reusable evidence-to-briefing workflow. **Important:** this article does not explicitly document a sentiment classifier or provide proof of operational deployment, accuracy, or impact. Treat INSIGHT as adjacent information-analysis and visualization, not a deployed sentiment product. **Confidence: high** on the stated developed platform; maturity beyond that remains unspecified. [Australian Department of Defence](https://www.defence.gov.au/news-events/news/2026-09-16/platform-deals-blow-disinformation)

- **NATO Strategic Communications Centre of Excellence, Riga: low-resource-language stance/sentiment evaluation — published research, 9 April 2026.** This report evaluates English, Lithuanian and Russian on politically sensitive topics and tests adaptation methods including fine-tuning and retrieval-augmented generation. Its summary reports persistent language performance gaps and that adapted smaller models can outperform larger models. This is benchmark evidence that language-specific evaluation matters, not proof of any NATO-wide deployed product. **Confidence: high** on the published study; do not infer Indonesian-language performance from Baltic/Russian results. [NATO StratCom COE report page](https://stratcomcoe.org/publications/understanding-llm-performance-gaps-strategic-implications-of-stance-detection-and-sentiment-analysis-in-small-languages/341)

- **Additional United States precedent: DARPA SocialSim — completed research program, not operational sentiment deployment.** The official page explicitly identifies disaster-relief information delivery and analysis of strategic disinformation as possible applications of better simulation of information spread/evolution. The page marks the program complete and unmaintained. It is an unusually clear primary example of the same general computational capability being relevant to both defence and humanitarian response. Simulation is adjacent to sentiment analysis; accurate simulation is a research goal rather than evidence of reliable forecasting. **Confidence: high** on program goals/completion; no operational delivery claim. [DARPA program summary](https://www.darpa.mil/research/programs/computational-simulation-of-online-social-behavior)

### Inferences

- The strongest positioning is **general-purpose evidence-linked sentiment and issue intelligence**, demonstrated on a public-service disruption; defence is an additional deployment context. The precedents support the relevance of that direction but do not prove market demand or novelty in Indonesia.
- UK exercise evidence validates the relevance of analysing public communication; INSIGHT suggests that automatically maintained briefings may offer more workflow value than another polarity chart. These are product-design inferences, not verified claims about what judges prefer.
- A multilingual quality-assurance layer may be a more credible differentiator than a claim to detect hostile actors: NATO COE's study provides a defensible reason to measure errors separately by language and domain.

### Gaps

- These sources cannot prove that a similar capability is absent from Indonesia or from non-public defence systems. Use “no equivalent public implementation verified” only after a separate Indonesian search; never “Indonesia has none.”
- The candidate Singapore DSTA example was not verified from a DSTA primary source. Exclude it as a defence deployment. GovTech public-service stance analysis exists, but it belongs in a civilian precedent section.
- India NETRA is frequently conflated with other systems carrying the same name. The official DRDO product result found concerns airborne early warning; a DRDO-hosted press compilation repeats an external article about Internet interception. Neither is sufficient primary evidence for a reusable sentiment dashboard. Exclude it.

## Which capabilities can a generic product reuse without military-specific design?

### Takeaway
Reuse one analysis pipeline and vary the workspace's aspects, source documents, language labels and response categories. A product need not collect private data, identify people, or optimize persuasion to show national-resilience relevance.

### Cited Findings

- The UK Government Communication Service's RESIST toolkit says commercial monitoring tools are used by government, while emphasizing that no tool fits every case, sentiment cannot be wholly relied upon, and data availability/limitations must be understood. [UK GCS RESIST toolkit](https://www.communications.gov.uk/publications/resist-counter-disinformation-toolkit/)
- Singapore GovTech's 6 June 2025 author-written description reports an implemented conversation-analysis tool combining narrative summaries, stance aggregation, reviewer editing, preprocessing and anonymization. This is a **civilian public-service example**, useful as a reusable architecture precedent; it is not a defence adoption claim. [GovTech AI Practice via AI Singapore](https://blog.ai.gov.sg/fine-tuning-language-models-for-long-context-data-automated-stance-analysis-of-citizen-discussions/)

### Inferences

Recommended minimal shared core, offered as design proposals:

1. Import CSV/JSON, authorized public comments or survey text with source, timestamp, language and consent/access metadata. A reproducible dataset upload is sufficient for a hackathon demonstration; live social-platform collection is optional.
2. Preserve original text; deduplicate and redact personal identifiers. Use source-category filters to distinguish institutional posts and reposts from independent feedback.
3. Extract **aspect + sentiment + evidence span**. Add topic clustering; add stance only when the workspace defines an explicit question/proposition. Keep expressed emotions optional and separately labeled.
4. Show changes relative to a historical baseline with sample size, unique-document count and source coverage. Flag for review; do not automatically label change as coordinated attack or public consensus.
5. Produce a compact briefing with claims tied to source excerpts. Let analysts correct labels and record decisions; suggestions should remain drafts.

The same core can serve product reviews, transport/service complaints, utility outage communication, disaster-information triage, and aggregate defence public-information support. Avoid designing separate hard-coded apps for each of these domains.

### Gaps

- The cited platforms do not establish an Indonesian model's accuracy, availability of platform APIs, or rights to reuse their datasets/software. Availability, licensing and model evaluation require separate checks.
- None of the evidence justifies promising factual verification from sentiment, a general threat detector, or population-level representativeness.

## What should be evaluated and what claims should the proposal avoid?

### Takeaway
Evaluate decisions the dashboard supports, alongside model quality. Present a public-service case and a small secondary defence example using the same implementation, then state the adaptation needed for a real deployment.

### Cited Findings

- A historical Australian Defence review explicitly warns that the organization's own promotional posts and their reposts can inflate measured positive sentiment, so this contribution should be discounted when interpreting public sentiment. [Australian Defence, Review of Social Media and Defence, Annex 2](https://www.defence.gov.au/sites/default/files/2021-06/Review-of-Social-Media-and-Defence-Full-report.pdf)

### Inferences

- Evaluate aspect extraction and macro-F1 for sentiment; evaluate stance separately. Report per-language and per-source results, an unknown/abstain option, confidence calibration, and errors on sarcasm, negation, mixed language and multiple aspects.
- Split train/test by time and duplicate group, not randomly across near-identical posts. Include a manually labeled small holdout and document label disagreements. Baseline against a simple classifier before selecting a larger model.
- Measure cluster purity and topic stability, source-link accuracy in briefings, false alerts, analyst time saved, and human corrections. Sentiment change alone does not demonstrate service improvement or national-security benefit.
- For a hackathon demonstration, show one model correcting an aggregate sentiment error: “The volunteers were helpful, but the water delivery is still late” should remain positive about staff and negative about delivery. Reuse that feature for business service aspects and public communication aspects.
- Prefer on-premises capability as an optional later deployment requirement if justified by a partner, not mandatory infrastructure for the first prototype. Australia's article establishes an on-premises precedent, not a universal need.
- Do not promise hostile attribution, deception detection, psychological profiling or persuasion optimization. Those exceed the sentiment category and require materially different evidence and governance.

### Gaps

- No model, API, dashboard, code repository or operational system was tested in this research. No interviews or procurement contacts were conducted.
- RTK.md was absent from the project root and the scoped filesystem search; no RTK-specific instructions could be read.

# Five reusable sentiment products with optional national-resilience applications

Research date: 26 October 2026, Asia/Jakarta. The five directions below are alternative product jobs, not five applications or a proposed five-module platform. Product names, architectures, MVPs and commercial positioning are researcher proposals. Public evidence of a foreign research programme does not establish operational deployment or absence of an equivalent Indonesian system.

## What do foreign defence examples actually establish?

### Takeaway
Foreign defence evidence supports analyst sensemaking, source comparison, uncertainty and language/domain validation. It does not justify converting a negative comment into a threat label. The strongest reusable opportunity is an auditable analysis workflow, with defence as one application rather than the identity of the product.

### Cited Findings
- **US DARPA INCAS:** its stated objective was detecting, characterising and tracking influence campaigns with quantified confidence. The official page criticises manual, static keyword-based analysis and weak confidence assessment. It currently marks the programme complete and the page unmaintained. This establishes a completed research programme and its aims, not independently measured operational performance. — [DARPA](https://www.darpa.mil/research/programs/influence-campaign-awareness-and-sensemaking)
- **Australia/US RAPID:** University of Melbourne's 30 January 2023 research-partner case study says its DSTG collaboration developed real-time topic/network analysis, including time-sequenced event comparisons; trials included DSTG and US Army Research Laboratory researchers. It reports crowd-mood observations during a 2018 test. This is broader social analytics and a partner-reported trial, not proof that a pure sentiment classifier is operationally reliable. — [University of Melbourne/DSTG case study](https://research.unimelb.edu.au/partnerships/case-studies/ai-platform-targets-crowd-sourced-data-for-military-intelligence)
- **Canada DND IDEaS:** its official results list The Dark Crawler, explicitly combining textual analysis, sentiment analysis and machine learning, with CAD 1,005,295.50 funding. These are funded competitive R&D projects; the page does not establish deployment or accuracy. — [Canada DND results](https://www.canada.ca/en/department-national-defence/programs/defence-ideas/element/competitive-projects/challenges/detecting-responding-hostile-information-activities.html)
- **NATO domain error:** ACO/ACT Public Affairs Handbook 2020, printed p.152 / PDF p.159, warns that routine military vocabulary such as adversary/tank can be classified negatively and calls for human involvement. Its dated recommendation should not be presented as a current NATO AI architecture. — [NATO handbook](https://www.act.nato.int/wp-content/uploads/2023/06/nato-pao-handbook-2020.pdf)
- **NATO current communication approach:** its public page states that regular media monitoring and analysis improve understanding of the information environment and that communication respects freedom of speech and the press. This supports public communication analysis, not individual loyalty scoring. — [NATO approach](https://www.nato.int/en/what-we-do/wider-activities/natos-approach-to-counter-information-threats)

### Inferences
- Borrow the useful primitives: linked evidence, target-aware analysis, time/version comparison, explicit uncertainty, source coverage and human correction. A hackathon does not need to replicate influence-campaign detection, actor attribution or network surveillance.
- Restrict the optional defence scenario to communications and public-service resilience: evacuation instructions, infrastructure disruption, aid-service feedback or administrative announcements. Analyse corpus-level issues and documents; no individual political, loyalty or extremism scores.

### Gaps
- No classified/internal defence systems were inspected. No source here establishes that an equivalent system has never been implemented in Indonesia.
- Public research announcements and partner claims are different evidence tiers from fielded systems and independently reproduced evaluations.

## Which five reusable product directions are worth considering?

### Takeaway
Sentiment charts, topics and alerts are already commodities. Five narrower jobs are more defensible: verify issue recurrence after a response, compare narratives on the same event, find rating–text mismatches, locate communication gaps, and expose unreliable model decisions. These remain product hypotheses requiring user/data validation.

### Cited Findings
- **Indonesia has real feedback volume:** Ombudsman RI reports 23,596 public reports for 2025 and stresses systemic service improvement. Do not calculate growth against other annual releases without reconciling their different counting definitions. This documents a service-feedback context, not a quantified need for any specific AI product. — [Ombudsman press release, 20 February 2026](https://ombudsman.go.id/news/download/ombudsman-ri-terima-23596-aduan-sepanjang-2025-tegaskan-warisan-pengawasan-berdampak-di-akhir-masa-jabatan-2021-2026)
- **Existing capability:** NoLimit markets social listening, sentiment/data analysis and offers human validation as an add-on. Basic Indonesian monitoring is already a commercial product. — [NoLimit pricing and product FAQ](https://nolimit.id/pricing)
- **Existing aspect analysis:** Qualtrics Text iQ distinguishes overall and topic sentiment, mixed sentiment, and lets users correct classifications. Its example can rate service/food positively and price negatively in one response. Thus aspect sentiment and manual correction alone are not novelty claims. — [Qualtrics documentation](https://www.qualtrics.com/support/survey-platform/data-and-analysis-module/text-iq/sentiment-analysis/)
- **Existing feedback workflow:** Medallia describes review aggregation, topics, low-score alerts, sentiment and response/closure workflows. Merely adding an assigned/closed status is insufficient differentiation. — [Medallia product brochure](https://www.medallia.com/wp-content/uploads/pdf/resources/Medallia-Brochure-Social.pdf)
- **Winning inspiration, mismatch:** Bupa Australia won silver in Databricks Smart Business Insights Challenge 2025 for a real-time anomaly engine flagging emotional mismatches in customer feedback. The organiser verifies the award and high-level function; it does not publish the precise scoring algorithm or its accuracy. — [Databricks organiser page](https://hackathon.stackup.dev/web/events/databricks-smart-business-insights-challenge)
- **Winning inspiration, cross-source:** Echodex received the expert.ai brand/company/product sentiment category prize in 2021; its project combines news, Reddit and Twitter analysis. Its creators' unbiased claim is not validated. — [Echodex project](https://devpost.com/software/echodex), [organiser gallery](https://expertai-nlapi-042021.devpost.com/project-gallery)
- **Winning inspiration, multilingual:** Multilingual sentiment analyser received third prize in the same 2021 event and combines reviews, translation, phrase analysis and search. This is an inspiration for original-text evidence, not evidence that translation preserves all local sentiment. — [Project](https://devpost.com/software/multilingual-review-analyser), [organiser gallery](https://expertai-nlapi-042021.devpost.com/project-gallery)
- **Winning inspiration, temporal:** E-Insights received Best E-Sports at Wallifornia 2020; its live-feed demo was simulated because integrations were problematic. It supports a clearly labelled replay demo rather than claiming unavailable live data. — [Organiser](https://wallifornia-hackathon-2020.devpost.com/), [project](https://devpost.com/software/e-insights)
- **Indonesian language evidence:** NusaX supplies Indonesian, English and ten Indonesian local languages, created through translation checked by native speakers. It is useful for parallel evaluation, but it does not establish performance on organic slang, mixed-language complaints or emergency vocabulary. Dataset licence is CC-BY-SA; code licence Apache-2.0. — [NusaX authors' repository](https://github.com/IndoNLP/nusax)
- **Local baselines exist:** IndoBERT/IndoNLU and IndoBERTweet provide Indonesian research baselines. Pretraining/model availability is not domain-specific validation or permission to scrape platform data. — [IndoNLU](https://github.com/IndoNLP/indonlu), [IndoBERTweet](https://github.com/indolem/IndoBERTweet)

### Inferences

#### 1. ResponseCheck — Did the same issue recur after we responded?

**Job and Indonesian problem hypothesis:** service teams can mark a ticket resolved while the underlying issue keeps appearing. Existing complaint volume makes this worth investigating, but public figures do not prove how often resolution fails. Users: customer operations, utilities, municipalities, university administrators.

**Narrow reusable core:** an issue ledger linking aspect-level evidence to a timestamped response/resolution record. The unit is an issue or service event, not a person. Avoid rebuilding a ticketing system.

**Technical solution:** import `case_id`, event/service, timestamp, text and response time/status from a partner export; deduplicate; classify a small aspect taxonomy; store the sentence/target causing a negative or unresolved label; group recurrence by confirmed event/service identifiers. Show matched-source counts and rates before/after response, plus reopened/verified statuses. Sentiment is a secondary outcome; repeated explicit failure evidence matters more.

**Slim MVP:** one service outage, four aspects and a replay of a response followed by new complaints. A human can merge/split issue groups and mark an evidence-backed outcome. No automatic customer messaging.

**Optional defence application:** assess whether an evacuation-information or public administrative-service clarification actually addresses recurring reported confusion. Same import and ledger; a different taxonomy.

**Reuse/business:** complement existing helpdesk/CRM exports with independent issue-outcome reporting. Commodity overlap with Medallia and local social-listening workflows is high; the proposed wedge is reproducible recurrence evidence, not assignment/closure buttons.

**Evaluation:** human-labelled issue linkage/recurrence precision; expert agreement on unresolved cases; analyst time per correctly linked case. Split by incident and time, keeping all duplicates and ticket chains together. Observed before/after changes are descriptive, not causal proof that a response improved sentiment.

**Hardest assumption:** a partner provides outcome identifiers and feedback after resolution. Without them this becomes a generic sentiment chart.

#### 2. NarrativeLens — How do sources describe the same event differently?

**Job and Indonesian problem hypothesis:** an aggregate score can mix praise for responders, sadness about a disaster, and criticism of instructions. Analysts need to inspect what a statement is about and which evidence explains a divergence, rather than call all negative text criticism of one institution.

**Narrow reusable core:** one event, one explicit target, one bounded time window, side-by-side evidence from source groups. It compares observed documents, not national opinion or actor intentions.

**Technical solution:** upload a curated CSV/article corpus; deduplicate syndicated text; group by manually confirmed event; extract aspect/target evidence spans; classify sentiment toward that target. Optional stance is a separate task on a declared proposition: support, oppose, insufficient/unrelated. Start with human-labelled stance for the demo if there is no defensible Indonesian training set. Compare proportions only within matched time/source conditions, display sample sizes and omitted/uncertain records. A simple keyword/TF-IDF baseline plus reviewer corrections can work before an encoder or LLM. Link every summary to original snippets and dates.

**Slim MVP:** 150–300 authorised or openly reusable documents across two source groups, one incident, four aspects. Reviewer chooses an aspect and inspects the quotes driving the divergence; a duplicate-news toggle shows why denominator control matters. These are proposed sample sizes, not statistical sufficiency guarantees.

**Optional defence application:** compare official emergency instructions with the questions/interpretations observed in a public response corpus; or compare coverage of a public rescue operation. No automatic attribution to hostile actors.

**Reuse/business:** corporate incident communications, product recall coverage, university announcements and policy explainers. Competes with NoLimit, Kazee, Drone Emprit, Brandwatch and general media intelligence. Wedge: matched comparison, target correctness and an auditable evidence brief. Do not claim competitors cannot do these without a feature audit.

**Evaluation:** target extraction and target-sentiment macro-F1; matched-event retrieval precision; human-rated evidence support for every summary; analyst task time. Hold out entire events and later time periods. Compare against whole-document sentiment to demonstrate the precise failure addressed.

**Hardest assumption:** matching events/targets across documents is reliable enough that reported divergence is not corpus-selection artefact. Keep matching reviewed and transparent in the first version.

#### 3. ScoreGap — Which apparently good scores hide a real problem?

**Job and Indonesian problem hypothesis:** structured ratings and free-text comments can conflict. Teams relying on an average star/NPS score may overlook a concrete complaint. This hypothesis needs Indonesian partner data; the Bupa winner is a foreign precedent, not proof of local prevalence.

**Narrow reusable core:** review-priority inbox for rating–text inconsistency. It does not invent a universal emotional score or accuse respondents of dishonesty.

**Technical solution:** import timestamp, survey question, scale, rating and original comment. Retain question context; classify aspects and sentiment; flag conservative cases such as a high satisfaction rating plus a clearly negative service evidence span. Learn/test thresholds per question/scale, not by directly subtracting stars from a model probability. Display why each record was flagged and allow reviewer confirmation.

**Slim MVP:** one five-point satisfaction survey and 200–500 consented/de-identified feedback rows; compare a conventional rating-sorted queue with a mismatch queue. Synthetic additions may illustrate edge cases, but must be labelled and excluded from performance claims.

**Optional defence application:** feedback about public administrative services or disaster-aid facilities, with complaint details protected. The classifier and reviewer UI remain generic.

**Reuse/business:** hospitality, education, logistics, healthcare administration, public services and SaaS surveys. Commercial overlap with Qualtrics/Medallia is substantial; Indonesian language/context evaluation and lightweight deployment are potential sales angles requiring customer validation.

**Evaluation:** reviewer-confirmed actionable mismatches in top 10/20 results; false-alert rate; review time saved; aspect sentiment macro-F1. Split by customer/case/question and time. Keep the question wording with the record, because context can reverse the meaning of an isolated answer.

**Hardest assumption:** real score-plus-text pairs are available and human reviewers agree a mismatch is useful rather than harmless politeness or a question-context issue.

#### 4. ClarityLoop — What did our announcement leave unanswered?

**Job and Indonesian problem hypothesis:** organisations publish FAQs/updates but repeat questions and misunderstandings can remain. The product identifies information gaps, not the political persuasiveness of messaging.

**Narrow reusable core:** versioned announcement/FAQ plus a queue of observed questions mapped to cited answers or an explicit missing-answer state. Sentiment/emotion helps describe the surrounding feedback; it does not determine factual accuracy or comprehension by itself.

**Technical solution:** user imports dated approved documents and de-identified inquiry text; detect questions and explicit misunderstanding statements; group near-duplicates; retrieve answer passages with keyword/BM25 first; classify answer coverage as a reviewer-confirmed match/partial/not found; attach aspect sentiment and evidence. An optional LLM may draft a clarification solely from retrieved cited passages, with human review. Do not auto-publish.

**Slim MVP:** two versions of one announcement and a replay of 100–200 enquiries. Show a recurring question before/after the revised FAQ, including unanswered examples and ambiguity. A question alone is not proof its author failed to understand.

**Optional defence application:** clarity of evacuation routes, public exercise notices, emergency-service locations or administrative deadlines. Same core later serves product releases, policy changes or campus notices.

**Reuse/business:** communications teams, support centres and customer onboarding. Competes with help-centre analytics, chatbots and media monitoring. Wedge: measured unanswered question clusters linked to document versions and evidence, not another FAQ chatbot.

**Evaluation:** retrieval recall for known answers; reviewer precision for missing/partial-answer flags; false reassurance rate; analyst time to produce an evidence brief. Hold out announcement versions and question threads; do not train/test on paraphrases of the same FAQ. Pre/post inquiry changes are not causal evidence without a controlled study.

**Hardest assumption:** the document library is complete/current and the organisation can connect question volume to actual communication versions. Otherwise missing data looks like a missing answer.

#### 5. SentimentBench — Where should we refuse to trust the classifier?

**Job and Indonesian problem hypothesis:** teams may deploy a generic sentiment model without knowing its errors on slang, local languages, negation, specific domains or mixed sentiment. NusaX and the NATO vocabulary example establish meaningful testing contexts; they do not quantify local deployment failure.

**Narrow reusable core:** sentiment evaluation and review workbench for existing classifiers, not a new general-purpose model or model-observability platform.

**Technical solution:** import model predictions plus a small human-labelled test set; calculate per-class/domain/language results; show evidence-linked disagreements and an uncertain/abstain queue. Compare majority and TF-IDF/logistic baselines with an Indonesian encoder. Choose a confidence threshold on a calibration set and display coverage versus error on a separate holdout. Raw softmax output is not automatically calibrated confidence. Test whether translation changes the label while retaining the original text.

**Slim MVP:** Indonesian plus one local-language slice from NusaX; a separately authored or consented domain challenge set for negation, sarcasm and routine emergency/military words; one reproducible benchmark run and a correction inbox. Keep parallel translations of the same example in one split. No claim that one tiny slice represents the entire language.

**Optional defence application:** identify false negativity in routine rescue/defence vocabulary and route uncertain cases for human review, following the failure mode documented in NATO's handbook. No operational threat classifier.

**Reuse/business:** sentiment API vendors, enterprise NLP teams, localisation teams, public agencies and researchers. Alternatives include open-source evaluation scripts and general ML tooling. A sellable wedge would be curated Indonesian slice tests plus review evidence; this is unvalidated willingness to pay.

**Evaluation:** held-out per-class macro-F1, coverage/error trade-off after calibration, inter-annotator agreement and regression detection on predefined slices. Split by original example across translations, domain and time; do not choose a threshold on the reported test set.

**Hardest assumption:** obtaining reliable native-speaker/domain labels at reasonable cost. This has the strongest technical differentiation but a weaker frontline hackathon story unless paired with a clear analyst decision.

### Gaps
- None of the five is established here as globally novel or first in Indonesia. Basic sentiment, aspects, correction, alerts, topic grouping and workflow exist. A claim about a narrow combination still needs competitor demos and target-user interviews.
- No Indonesian partner supplied feedback/outcome data; sample sizes above describe proposed demos. No model/API, language licence or live integration was tested.
- Winner status shows jury recognition, not why a project won, its production readiness or suitability for this contest's rubric.

## What is the smallest reusable product recommendation?

### Takeaway
Recommend **NarrativeLens** as a small evidence-backed comparison product if the team can curate a legally usable corpus; choose **ScoreGap** instead if a real rating-plus-text partner dataset is already available. Build one coherent workflow and show at most two domain templates. SentimentBench's reliability practices should be a small quality requirement inside the selected product, not a second platform.

### Cited Findings
- INCAS explicitly frames quantified confidence and connecting messages over time as research challenges; RAPID documents cross-scenario event/time analysis. Those precedents support a general analyst tool rather than a TNI-only dashboard. — [DARPA](https://www.darpa.mil/research/programs/influence-campaign-awareness-and-sensemaking), [Melbourne/DSTG](https://research.unimelb.edu.au/partnerships/case-studies/ai-platform-targets-crowd-sourced-data-for-military-intelligence)
- Bupa's silver award provides a stronger direct competition precedent for mismatch review if that data path is accessible. — [Databricks organiser](https://hackathon.stackup.dev/web/events/databricks-smart-business-insights-challenge)

### Inferences
- **One core workflow:** import corpus → declare event and target → inspect aspect-level source comparison → open evidence and uncertain cases → correct → export a brief with denominators and limitations. Store source ID, record ID, timestamp, original text and evidence spans; event/target/aspect labels are versioned outputs. Do not add every ML task by default.
- **Two maximum templates:** (1) a generic product/service disruption; (2) public emergency-information clarity. The same schema, classifier and UI serve both. Templates change the event/aspect vocabulary and sample data, not application code or separate workflows.
- **Scope cutoff:** no live social scraping, cross-platform identity graphs, bot scoring, automatic truth labels, automatic public posting, custom foundation model, microservices, vector database or streaming architecture unless the chosen demo genuinely needs one. CSV plus local relational storage, an established Python model baseline and a simple dashboard are enough to prove the user task.
- **Acceptance evidence:** a human-reviewed held-out incident; an error table showing target-aware analysis versus naive document polarity; each brief statement links to quotes; source/time counts visible; unresolved/uncertain text remains visible; duplicate syndication cannot inflate apparent independent evidence.
- **Honest pitch:** “A reusable tool for comparing how the same issue is understood across sources, with every insight linked to evidence and uncertain cases sent for review. National-resilience communications is one application.” This is a product position, not a measured superiority claim.
- **Vocabulary:** sentiment = evaluative tone toward a target/aspect; emotion = expressed affect; stance = position toward a specified proposition; urgency = operational need; factuality = support from evidence; narrative = recurring framing across documents. Do not use them as interchangeable labels.

### Gaps
- Corpus access and matching quality are the main technical/product risks. Interviews, annotation pilot and basic competitor feature audit should precede a production investment.
- No performance, deployment cost, willingness-to-pay, operational suitability or contest-winning probability has been measured.

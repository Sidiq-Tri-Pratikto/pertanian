# Generic TemuRiset matching and trust

Research date: 31 October 2026 (Asia/Jakarta). Ten primary sources were opened. The Indonesian PRD attachment dated 20 October 2026 was reviewed as the inherited product proposal, not as evidence that any functionality is implemented. The requirements below are design recommendations for an invention discovery and collaboration product; they do not certify investment suitability, legal rights, regulatory readiness, or production security.

## How should matching work across inventions, investors and other support partners?

### Takeaway

Match a versioned invention and a specific support objective against a versioned opportunity or partner intake mandate. Keep eligibility, evidence coverage, submission readiness and ranking separate. A small catalogue can begin with explicit rules and lexical retrieval; semantic retrieval and reranking should earn their place through evaluation.

### Cited Findings

- The original Reciprocal Rank Fusion paper combines document rankings using `sum(1 / (k + rank))`. Its experiments fixed `k = 60` after a pilot investigation. The evidence concerns information-retrieval collections, not funding outcomes. RRF combines positions, so it avoids directly adding unrelated raw lexical and vector scores. It does not establish an optimal constant or guaranteed improvement for TemuRiset. — [Cormack, Clarke and Büttcher, SIGIR 2009](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)
- Sentence Transformers describes a first-stage lexical or bi-encoder retriever followed by a cross-encoder reranker operating on candidate query–document pairs. Cross-encoders compare both texts together and are expensive to apply to very large candidate sets. The documentation's relevance score is not a validated probability of financing, collaboration, or commercial success. — [Sentence Transformers, Retrieve and Re-Rank](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)

### Inferences

The following is a proposed TemuRiset domain contract. Its precise fields and thresholds remain product choices:

1. **Pair identity:** `invention_version + opportunity_version/intake_version + support_type + ask_scope + access_context`. Do not merge a partner's manufacturing offer from one opportunity with its funding terms from another to manufacture a stronger match. An investor's thesis describes preferences; active intake additionally records whether approaches are accepted, by whom and until when.
2. **Support objectives:** distinguish project finance, co-development, validation, licensing, production, distribution, and company investment. Display the subset that the selected opportunity actually supports. An individual inventor without a company can still find project support; an opportunity expressly requiring an incorporated investee may require a company before that particular submission.
3. **Typed rules:** retain `field`, `operator`, `value/unit`, `mandatory`, `applies_at`, `verification_mode`, `source`, `version`, and `visibility`. Use a bounded implementation of equality, membership, range overlap, existence and manual review. Narrative requirements without an approved mapping require human clarification; avoid a general executable rule language.
4. **Four item results:** `PASS` means sufficient permitted evidence meets the requirement; `FAIL` means sufficient comparable evidence disproves it; `UNKNOWN` covers absence, conflict, stale or insufficiently reviewed evidence; `NOT_APPLICABLE` requires an explicit reason. Planned functionality cannot satisfy a requirement for existing functionality. An uploaded certificate is different from an appropriately reviewed certificate.
5. **Distinct outputs:** eligibility (`ELIGIBLE`, `NEEDS_VERIFICATION`, `INCOMPATIBLE`), target-specific pitch readiness, provided/reviewed evidence counts, and later development gaps. A future market-entry requirement does not block an early co-development opportunity unless the recipient explicitly requires it at submission. High topic similarity never compensates for a failed mandatory requirement.
6. **Money semantics:** store decimal amount/range, currency, purpose, period, scope, estimate date and funding form. Company-investment requests may name an instrument and legal entity where applicable; company valuation, project cost, license fee, royalty rate and money already raised are different quantities. Compare only compatible bases. Unknown currency conversion or differing bases produce clarification, not invented equivalence. Partial support is relevant only when expressly accepted; the UI explains the remaining requirement.
7. **Ranking:** begin with all authorized candidates for a tiny catalogue, cheap eligibility checks, lexical relevance and deterministic explanations. Add dense retrieval, RRF and a reranker as separately named engine modes. Pin model revision, tokenizer, truncation policy, rule and weight versions. Never mix cosine and cross-encoder output as interchangeable features. A failed model leaves manual forms, rules and brief templates usable.
8. **Uncertainty:** retain missing feature weights rather than renormalizing one known positive feature into a perfect score. A reciprocal fit interval can be a transparent heuristic, provided it is explicitly an index with unknown-information bounds, not a confidence interval. Introduce numerical thresholds only as versioned hypotheses. Show a few reasons, the main gap and the next action; keep detailed scores secondary.

### Gaps

- No labelled cross-sector TemuRiset dataset, investor mandate validation, latency measurement or model comparison was available. Neither source validates a preferred embedding model, fixed candidate count, score threshold or funding prediction for this product.
- The right investment vocabulary depends on the first supported markets and customer workflows. The generic base should represent expressed support and evidence without claiming to decide instrument eligibility or applicable law.

## How should confidential evidence remain protected through matching and AI features?

### Takeaway

Authorization must follow information through its complete lifecycle. Public discovery should use a deliberately public projection; private evidence and its derivatives remain subject to current object-level permissions. Consent to share one pitch does not publish an invention's entire data room.

### Cited Findings

- OWASP recommends least privilege, deny-by-default behavior, authorization on every request, server-side checks, protection of static resources and unit/integration tests for permission logic. Knowing an object's identifier does not grant access to it. — [OWASP, Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- OWASP's multitenancy guidance requires verified context, appropriately scoped caches, authorization before reading protected cached values, and re-establishment of authorization in asynchronous consumers. It distinguishes intentionally global assets from tenant/user-scoped assets and requires object authorization before signing download URLs. — [OWASP, Multi-Tenant Application Security](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)
- OWASP recommends extension/type/signature checks, generated storage names, size limits, authorization, storage outside the web root and appropriate malware/content processing. Client-supplied MIME types are insufficient; public scanning services can themselves create disclosure risks. — [OWASP, File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- OWASP describes indirect prompt injection in retrieved documents, pages and attachments. Its defenses include separating instructions from data, output validation, least privilege and human approval for consequential actions; a prompt alone is not an access-control boundary. — [OWASP, LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)

### Inferences

- **Identity and access model:** an inventor, manager, contributor, rights holder, company and workspace administrator are separate concepts. Onboarding persona assists navigation; membership and named capabilities authorize operations. A reviewer may inspect assigned evidence without possessing an investor's decision authority. This applies object-level authorization to the proposed product model. — [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- **Lifecycle coverage:** evaluate scope for indexing, retrieval, cache reads, previews, AI inputs/outputs, background parsing, generated briefs, export jobs and downloads. Carry permission/version context into queued work and recheck before execution and result delivery. Tenant identity, when applicable, comes from verified membership rather than a submitted identifier. A shared catalogue is an explicit sharing policy, not an exception that exposes private workspaces. — [OWASP Multi-Tenant Application Security](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html)
- **Upload behavior:** accept only supported formats; quarantine new files until permitted checks finish; separate stored, processing, available, rejected and manual-input states. A scanned PDF without supported OCR remains available for appropriately authorized manual review but cannot silently satisfy an extracted-content rule. — [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- **AI authority:** use selected, permitted facts with stable references and source locations. Validate generated references against the provided fact set. AI proposes summaries and extraction drafts; it cannot alter permissions, certify rights, submit pitches, approve investment, or publish relationships. Unsupported output falls back to a deterministic template. — [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)

Additional original product decisions for the generic base: record who asserted each fact, supporting document version/location, current/planned status, review scope, reviewer and date. Treat a public catalogue assertion as source-reported until reviewed. Before sharing, preview the recipient, selected evidence, brief and permitted uses. Separate a nonconfidential public summary from technical detail. Record disclosures and recipients without representing that audit as a signed NDA or proof of ownership.

For revocation, preserve a private submission/audit record according to a documented retention policy while enforcing current access on participant-facing reads. A snapshot must not grant perpetual access to source files or derived confidential briefs. An artifact with revoked dependencies must be denied or safely redacted rather than served from cache. Preserve stable history without silently rewriting the original submission. State clearly that stopping future retrieval cannot recall material a recipient previously downloaded or independently copied. This is a proposed product behavior and operational limitation, not a promise of legal revocation.

### Gaps

- No threat model, provider data-processing review, retention policy, pen test or authorization implementation was audited. These controls describe acceptance requirements, not completed security work.
- Separate deployments cannot automatically discover or message one another. Federation or cross-deployment disclosure needs an explicit protocol, identities, consents and operator agreement; it should not be implied by reusing the same source code.

## What transaction and evaluation guarantees make the generic base credible?

### Takeaway

Reliability should protect human intent: retrying a submission must not duplicate it, competing decisions must not overwrite each other, and selecting a proposed time must not imply a confirmed meeting. Evaluate generic rules and complete journeys across sectors before adding more ranking sophistication.

### Cited Findings

- PostgreSQL documents range exclusion constraints that prevent overlapping reservations, including combining scalar resource identity with a range-overlap constraint through `btree_gist`. This supplies a database mechanism for guarding shared booking resources. — [PostgreSQL, Range Types](https://www.postgresql.org/docs/current/rangetypes.html)
- AWS's transactional-outbox guidance writes the business change and outbox row in one transaction. Delivery can duplicate events; consumers must deduplicate, and a rolled-back transaction must not emit its business notification. The pattern can be applied without adopting AWS services or microservices. — [AWS Prescriptive Guidance, Transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)
- AWS describes caller-provided request identifiers, recording their effects atomically, returning semantically equivalent retry results, rejecting reused identifiers with changed parameters, and explicitly choosing token-retention behavior. — [AWS Builders' Library, Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- scikit-learn explains that using information unavailable at prediction time, or using test data to choose a model/preprocessing, creates optimistic evaluation. It recommends splitting before learned preprocessing and keeping test information out of fitting and model selection. — [scikit-learn, Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)

### Inferences

- Use actor/scope/operation-bound idempotency keys for submit, resubmit, decision, booking and relationship confirmation. Store the request digest and result atomically; same-key/different-body means conflict. A distinct `expected_version` prevents stale decisions: idempotency and concurrency control solve different problems. Choose a documented retention window rather than claiming infinite deduplication. — [AWS idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- Record state, audit event and notification intent in one transaction. Retry delivery separately and deduplicate each event/channel/recipient. An email failure never repeats the business decision. A small PostgreSQL outbox and ordinary worker suffice initially. — [AWS transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)
- Proposed slots do not reserve calendars. Accepting one slot atomically books every required participant; protect overlapping active reservations at the database boundary. A reschedule leaves the previous meeting in force until the replacement succeeds or cancellation is explicit. Store UTC instants plus IANA display zones and show a recoverable conflict. — [PostgreSQL range constraints](https://www.postgresql.org/docs/current/rangetypes.html)
- Split evaluation by meaningful invention/opportunity groups and keep near-duplicate paraphrases together. Tune thresholds and weights on development data, then freeze them for held-out evaluation. Record dataset, permission projection, model/config versions, candidate recall, result count, P@k/nDCG, known-constraint violations, unknown handling, factual support, latency and cost. These metric selections are product recommendations, not reported results. — [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html)

Proposed generic acceptance fixtures should be synthetic and plainly labelled: (A) an independent maker's solar dryer seeking project validation, (B) an irrigation-software team offering a license, (C) an incorporated biomaterials startup seeking company investment, and (D) a manufacturing process with unclear rights and incomplete evidence. Include support partners that accept prototypes, require a company for an expressed mandate, provide noncash facilities, or seek market-ready distribution. Give every fixture explicit expected PASS/FAIL/UNKNOWN outcomes, comparable money bases and confidential-document grants. These examples test domain variation without carrying a competition's real catalogue into the base.

Required behavioral checks include: a planned feature fails a current-feature requirement; missing rights evidence remains unknown; a project grant is not equity; mismatched currencies are not compared without a supported conversion; revoked grants invalidate cached/queued derivatives; two concurrent bookings produce at most one conflicting reservation; retries produce one submission; changed versions require fresh decisions; and a single party's confirmation never publishes a mutually confirmed partnership. Agreeing to discuss is separate from any project, license or equity relationship. Actual relationship records require both authorized parties to confirm the same summary and public-field consent. Material edits invalidate prior confirmations; passing a meeting time alone cannot establish that it occurred.

### Gaps

- No implementation, benchmark or usability test was run. These fixtures need actual executable assertions and participant walkthroughs when the application exists.
- Numerical quality/latency goals should be identified as proposed test targets with dataset and hardware assumptions. A successful synthetic demo does not prove cross-sector matching effectiveness, investment outcomes, security compliance or production scale.

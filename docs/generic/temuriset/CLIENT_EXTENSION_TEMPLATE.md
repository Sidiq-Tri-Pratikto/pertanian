# TemuRiset client extension specification

This is a deliberate template. Replace every square-bracketed field before approval; remove genuinely inapplicable optional sections with a reason. It supplements [the generic base PRD](01_PRD_TemuRiset_Generic_EN.md), rather than copying it. An unmentioned requirement inherits the pinned base version. Client requirements cannot silently disable authorization, evidence labels, money semantics, retry integrity or two-party consent.

## 1. Identity, versions and decision owners

- Extension id/name: [stable id and descriptive name].
- Client/product owner and contact: [responsible party].
- Engineering, security/privacy and release owners: [named roles/contacts].
- Base PRD version and repository commit: [version and immutable commit].
- Shared application source release/artifact digest: [release/digest].
- Configuration schema and configuration revision: [versions].
- Enabled capability ids/versions and adapter ids/versions: [explicit list].
- Database schema/migration level: [version].
- Status, approval date and next review: [draft/approved/retired; dates].

Do not describe a proposed release as deployed. Record distinct approval, implementation, test and rollout states. Identify who accepts changes to the shared base when this extension reveals a common requirement.

## 2. Users, problem and scope

Describe [actual inventor groups], [actual investor/partner groups], their current problem and the outcome this offering should enable. Explain whether personal contexts, companies, community teams and other organizations participate. Keep the two public onboarding personas unless a separately reviewed base change is required; reviewer capabilities are not extra market personas.

State [initial sectors, languages, countries/currencies and recruitment cohort], [supported relationship/support forms] and [explicit exclusions]. Identify what evidence shows complementary supply and demand. Mark assumptions as assumptions. Do not insert universal patents, institutions, revenue or company-registration requirements when only one recipient needs them.

## 3. Exact requirement differences

| Change id | Base FR/AC | Requested behavior and user reason | Classification | Owner/acceptance |
|---|---|---|---|---|
| [EXT-01] | [FRxx / ACxx] | [Concrete before/after behavior] | [content/config/capability/adapter/base change/separate product] | [Owner; exact test] |

For each difference, identify preserved invariants, affected actors, success state, errors/recovery, data changes and migration needs. Add replacement AC only for deliberate changes; retain unaffected base tests. Explain why a configuration or existing capability is insufficient before adding new code. Never scatter checks for the client's name through domain rules.

## 4. Supported composition and disabled behavior

List [brand/copy], [locale/currency configuration], [governed taxonomy/checklist policies], [enabled capabilities] and [real integrations]. For each capability, state its prerequisite and behavior when disabled. A disabled AI adapter must leave manual facts and template briefs usable; disabling a review gate requires resolving queued items. Define historical-record access when new creation is disabled.

Describe each adapter's actual provider, contract version, source mapping, authentication reference, failure/retry semantics and contract-test fixture. Secrets belong in secret storage: include reference names only. State [unsupported combinations] and the validation that rejects them before deployment. Record any temporary rollout flag's owner and removal date separately from persistent capabilities.

## 5. Financial subject and evidence policies

Identify whether requests concern invention project support, licensing or a company/venture raise. Define financial basis, currencies, periods, partial/syndicated support and accepted financing forms. Keep round target separate from desired individual contribution. A raise linked to several inventions remains one raise. Do not infer valuation, share percentages, ownership or committed funding from amounts or pitch state.

For every checklist provide [source URL/document and version], [accountable reviewer], [applicable sector/purpose], [submission/discussion/pilot/commercialization stage], [verification mode], [review/expiry date] and [exception authority]. Unknown evidence remains unknown. Specify any actual entity requirement for a selected opportunity; distinguish company financing stage from invention maturity.

## 6. Information sharing, privacy and operations

Define [marketplace boundary], [personal/organization workspaces], [public projection] and [named counterparty grants]. State whether this is the common marketplace or a separate deployment. Separate deployments do not automatically share accounts, catalog entries, grants or conversations. If a true tenant boundary is proposed, define its business meaning and enforcement across database, caches, jobs, files, search, exports and support access.

Record [retention periods], [deletion/hold exceptions], [backup expiry], [operator access purpose], [approved model/provider processing], [incident contact] and [download-revocation wording]. Confidential source revocation must affect derived outputs and pending jobs; prior recipient copies cannot be recalled. An NDA acknowledgement or confirmed relationship must not be presented as executed legal verification.

## 7. Acceptance and release matrix

| Composition/journey | Fixture and expected outcome | Core/extension AC | Evidence/status |
|---|---|---|---|
| [Default core] | [Independent inventor and investor path] | [ids] | [Not run/result/environment] |
| [Client variation] | [Enabled capability success/recovery] | [ids] | [Evidence] |
| [Disabled/failure path] | [Fallback, stale state or revoked access] | [ids] | [Evidence] |
| [Migration/rollback] | [Old/new versions and restore oracle] | [ids] | [Evidence] |

Include permission boundaries, duplicate retries, conflicting decisions/booking, financial-basis mismatch, funding-request deduplication and both-party confirmation. Use fictional fixtures until real-data permission is established. Define measured NFR conditions rather than claiming production capacity from a demonstration.

## 8. Rollout, maintenance and retirement

Record [supported source/config/schema inventory], [deployment operator], [shared-fix/backport owner], [support window], [upgrade cadence], [migration/restore evidence] and [rollback or forward-repair procedure]. State the data-loss window when restoration is necessary. Define canary checks, staged rollout approval and how actual deployment versions are verified.

Explain which reusable improvements return to the common source and how this client consumes them. If a deliberate fork exists, identify its maintenance cost and reconciliation owner. Set [retirement/export plan] for the extension and its data. The extension is approved only when these responsibilities and the changed behavior are concrete and reviewable.

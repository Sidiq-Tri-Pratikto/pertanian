# Implementation Plan: Scope API

**Branch** `028-scope-api` | **Date** 2026-10-30 | [Spec](spec.md)

## Project structure

```text
app/scope/
├── dependencies.py
├── selection_dependencies.py
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{errors.py, proposal.py, selection.py, service.py, validity.py}
migrations/versions/0010_create_aggregation_selections.py
```

Use the existing FastAPI request session, Postgres site locks and 009 summary and authority calculations. Add a site selection and membership table on the actual Alembic head. Sites without a saved row keep the all-active default.

## API contract

| Route | Behavior |
|---|---|
| `GET /api/v1/sites/{site_id}/aggregation-selection` | Return raw `selected_asset_ids`, `selection_revision`, `binding_revision`, issues, relations including containment, and current source authority and candidates at site time. |
| `POST /api/v1/sites/{site_id}/aggregation-selection/preview` | Evaluate asset IDs, authority actions, disjoint confirmations, and period. Return both revisions and the standard summary shape, including the resolved window, scope, rows, exact totals or null with reasons, and source conflicts. Return the stored candidate bindings for proposed members whose ranges intersect the resolved period, with binding, source and asset IDs, explicit authority status, and original half-open spans. The summary reflects the projection. Preview performs no persisted writes. |
| `PUT /api/v1/sites/{site_id}/aggregation-selection` | Confirm the same proposal with both expected revisions and the preview's resolved timezone and inclusive local start/end dates. Return the confirmed raw selected IDs and both revisions. |

Use the existing local date and preset forms, with the 366-day limit. Resolve the period under the site lock using one captured site time per calculation. PUT resolves the original period request again and compares timezone and local dates with the preview. A timezone change or preset rollover returns `SCOPE_STALE`. The measurement cutoff may move within the same period. PUT reruns validity with the new cutoff and latest measurements and returns no success if the proposal is now invalid. Preview stores no token or draft.

Use selection revision `0` and the all-active IDs for a legacy site without a row. The first explicit save creates revision `1` even if those IDs match the default. Compare membership as a set. Keep stored archived IDs in GET and PUT responses, exclude them from calculations with the archived reason, and reject newly adding archived IDs. An unchanged proposal retaining a stored archived member can round-trip without an audit or revision increment. Restore makes the member eligible again. New assets join the default only on sites without a saved selection. Demo reset clears the saved row and advances the binding fence.

The site summary adds nullable `selection_revision` and `binding_revision` fields from the same state as its included/excluded IDs, resolved dates, timezone and cutoff. A current site response always supplies the binding revision and supplies a selection revision only for a saved selection. Legacy responses and explicit asset summaries may lack these fields or use null. Preserve the meaning of `SummaryResponse.revision` as binding plus measurement revision. 029 uses both scope revisions, exact IDs and the existing owner/epoch to classify and fence 034 snapshots. Preview responses are ineligible for the confirmed summary cache.

## Evaluation and transactions

Take an owned site row `FOR SHARE` before reading any scope or measurement state for GET, preview and site summary. Hold it in the same `SessionDep` transaction as the selection, asset, binding and measurement reads. Use the current locked site row. This serializes reads against the existing site writers without mutating domain rows. PUT acquires the owned site row `FOR UPDATE` before loading current state and comparing revisions. Both operations reuse one projected evaluation over the 009 rules. Project preview changes in memory and keep repository writes and audit out of reads.

Resolve half-open authority as 009 does, including an implicit single candidate. If distinct selected assets would count the same source over an intersecting span, report a typed `shared_source` issue identifying the pair and refuse the combined total and shares even when a disjoint relation exists. Evaluate at site time for GET and over the resolved elapsed interval for preview, PUT and site summary. Touching endpoints alone do not create an overlap. Check the authority spans independently of measurement presence. Keep existing parent/child, unknown and unresolved candidate refusals and keep safe individual rows visible. At zero elapsed time, evaluate structural validity independently of missing data.

Each choose action identifies one owned asset and a source with an unambiguous binding candidate at the supplied effective instant. Use `[effective_from, min(candidate end, next strictly later preexisting explicit authority start))`, treating a missing end as unbounded. Split or demote old authority within that interval and split or promote the chosen candidate. Preserve prior and later attribution, unrelated bindings and source readings. A choose action is a no-op only when the chosen source is already explicitly authoritative across the planned interval. An implicit single source made explicit is a versioned authority change. Skip leaves existing bindings and any unresolved conflict in force.

Confirm disjointness by removing unknown-overlap edges in either direction and creating one positive relation for the unordered pair if no positive evidence exists. Refuse self-pairs and direct or transitive containment. Revalidate the full projected state under the lock and persist it atomically. Advance the selection revision once for the first or changed membership. Advance binding revision once if any bindings or relations change. Store actor, subject and revision in each change audit. Record actual effective bounds for authority. Store the reviewed window separately from the site-wide effect of selection or relation changes. A failed or unchanged write leaves revisions and audit intact.

## Errors and input limits

Validate before pairwise evaluation. Accept 1–100 distinct members, at most 100 choose/skip actions with one per asset, and at most 200 unique unordered confirmation pairs. That supports all 190 pairs of a 20-asset pilot. Foreign nested resources return the same `NOT_FOUND` as absent resources.

Map overlap to `SCOPE_CONFLICT` (409) using `APP-SCOPE-OVERLAP`. Identify affected pairs with stable issue types and owned names sanitized through `redact_text`. Limit error detail entries to 20 in deterministic order and keep the diagnostic generic, with no labels or proposal body. Map changed expected revisions or reviewed period to nonretryable `SCOPE_STALE` (409) with instructions to preview again. Use the existing error envelope and field detail shape.

## Verification and boundaries

- Pin AT-35, AT-36 and AT-36b, including same-source overlap with positive disjointness, implicit authority and adjacent intervals. Cover stored archived membership, stale main meter, preserved history, and valid H/I totals.
- Use real Postgres and separate sessions with barriers for read/write coherence, simultaneous confirmations, and binding or import races. Check no preview writes and rollback after a late failure following audit and revision writes. Cover owner isolation, credential-like names in overlap details and logs, bounded requests, timezone/preset staleness and a moving cutoff.
- Verify populated upgrade and downgrade, one Alembic head, the generated contracts and API/mobile checks. Record local PostgreSQL 16 separately from PostgreSQL 17 CI evidence.
- 029 owns S11, client confirmation and cache behavior. Explicit asset summary, history, and per-asset insight evaluation retain their caller semantics. Phase-total adapters (046) and topology editing are outside 028.

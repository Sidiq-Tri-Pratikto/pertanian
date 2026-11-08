# Implementation Plan: Scope screen

**Branch** `029-scope-s11` | **Date** 2026-10-30 | **Spec** [spec.md](spec.md)

## Project structure

```text
applications/hematdaya-mobile/
├── src/features/scope/{useSelection.ts,useScopeDraft.ts,ScopeScreen.tsx}
├── src/app/(tabs)/(beranda,perangkat,saran)/cakupan.tsx
├── src/components/hd/HDScopeSummary.tsx
├── src/api/client.ts
└── src/features/{offline,navigation-context,energy,workspace}/
```

Reuse Expo Router's shared detail stack, TanStack Query and 034's attested owner storage, connectivity and local scope epoch. Use the merged [028 contract](../../contracts/openapi.json) unchanged.

## Review and confirm

Read raw membership and current relations from the owned selection GET. Its authority, candidates and issues describe site time. For the reviewed period, use POST preview for server-computed rows, scope validity, and candidates. Keep membership, authority choice or skip, and explicit disjoint confirmations in the draft. Drop actions for excluded or archived assets, including disjoint pairs involving them. Any draft edit or change to the active period invalidates the review. Cancel discards the draft and returns to the invoker. Track an already dispatched write outside the screen's lifetime.

Use separate bounded, read-only previews to show an alternate parent view, child group or individual asset, with only the applicable draft actions. Retain the server's original window and cutoff for each response. Associate each option with its proposal and base revisions, and show unavailable values with their reason. An alternate preview cannot authorize saving the draft. Obtain period-specific candidate bindings by previewing the relevant asset without the pending authority action when necessary. Select candidates by binding ID. Send their source and asset IDs and show the effective instant before confirmation. Use the later of the candidate start and the server-resolved window start, strictly before both the candidate's finite end and the reviewed cutoff. When several bindings for the same source cover that instant, keep the choice unavailable with a reason. Skip leaves the existing authority as evaluated by the server.

Send the exact reviewed proposal with its original preset or explicit dates, top-level expected selection and binding revisions, and the resolved local dates and timezone from the preview summary. The service resolves the original period again, rejecting a changed local period or either revision. A cutoff can move within the same local period and new measurements can affect the server's revalidation. Use one explicit PUT per intent. Require a valid 200 response, exact raw membership, and plausible revision changes for that request. Membership changes, including the first explicit save, advance selection by one. Binding or relation edits advance binding by one. A no-op can return the base pair. An invalid or lost response after dispatch is uncertain.

## Recovery and confirmed summaries

Before dispatch, persist a non-executable attempt marker in the attested owner/site namespace, recording the base revision pair and enough local identity to distinguish the sole attempt from a preexisting uncertain one. A failed write blocks PUT. A same-pair owned GET cannot rule out a pending commit. Keep the marker through a later same-base no-op or refusal. Clear an older marker only after a higher trusted pair has been durably fenced. A definitively unsent or rejected sole attempt can clear its own marker. The marker carries no proposal body or replay instruction.

On stale or definite rejection, keep the draft and obtain fresh review before a new confirmation when needed. After an uncertain write, allow a fresh owned preview and a separate explicit confirmation under compare-and-set. Every mutating success advances at least one revision token. An earlier in-flight request and a later request using the same base cannot both mutate successfully. A newer observed state establishes the current scope and does not attribute the result to a particular write. Never automatically resend on reconnect, remount, refresh or recovery. Show a distinct message when the write is acknowledged but refresh or local storage fails.

Order trusted revision pairs by binding first, then selection, because a reset advances binding and can clear selection. An older valid acknowledgment never replaces a newer trusted observation. Observe newer pairs from regular confirmed site summary reads as well as S11 GET/PUT. Advance the existing owner/site scope fence once before exposing newer state, reject older completions, and refresh affected reads after an S11 save. Selection affects the site summary and scope notices. Authority edits also affect the relevant asset reads. `Periksa sumber` remains a bounded summary GET, with no extra eager selection or Saran request. A validated fresh summary GET that discovers a newer pair can supply that pair's summary after fencing.

Use the fresh confirmed summary GET as the only source of confirmed figures and fetch time. Bind its exact eligible IDs and scope revisions to the attested owner, local scope epoch, resolved dates, timezone, UTC bounds and cutoff. Keep raw selected IDs separately. Where both responses are present at the same pair, eligible IDs equal raw membership minus archived IDs from that summary. A current site summary's non-null binding revision with null selection revision corresponds to selection revision zero. Missing pair evidence is distinct. Show legacy v1 site snapshots only as previous scope with original labels and fetch time. Keep exact explicit asset snapshots usable independently. An outstanding attempt marker blocks hydration of prior site snapshots as current until reconciliation. If fencing or cleanup fails after acknowledgment, retain known state in memory and fail closed for hydration where the marker or revocation is durable. When an external change is observed during total local storage failure, the process fences it in memory. A cold offline launch cannot know about that observation if every attempt to write the fence or revoke the old namespace failed.

## Entry and verification

Beranda's scope control and Beranda/Perangkat issue actions open S11 in the active tab. Redirect the old `segera-hadir/cakupan-sumber` path in the same tab. Return focus to the invoker or the tab heading if that control disappeared. Verify choice and notice semantics, keyboard navigation, text enlargement and 320 px layout.

Use the existing [prototype P09 oracle](../../docs/reference/prototype/ACCEPTANCE.md) for interaction and the merged 028 service for values. Run the Chromium live flow against core-only API/Postgres at `http://localhost:58029` using the 25 October 2026 `h-scope` fixture. For Android, extend the existing live-data `CASE=scope` flow to open, preview and cancel S11 with bounded waits. Retain its weekly `70.000` kWh check and assert zero PUTs to the scope endpoint specifically. The existing CI job runs it. Record local Android as unverified when an SDK or AVD is unavailable.

Topology editing and new API endpoints are out of scope.

# Feature Specification: Offline and combined states

**Feature Branch**: `034-offline-states`
**Created**: 2026-10-30
**Status**: Planned, implementation pending
**Milestone**: M8 Recovery
**Depends on**: 010, 016, 022, 023, 027
**Size**: M
**Covers**: FR-15, FR-18, UX-05, UX-11, AT-38, AT-40, AT-57, P08
**Flips**: registry `data-tersimpan` → `available`

## User scenarios and testing

### User Story 1 - Keep reading offline (Priority: P1)

**Why this priority**: FR-15 calls for cached data with timestamp, scope and quality.

**Independent Test**: Confirm a demo workspace and load a chosen period online. Go offline, edit an asset and try to save. Restart in the same workspace with the API still unavailable. Open a different confirmed workspace without wiping app storage.

**Acceptance Scenarios**

1. **Given** a cached summary, **when** the device is known offline, **then** “Offline · menampilkan data tersimpan” appears alongside the original fetch time, resolved period and scope. If the matching snapshot is absent, the app explains that no data for that selection was saved.
2. **Given** an offline save attempt, **when** the user edits, archives, restores, previews or confirms an import, or sends feedback, **then** the app reports the action was unsent, keeps applicable input and sends zero writes on reconnect. An earlier attempt whose outcome is uncertain retains its own status.
3. **Given** an unexpired, previously confirmed workspace with a saved summary and draft, **when** the app restarts with local storage available, **then** it restores the last confirmed chosen period and scope and lets the user open the draft even if asset detail cannot be fetched. A different, expired or unconfirmed owner cannot see that cache or draft.
4. **Given** a restored asset draft, **when** the user comes online, **then** a fresh owned read establishes the current baseline before a new explicit save. If the server already matches the intended edits, the app reports the observed result and sends no PATCH. Changed fields that still differ from the draft require review before a new explicit save.
5. **Given** a 027 import whose commit was previously attempted, **when** the confirmed owner reloads or resumes the supported web flow, **then** they can explicitly check status and, if the same preview is still pending, explicitly resend it with the same key. Reconnection and hydration alone never dispatch it. A selected file requires reselection where its bytes are unavailable.

### User Story 2 - States stay independent (Priority: P1)

**Why this priority**: PRD §13 distinguishes availability, time coverage, provenance, freshness, evidence and scope.

**Independent Test**: Run the five real-data combinations in [tasks.md](tasks.md) with the core-only API.

**Acceptance Scenarios**

1. **Given** offline plus a stale source, **when** shown, **then** client fetch time and last source capture appear separately. A retry cannot fabricate a reading.
2. **Given** committed historical CSV plus offline, **when** shown, **then** import provenance, data period and last historical capture remain visible without a live-disconnection claim.
3. **Given** learning plus partial data in core-only, **when** shown, **then** recorded kWh, gaps and insufficient comparison remain available alongside valid history. Estimated cost has no numeric amount.
4. **Given** valid zero energy in core-only, **when** shown, **then** the energy is numeric zero and the cost remains unavailable.
5. **Given** a scope conflict with known individual values, **when** shown, **then** the unsafe combined total and its shares are refused. Known individual readings and history remain available. A source-conflicted asset retains its own unavailability reason and alternate-source values.

### User Story 3 - Stale means stale (Priority: P1)

**Why this priority**: PRD §13 defines “Data belum diperbarui” as a reading status.

**Independent Test**: With a one-hour recurring source, compare freshness at exactly two hours since the last valid capture and immediately after two hours.

**Acceptance Scenarios**

1. **Given** a recurring source under a current effective binding with a positive known cadence and a last valid completed capture older than two intervals, **when** shown, **then** last capture, cadence and “Periksa sumber” appear. Exactly two intervals is within the threshold.
2. **Given** historical CSV, unknown cadence, no valid completed capture or a source with no expectation of recurring capture, **when** shown, **then** elapsed time alone never marks it stale.
3. **Given** a source recheck, **when** the API is reachable, **then** the app performs only a bounded summary read for that scope. A failed recheck keeps the previous snapshot and timestamp. A successful recheck can advance the fetch time even if the source capture stays unchanged.

### Edge cases

- Explicit online recovery keeps 016's one-shot PATCH and read-based observation, 023's manual same-key feedback check, and 027's status-first import flow.
- A known scope change invalidates the earlier scope for new reads. Prior snapshots may appear only with their original resolved period and scope and a clear previous-scope label.
- Local storage failure leaves usable in-memory input, with an honest limit on restart recovery. A failed wipe is reported as a storage failure.
- A demo reset through the app uses the existing server contract and invalidates pre-reset local data even though site and token stay the same. An external reset or revocation cannot be detected while fully offline. The app enforces known expiry locally and revalidates when it can reach the service.
- Before the first workspace is confirmed, S10 may retain user input in memory and attach it once to that first workspace. Once attached, input belongs to that owner.
- After 019 ships, verify learning plus partial plus missing tariff and valid zero plus missing tariff as separate integration cases.
- Saved-account expiry and sign-in recovery belong to 037. Selection persistence and the scope screen belong to 028/029. 034 verifies real refusal using the merged summary/history paths.

## Requirements

- **FR-001**: Persist the latest successfully fetched summary for each supported exact period and scope, with its original fetch-completion time and resolved window, cutoff, timezone and scope IDs. Restore the last confirmed selection. Hydration, placeholder data, failed refresh and local cache updates cannot advance the fetch time.
- **FR-002**: Distinguish client connectivity, service reachability, freshness, historical provenance, completeness, learning and scope validity in the data and the interface.
- **FR-003**: Require an explicit online action and a confirmed or observed outcome for each write. Guard known-offline dispatch, retain applicable drafts and preserve manual recovery for an actually attempted operation. Never enqueue writes or replay them automatically.
- **FR-004**: Use a single service freshness policy based on the site clock, effective source authority and latest valid completed capture. Use a strict threshold of more than two known recurring intervals. Historical imports and unknown cadence never imply stale transport. A source recheck is a read.
- **FR-005**: Scope persisted reads and allowlisted drafts to a confirmed principal/workspace/site and its active lifecycle epoch. Block mismatched, expired and unconfirmed restoration. Fence in-flight work and clear or revoke its durable namespace on logout, workspace change, expiry and demo reset.
- **FR-006**: Fence responses from an earlier scope epoch after an acknowledged or observed scope-changing operation. Treat the future 028 selection revision as independent of the current summary data revision.

### Key entities

- **CachedSummary** retains its original server response, selected period and scope, and fetch-completion time.
- **Draft** retains only supported editable fields, baseline, and minimal information needed to resume the applicable form.
- **Workspace epoch** controls which confirmed credential binding may read and write those records.

## Success criteria

- **SC-001**: Pass the core recovery and combination matrix on Chrome and on a real Android emulator with a live test API and Postgres. Capture each runtime separately, including true offline on a loaded web tab, a same-tab reload with shell available and API blocked, and native offline process cold launch.
- **SC-002**: No scenario fabricates equipment status, energy, cost, or acknowledgment.
- **SC-003**: Demonstrate zero outbound writes while known offline and on reconnect, owner isolation with previous app storage still present, and read-only source recheck.

The separate household and industrial walkthroughs with P1 require the M6 merge and complete the joint MVP sign-off after 034 feature acceptance.

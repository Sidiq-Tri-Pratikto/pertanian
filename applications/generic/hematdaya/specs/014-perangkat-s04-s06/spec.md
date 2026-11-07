# Feature Specification: Perangkat and asset detail

**Feature Branch**: `m2/perangkat`
**Created**: 2026-10-30
**Status**: Implemented on base `6563a2f`, not yet merged. Exercised in Jest, in the web build on Chromium 152 against a live API, and through the API's integration tests. Android beyond the smoke flow was not run, and that job's result on this PR is still to be read
**Milestone**: M2 Read journey on phone
**Depends on**: 010, 013
**Size**: M
**Covers**: UX-13, UX-14, S04, S06, P03
**Flips**: registry `daftar-perangkat` → `available`

**Also reads**: the stale notices from 021's insights route, merged in `6563a2f`. `check_traceability.py` refuses a later spec number under **Depends on**, so it is named here instead. 014 calls no route from 010: its history route is 015's.

## User Scenarios & Testing

### User Story 1 - See every measured thing (Priority: P1)

**Why this priority**: S04 lists devices, groups, circuits and site-total meters with visible scope labels.

**Independent Test**: Open Perangkat in `h-base` and in `h-scope`.

**Acceptance Scenarios**:

1. **Given** `h-base`, **When** Perangkat opens, **Then** four rows show name, scope kind, location, category when present, kWh and quality for the shared period, in the service's order: largest first, unavailable last, then name, then asset ID.
2. **Given** `h-scope`, **When** Perangkat opens, **Then** Meter utama shows the scope kind "Meter lokasi", individual values remain, no combined total shows, and the scope notice explains the conflict.
3. **Given** any row, **When** inspected, **Then** it is one link with no nested button, and no switch, power icon or "paling boros" label appears.
4. **Given** no workspace or a workspace with no asset, **When** Perangkat opens, **Then** "Belum ada perangkat" shows with Tambah sumber, Impor data and Coba demo, and no number or date. With no workspace it makes no request.

### User Story 2 - Open one asset in context (Priority: P1)

**Why this priority**: Period and scroll must survive the round trip (UX-05, UX-14).

**Independent Test**: Scroll, open, go back. From Beranda, count one tap to the asset.

**Acceptance Scenarios**:

1. **Given** a row, **When** opened, **Then** the detail shows the same period, name, scope kind, kWh, coverage, gaps and source provenance, and no share.
2. **Given** detail opened from the list, **When** Kembali is pressed, **Then** the list returns at the same scroll position and tab, without reloading.
3. **Given** an empty period, **When** detail opens, **Then** it offers Lihat periode data and shows no zero. On the workspace's initial period itself the action does not appear, because pressing it would change nothing.
4. **Given** a Beranda ranking row or Lihat perangkat terbesar, **When** pressed, **Then** its asset detail opens in one tap with the same period, and Kembali returns to Beranda. Lihat perangkat terbesar appears only when the service gives the largest row a share, so not on a zero total or a scope conflict.
5. **Given** an unknown asset, another owner's asset or no workspace, **When** detail opens, **Then** "Perangkat tidak ditemukan" shows with Kembali, and never an endless loading state.

### Edge Cases

- Full names wrap and are never truncated.
- A stale simulated source says "Data belum diperbarui" and never says the device is off. The only "mati" on screen is the service's "Ini bukan tanda perangkat mati." Stale and partial show together.
- Loading or failure never replaces a known list or detail. Rows, values and the period selector stay, with a status. A failed period change counts.
- An asset with two unresolved sources shows each source value separately, on its row and on detail, and no sum.
- A failed read of location or of freshness removes only that fact and says so. The energy values stay.

## Requirements

### Functional Requirements

- **FR-001**: Rows MUST show recorded kWh and quality, or an explicit unavailable state. Gap, unknown value, measured zero and partial coverage MUST read differently.
- **FR-002**: The list and detail MUST use the shared period. Scope is what the service's response states: the site's default selection on the list, and the asset itself on detail. 014 sends no scope parameter, because no route takes one until 028.
- **FR-003**: Detail routes MUST live in the shared tab folder.
- **FR-004**: Primary **Tambah sumber** and **Impor data** MUST stay reachable through the existing Segera hadir screens until 035 and 027 ship their respective flows. 026's merged commit route does not change this.
- **FR-005**: Each screen showing a number MUST state its period, measurement scope and origin, with simulated and imported data kept apart. Detail takes origin from the asset's sources, so it survives an empty period and a source conflict.
- **FR-006**: The client MUST NOT sort, sum or compute. Values, order, coverage and staleness come from the service. Staleness comes from its `stale` notices, never from comparing a timestamp with a cadence.
- **FR-007**: A failure MUST show the service's message and reference ID, and offer retry only when `recovery.retryable` is true.
- **FR-008**: Rows MUST be one link with a full accessible name and a 48 × 48 minimum target. Screens MUST keep font scaling and safe areas, announce status changes through a status region, and add no animation.
- **FR-009**: Scope and source-conflict notices MUST carry no scope-resolution link until 029.
- **FR-010**: Settings MUST list only features whose status is `coming_soon` under "Rencana fitur", so `daftar-perangkat` stops being called "segera hadir" when it flips.
- **FR-011**: 014 MUST NOT change the API or the contract, and MUST NOT depend on 027 or 035. `contracts/openapi.json` and `src/api/schema.generated.ts` stay as they are at the base.

### Key Entities

Asset, source and binding from 005. Summary row from 009. Notice from 021.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Each asset's kWh and coverage agree between list, detail and Beranda when shown for the same period. Jest compares the three screens from responses recorded from the service, and an API test proves the site and asset summary routes give the same row apart from `share_percent`.
- **SC-002**: On web, the scroll position after Kembali equals the position before the row was opened, measured in a named browser. On Android this stays **not run** until a native run reaches a populated workspace, because the smoke job has no API. The PR says so and reports no Android result for it.
- **SC-003**: The Android smoke job passes with `e2e/smoke.yaml` unchanged. It proves the app builds and starts and that Perangkat's no-workspace state renders, and nothing more.

## Open Items

- PRD S06 lists related insights and the handoff adds a Saran row to S08, but no spec owns them. Default: 014 does not build them, and the owner decides where they go.

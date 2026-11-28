# Feature Specification: Match breakdown per aspect

**Feature Branch**: `057-match-breakdown`
**Created**: 2026-11-28
**Status**: Seeded, not started
**Milestone**: Revamp 2, demo feedback ([plan](../../docs/roadmap/revamp-2-demo-feedback.md)); Track A
**Depends on**: 019, 020, 055
**Size**: M
**Covers**: FR11, AC77, AC78, AC79, S10, S12
**Flips**: nothing

## Context

A match today shows one label ("Kecocokan lemah") and a range ("20–54 dari 100"). Demo feedback: both sides want to see how each aspect matches, for example "Bidang 100%, Detail produk 70%, Kesiapan 40%". This spec makes every match result carry a **breakdown** of eight dimensions. It changes how two inputs are read (topic now looks at the whole product text, and readiness now includes TKT), so the matching policy version goes up and the golden files are regenerated and reviewed.

## The eight dimensions

Each dimension has a 0–100 score or `null` when unknown, a status, and the raw values that explain it. Scores are rounded to whole numbers.

| Id | Label (ID / EN) | How the score is computed | Counts in fit? |
|---|---|---|---|
| `sector` | Bidang / Field | 100 when the invention's sector is in the mandate's sectors, else 0. Unknown when either side states none. | Yes, weight 0.15 (need side) |
| `topic` | Topik dan detail produk / Topic and product detail | Share of the mandate's keywords found, case-insensitively, in the invention's keywords, title, summary, problem or solution, as whole words. Unknown when the mandate lists no keyword. | Yes, weight 0.45 (need side); replaces keyword-only overlap |
| `readiness` | Tahap dan TKT / Stage and TKT | Mean of: stage (100 if accepted, else 0) and TKT (100 if TKT ≥ minimum, else max(0, 100 − 25 × gap)). A part that is unknown or not asked is left out of the mean; unknown when both are left out. | Yes, weight 0.15 (need side) |
| `money` | Dana / Funding | Compared whenever both sides state a comparable range, with or without a budget requirement on the mandate (today only a budget requirement triggers it): 100 when ranges overlap on the same basis; 50 when they do not but partial support is accepted; 0 otherwise. Unknown when not comparable. | Yes, weight 0.15 (need side) |
| `form` | Bentuk kerja sama / Form of partnership | 100 when the need's form is one the mandate accepts, else 0. Unknown when the need has none. | Yes, weight 0.30 (mandate side) |
| `requirements` | Syarat wajib / Required items | Share of the mandate's entry-stage required items that pass. Status MISMATCH if any fails, UNKNOWN if any is unknown and none fails. Not applicable when the mandate lists none. | No: decides eligibility, as today |
| `evidence` | Bukti / Evidence | Share of applicable items backed by provided or reviewed evidence. Not applicable when there are none. | No: shown for trust |
| `availability` | Ketersediaan investor / Investor availability | 100 when the mandate takes pitches now, else 0. | Yes, weight 0.15 (mandate side) |

Status: `MATCH` ≥ 80, `PARTIAL` 40–79, `MISMATCH` < 40, `UNKNOWN` (null score), `NOT_APPLICABLE`. Timing (weight 0.10) stays unknown, as today, and is not shown as a dimension.

The headline fit range, coverage and label keep their current meaning and formula (harmonic mean of both sides, unknowns widen the range). A failed required item still makes the result "Tidak cocok untuk target ini" whatever the other dimensions say.

## User Scenarios & Testing

### User Story 1 - The inventor sees each aspect (Priority: P1)

1. **Given** a match, **When** the inventor opens it, **Then** below the label they see "Rincian kecocokan": eight rows, each with the name, a bar, the percentage or "Belum diketahui", a status word, and one sentence such as "Mandat mencari TKT 6 ke atas; produk Anda TKT 4." Each name has a Toggletip explaining how it is scored (AC77).
2. **Given** the demo scenario after 056, **When** Inovator A matches Produk B against Investor B, **Then** Bidang 100, Topik 100, Tahap dan TKT 100, Dana 100, Bentuk 100, Ketersediaan 100; and Produk A against Investor A shows Bidang 0, Topik 25 (only "desa" found) and Tahap dan TKT 25 (stage Prototipe not accepted = 0, TKT 4 against minimum 6 = 50).
3. **Given** a required item fails, **Then** "Syarat wajib" shows the failing item and the label stays "Tidak cocok untuk target ini" (AC78).
4. **Given** an old run stored before this spec, **When** read, **Then** the breakdown is empty and the card says "Hitung ulang untuk melihat rincian" with a button that runs the match again.

### User Story 2 - The investor sees the same breakdown (Priority: P1)

1. **Given** a pitch is submitted, **When** the recipient opens the pitch room, **Then** the summary tab shows "Kecocokan dengan mandat Anda" with the label, range and the same eight rows, frozen at the submission they are reading (AC79).
2. **Given** a resubmission, **Then** the breakdown shown is the one frozen with that submission.
3. **Given** an investor viewing a published invention in Jelajahi, **When** they have at least one active mandate, **Then** the detail shows "Kecocokan dengan mandat Anda" for each of their mandates, computed from the public projection only (money and form unknown, labelled "Pratinjau dari profil publik"). Nothing is stored. (P2)

## Requirements

- **FR-001**: Pure function `breakdown(source, target, rows, fit_inputs) -> list[Dimension]` in `app/matching/engine/breakdown.py`; `evaluate()` adds `"breakdown"` to its result. No I/O.
- **FR-002**: `topic` uses a whole-word, case-insensitive match over the invention's keywords, title, summary, problem and solution; the matched and missing mandate keywords are returned.
- **FR-003**: Policy versions: `matching-weights` stays 1, add `"fit-features": 2`. Golden files regenerated with `UPDATE_GOLDEN=1` and the diff reviewed in the PR description.
- **FR-004**: The pitch submission snapshot stores `match: {label, fit, breakdown}`; the recipient's pitch view returns it.
- **FR-005**: `GET /api/v1/inventions/{id}/fit` for an acting party with active mandates returns one preview result per own mandate (P2). Registered in the isolation harness.
- **FR-006**: The web formats each sentence from raw values (`tkt.ts`, sector labels, money format); the API sends no prose for dimensions.

## Success Criteria

- Every result in a run has eight dimensions; unknown is never shown as 0%.
- The golden diff touches only the expected fields (`breakdown`, `topic` and `readiness`-driven fit values) and is explained in the PR.

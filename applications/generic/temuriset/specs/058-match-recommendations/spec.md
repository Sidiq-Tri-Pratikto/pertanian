# Feature Specification: Recommendations to improve a match

**Feature Branch**: `058-match-recommendations`
**Created**: 2026-11-28
**Status**: Seeded, not started
**Milestone**: Revamp 2, demo feedback ([plan](../../docs/roadmap/revamp-2-demo-feedback.md)); Track A
**Depends on**: 057
**Size**: M
**Covers**: FR11, AC80, AC81, S10
**Flips**: nothing

## Context

Inventors can see that a product matches an investor, but not what to do about it. With the breakdown from 057 we know exactly which aspects fall short. This spec turns each shortfall into a concrete, honest recommendation: what the investor is looking for, what the product states now, where to change it, and what the change could do to the match. It is for the inventor only.

## Principles

- **Honest by construction.** Recommendations are conditional ("Bila produk Anda memang…"). The product never suggests stating something untrue, never edits anything itself, and for aspects that cannot change quickly (field, stage) says so and offers other investors instead.
- **Blocking first.** A failed required item comes before anything that only raises the score.
- **Show the effect.** Each recommendation carries an estimate computed by the same engine ("Perkiraan: bisa naik ke Kecocokan potensial, 54–80"), labelled as an estimate.

## Rule table

| Trigger (from 057 breakdown or requirement rows) | Recommendation (ID, shortened) | Where (deep link, see plan §3 of the revamp page) | What-if used for the estimate |
|---|---|---|---|
| Required item FAIL or UNKNOWN with `action` | "Syarat '{label}': {reason}" with the engine's action: add a document, add a fact, complete the range, confirm authority | `#dokumen`, `#fakta`, `/support-requests/{id}#kisaran`, settings | the item passes |
| `topic` < 100 | "Investor ini mencari: {missing}. Bila sesuai dengan produk Anda, tambahkan sebagai kata kunci atau jelaskan di ringkasan." | `#kata-kunci` | all missing keywords present |
| `readiness`: TKT below minimum | "Mandat mencari TKT {min} ke atas; produk Anda TKT {tkt}. Bila uji terbaru sudah mencapai tingkat itu, perbarui TKT dan lampirkan buktinya." | `#tkt` | TKT = minimum |
| `readiness`: TKT not stated and the mandate sets a minimum | "Nyatakan TKT produk Anda. Investor ini mencari TKT {min} ke atas." | `#tkt` | TKT = minimum |
| `readiness`: stage not accepted | "Mandat menerima tahap {accepted}; produk Anda {stage}. Perbarui tahap hanya bila produk sudah maju; jika belum, lihat investor lain." | `#tahap` + finder | none (no estimate shown) |
| `money` unknown | "Lengkapi kisaran biaya kebutuhan ini agar investor dapat membandingkan." | `#kisaran` | ranges overlap |
| `money` 0 or 50 | "Kisaran Anda {source} tidak beririsan dengan {target}. Pertimbangkan menerima dukungan sebagian atau menyesuaikan cakupan." | `#kisaran` | ranges overlap |
| `form` 0 | "Mandat menerima {target}; kebutuhan Anda {source}." | `#bentuk` | form accepted |
| `evidence` < 100 | "Lampirkan bukti untuk: {items}." | `#dokumen` | items provided |
| `sector` 0 | "Mandat ini untuk bidang {target}; produk Anda {source}. Bila produk juga melayani bidang itu, jelaskan di ringkasan; jika tidak, lihat investor lain." | `#sektor` + finder | none |
| `availability` 0 | "Investor ini sedang tidak menerima pitching. Simpan atau ikuti investor ini." | none | none |
| Product has no need (preview, 059) | "Buat kebutuhan dukungan untuk produk ini agar dana dan bentuk kerja sama bisa dinilai." | `/support-requests?invention={id}#baru` | none |

## User Scenarios & Testing

### User Story 1 - What to do for this investor (Priority: P1)

1. **Given** a match for Produk A against Investor A, **When** the inventor opens it, **Then** "Cara meningkatkan kecocokan" lists at most five items, blocking ones first, then by estimated gain; each has a title, why, a button "Perbarui {tempat}" and an estimate badge; the rest sit under "Lihat semua (n)" (AC80).
2. **Given** a recommendation with an estimate, **Then** it reads "Perkiraan bila benar untuk produk Anda: Kecocokan potensial (54–80)"; when no estimate applies, no badge.
3. **Given** the sector or stage does not fit, **Then** the item offers "Lihat investor lain untuk produk ini" (link to 059's finder with the product selected) and no estimate.
4. **Given** an excluded match, **Then** recommendations still appear, so the inventor learns why.

### User Story 2 - Fix, come back, see the change (Priority: P1)

1. **Given** the inventor follows "Perbarui kata kunci", edits and saves, **When** they press "Kembali ke kecocokan" (the editor shows it when opened with `return=`), **Then** matching runs again and changed rows show "Topik 25 → 100" for this source and mandate (AC81).
2. **Given** a published invention, **Then** the editor reminds that changes reach investors only after publishing the new version, and the return link says "Terbitkan, lalu kembali ke kecocokan".

### User Story 3 - The three steps with the most effect (Priority: P2)

**Given** a matches page with several results, **Then** a summary at the top lists up to three recommendations with the largest total estimated gain across all recommended results, each naming the investors it helps.

### User Story 4 - Never for the investor (Priority: P1)

**Given** an investor reading a pitch or the P2 preview from 057, **Then** no recommendations are returned or shown.

## Requirements

- **FR-001**: Pure `recommend(source, target, result) -> list[Recommendation]` in `app/matching/engine/recommend.py`, using `evaluate()` for what-ifs on modified copies of `Source` (frozen dataclasses: `dataclasses.replace`).
- **FR-002**: `MatchResultResponse.recommendations` returned only on applicant runs; stored in the result JSON so a run reads back the same.
- **FR-003**: Recommendation ids are stable kinds (`requirement`, `topic`, `tkt_below`, `tkt_missing`, `stage`, `money_missing`, `money_gap`, `form`, `evidence`, `sector`, `availability`, `no_need`) with raw values; the web writes the sentences.
- **FR-004**: Deep links follow the contract in the revamp page; the editor and the need page accept `?return=` (relative path, same origin only) and show the return link.

## Success Criteria

- In the demo, Produk A against Investor A shows at least: keywords (pertanian, panen, irigasi), TKT 4 → 6, stage, sector; Produk B against Investor B shows none or only optional evidence.
- No recommendation text instructs stating something; every editing recommendation is conditional.

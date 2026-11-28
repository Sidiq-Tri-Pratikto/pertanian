# Feature Specification: Investor finder revamp (my products × an investor's mandates)

**Feature Branch**: `059-investor-finder`
**Created**: 2026-11-28
**Status**: Seeded, not started
**Milestone**: Revamp 2, demo feedback ([plan](../../docs/roadmap/revamp-2-demo-feedback.md)); Track A
**Depends on**: 057, 058
**Size**: L
**Covers**: FR10, FR11, AC82, AC83, AC84, S03, S10
**Flips**: nothing

## Context

In "Temukan Investor/Mitra" an inventor sees investors and their mandates but not how *their own products* fit a chosen investor. Matching exists only per need on a separate page. Demo feedback: "when we choose the investor, we simply match with each of our products and see the match score". This spec rebuilds the inventor's finder around that question, in two directions:

- **By investor**: pick an investor, see every one of my products scored against each of that investor's active mandates.
- **By product**: pick one of my products, see investors ranked for it.

## Page layout (inventor persona, `/discover`, result type "Investor dan Mitra")

```
┌ Temukan Investor/Mitra ─────────────────────────────────────────────┐
│ Cocokkan untuk: [ Semua produk ▾ ]   [Cari investor…]  [Filter (n)] │
├───────────────────────────┬─────────────────────────────────────────┤
│ Investor list             │ Investor A  · Investor pertanian         │
│ ● Investor B   ▮▮▮▮ Kuat  │ Mencari: Pertanian · Pilot, Berfungsi    │
│   Produk B                │ · TKT 6+ · USD 30–80rb                   │
│ ○ Investor A   ▮▯▯▯ Lemah │                                         │
│   2 produk                │ Kecocokan dengan produk Anda             │
│                           │ ┌ Produk        Mandat         Skor  ┐  │
│                           │ │ ClearSpring   Pilot pertanian 20–54 │  │
│                           │ │ SolarBox      Pilot pertanian 14–40 │  │
│                           │ └───────────────────────────────────┘  │
│                           │ ▸ ClearSpring × Pilot pertanian         │
│                           │   Rincian (057) · Cara meningkatkan (058)│
│                           │   [Siapkan pitching] / [Buat kebutuhan]  │
└───────────────────────────┴─────────────────────────────────────────┘
```

On a phone the list and the detail take turns, as Jelajahi does today (back link restores focus).

## User Scenarios & Testing

### User Story 1 - By investor (Priority: P1)

1. **Given** an inventor with published products, **When** they open an investor in the finder, **Then** the detail shows the investor's summary (thesis, sectors, stages, minimum TKT, funding range, intake) and a table "Kecocokan dengan produk Anda": one row per own published product and active mandate pair, with the label, the range bar and the top two dimensions, best first (AC82).
2. **Given** a row, **When** opened, **Then** it expands in place to the 057 breakdown and the 058 recommendations for that pair, and one action: "Siapkan pitching" when the product has an active need and the match is ready, otherwise "Buat kebutuhan untuk produk ini" or "Lengkapi {item}".
3. **Given** a product with no active need, **Then** its rows are scored in **preview** from the published product alone: Dana and Bentuk kerja sama show "Belum diketahui", the row is labelled "Pratinjau tanpa kebutuhan", and the recommendation "Buat kebutuhan dukungan" comes first. Nothing is stored (AC83).
4. **Given** the investor has no active mandate, **Then** "Investor ini belum membuka mandat. Simpan atau ikuti untuk kabar berikutnya."
5. **Given** an incompatible pair, **Then** it stays in the table but sorted last and labelled "Tidak cocok untuk target ini"; it never shows as a positive match.

### User Story 2 - By product (Priority: P1)

1. **Given** "Cocokkan untuk: ClearSpring", **When** chosen, **Then** the investor list is ordered by ClearSpring's best fit per investor (lower bound, then coverage), each row shows that best label and bar, and incompatible investors fall to the end under "Belum cocok" (AC84).
2. **Given** "Semua produk", **Then** each investor row shows its best product and how many of my products are at least "Kecocokan potensial".
3. **Given** the selection, **Then** it is kept in the address (`?produk={id}`) so Back and sharing restore it.

### User Story 3 - Fast and fair (Priority: P1)

1. **Given** 20 products and 30 investors with 3 mandates each, **When** the page loads, **Then** the fit list answers within 1.5 s locally (one evaluation per pair, pure and in memory) and the page shows a skeleton until then.
2. **Given** demo activity, **Then** ordering never uses popularity, saves or views; only fit.

## Requirements

- **FR-001**: `GET /api/v1/fit?acting_party_id=&partner_party_id=&invention_id=` returns fit for the acting party's published inventions × active mandates, filtered by either id. Each item: `{invention: {id, title, tkt_level, stage}, source: {type, id} | null (preview), opportunity: {id, title, partner_party_id, partner}, result: MatchResultResponse}`. Read-only; nothing stored; bounded at 50 inventions × 200 mandates (`VALIDATION_FAILED` past that, with a hint to filter).
- **FR-002**: Source per invention: its active support need (newest if several) else its active company raise link else a preview source from the published version (`budget=None`, `relationship=None`). Preview results carry `"preview": true`.
- **FR-003**: Authorization: the acting party's own inventions only; mandates as any applicant reads them (`active_targets`); the isolation harness gets the route.
- **FR-004**: The partners list in `GET /api/v1/discovery?type=partners` gains `best_fit` per partner only when `produk` is given (computed through the same service), so ordering happens on the server.
- **FR-005**: The existing `/matches?source=` page stays for a need's full list; the finder links to it ("Lihat semua investor untuk kebutuhan ini").

## Success Criteria

- Demo scenario 3 is shown from the finder alone: choose Investor B, see Produk B strong and Produk A weak, open Produk A, read why and what to do.

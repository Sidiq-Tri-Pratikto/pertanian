# Content, states and charts

## Domain-state grammar

These are independent dimensions. Combine them; never collapse them into one enum or one red panel.

| State | Presentation | Component |
|---|---|---|
| No data | "Belum ada data energi", import/demo next action; no 0 kWh, no empty chart | `HD.EnergyMetric` `quality: 'unavailable'` |
| Measured zero | `0,000 kWh` with complete coverage; no percentages from a zero total | `HD.EnergyMetric`, `HD.ContributionRanking` |
| Missing tariff | Energy stays; "Biaya belum dihitung — tarif belum diatur"; optional "Atur tarif" | `HD.CostEstimate` `tariff: null` |
| Learning | "Belum cukup periode pembanding"; measured totals still shown | `HD.InsightSummary` `kind: 'learning'` |
| No eligible finding | Honest no-finding text; not an efficiency or safety verdict | `HD.InsightSummary` `kind: 'none'` |
| Partial | Recorded amount qualified next to the number; gap times; data alternative | `HD.EnergyMetric` `partial`, `HD.HistoryChart` `null` points |
| Stale live source | Last measurement time + "Periksa sumber"; never "perangkat mati" | `HD.DataQuality` `freshness.state: 'stale'` |
| Historical import | Date range + "Lihat periode data"; not a failed live connection | `HD.DataQuality` `historical` |
| Client offline | Confirmed values with age; drafts retained; saves unconfirmed | `HD.DataQuality` `client: 'offline'` |
| Scope conflict | Individual values + explanation; choose a valid view before combining | `HD.ScopeSummary` `overlap` |
| Pending / unknown save | Inspectable status; no premature success; check before resending | `HD.ProgressStatus` |
| Unavailable capability | Reason + useful next action; no unqualified "Terhubung" | `disabledReason` on controls and options |

Combinations demonstrated: partial + no tariff (`CostEstimate` partial/missing and `EnergyMetric` partial), partial + stale (`DataQuality`), historical import + client offline (`DataQuality`), learning + measured totals (Household Beranda), measured zero + no percentages (`ContributionRanking`), parent/child 10/1 (Industrial).

## Copy rules

- One primary action per step; buttons start with a verb ("Simpan tarif", "Impor 8 baris", "Periksa status", "Coba lagi").
- Every disabled control says why, in a sentence the user can act on ("Isi tarif terlebih dahulu untuk menyimpan.").
- Field errors name the field and the fix; row errors name the data row, the file line and the column. Say whether a number is a data row or a file line.
- Draft and confirmed are visibly different: "Draf tersimpan di perangkat ini — belum dikirim" versus "Dikonfirmasi server 26 Oktober 2026 09.14".
- Technical detail (methods, policy versions) goes in "Detail perhitungan", never in the main reading path.

## Number and date display

| Value | Display | Source |
|---|---|---|
| 14.7 kWh | `14,700 kWh` | `HD.format.kwh` (three decimals, `id-ID`) |
| 0.05 kWh/unit | `0,050 kWh/unit` | three decimals |
| 22050 IDR | `Rp22.050` | `HD.format.rupiah` — rounds the unrounded product once |
| 8.4 / 14.7 | `57,14%` | `HD.format.percent` — `null` when the denominator is 0 |
| +1.4 kWh, +55.56% | `+1,400 kWh`, `+55,56%` | `signedKwh`, `signedPercent` (U+2212 for minus) |
| 2026-10-19 … 2026-10-25 | `19–25 Oktober 2026` | `HD.format.dateRange` |
| 07:00–17:00 | `07.00–17.00` | `HD.format.time` |

Machine exports and code keep canonical numbers (`14.7`, `1500`); only display is localised.

## Chart grammar

- **Contribution**: `HD.ContributionRanking` — sorted horizontal bars, common zero baseline, direct value + share labels, visible denominator ("Dari total 14,700 kWh perangkat terukur yang dipilih"). "Terbesar di antara perangkat terukur yang dipilih" — never "boros".
- **History**: `HD.HistoryChart` daily bars for a week; hourly with `dense` for a day. Current = solid green; reference = light fill + dashed outline + legend words; gaps = hatch + "Tidak ada data"; measured zero = baseline tick. The scale starts at 0 and keeps 20% headroom; exact values are in the table.
- **Every chart** has a text summary that resolves the same numbers and an `HD.ChartDataAlternative` with the same filter. No hover or drag is required to answer any task.
- **Never**: donuts for ranking, smoothing, interpolation, 3D, animated morphs, a percent when the reference is 0, a gap drawn as 0, an inferred full-day total.

# Pattern assemblies

Four bounded compositions validate meaning and reuse; they are not the S01–S12 application. Each is a preview page (`components/Pattern*/preview.html`) that uses only `HD.*` components and tokens. The dashed "Kontrol uji — bukan bagian UI produk" panel at the top of each page switches fixture states for reviewers and is not product UI. All data is synthetic and the screens carry "Demo · Data simulasi".

## 1. Household Beranda — `PatternHouseholdBeranda`

Mobile populated overview in the prescribed reading order: `HD.PeriodSelector` → `HD.EnergyMetric` (period, scope, 14,700 kWh) → `HD.CostEstimate` → `HD.DataQuality` → `HD.ContributionRanking` → `HD.InsightSummary` (learning), framed by `HD.Screen` with the three-tab bar. No schedule, no output metric, no AC. Test control switches the synthetic tariff (Rp22.050) and the no-tariff variant ("Biaya belum dihitung — tarif belum diatur"). Choosing "Hari ini" or another range shows "Belum ada data energi", not 0 kWh, because the demo data covers 19–25 Oktober 2026 only. From 768 px the scope list moves to the supporting column.

## 2. Evidence and incomplete data — `PatternEvidence`

Saran screen with three sections: (a) TV change, `HD.InsightSummary` + `HD.HistoryChart` (current vs reference, dashed outline) + `HD.ChartDataAlternative` + `HD.EvidencePanel` with harmless feedback whose send can fail then succeed on retry, stay unknown until checked, or succeed; (b) zero baseline: "Pompa Air naik 2,100 kWh", "Persentase tidak tersedia karena pembanding 0 kWh"; (c) partial/gap: Kulkas 12 of 24 hours, hatched gap, hourly table, `HD.DataQuality` partial + stale.

## 3. CSV preview and recovery — `PatternCsvImport`

`HD.ImportPreview` with 10 data rows. 2 invalid: confirming without the acknowledgment raises `HD.ErrorSummary`, which takes focus and links to the checkbox; after acknowledging, "Impor 8 baris" saves. 3 invalid: blocked with a notice and a disabled-with-reason confirm. Save outcomes: failure → "Coba lagi" (draft and acknowledgment retained) → success; unknown → "Periksa status" → the first import is found, with "Baris tidak diimpor dua kali"; success only after the simulated server confirmation. Buttons ignore repeated clicks while saving.

## 4. Industrial reuse — `PatternIndustrial`

Perangkat screen for Pabrik Cikarang using the same components: `HD.EnergyMetric` 144,000 kWh, `HD.CostEstimate` Rp216.000, `HD.ContributionRanking` (Oven 50%), `HD.AssetRow` list including the long name "Pompa Air Area Produksi Belakang" without data, and `HD.ScopeSummary` parent/child: Meteran Utama 10,000 kWh or Kulkas 1,000 kWh, never 11. The test control turns the optional capabilities off (the supporting column disappears and the core stays complete) or on: `HD.OutputMetricPreview` 144 ÷ 2.880 = 0,050 kWh/unit, 0 unit (no intensity), not filled; `HD.ScheduleWindows` with an overnight window.

## Fixture register

| Value | Origin |
|---|---|
| Household week 19–25 Oktober 2026: Kulkas 8.400, Router 1.680, Pompa Air 2.100, TV 2.520 = 14.700 kWh; Rp1,500/kWh = Rp22,050; virtual now 26 Oct 00.00 | Handoff §12 |
| TV 3.920 vs 2.520 kWh (+1.400, +55.56%); site 16.100 kWh, Rp24,150 | Handoff §12 (separate change scenario; current 19–25, reference 12–18 Oktober assigned here) |
| Industrial: Oven 72, Kompresor 36, Mesin Press 24, Lampu Area 12 = 144 kWh, Rp216,000; output 2,880 units = 0.050 kWh/unit | Handoff §12 |
| Main meter 10 kWh includes refrigerator 1 kWh | Handoff §12 |
| Import: 10 rows, 2 invalid accepted with acknowledgment, 3 invalid blocked | Handoff §12 |
| 24 hourly intervals, 12 valid (50%) | Handoff §12 |
| Daily TV split 0.560 / 0.360 kWh; hourly Kulkas 0.050 kWh at 00–06 and 18–24 on 25 Oct (0.600 kWh); Pompa Air reference 0 kWh; Pompa Air Cadangan 0 kWh; Panel Produksi 6 kWh; Sirkuit Dapur 10.5 kWh; Pompa Air Area Produksi Belakang 3.6 kWh / no data; import row messages; timestamps such as 09.14 and 17.58 | Derived for this design system only, labelled in each preview; not canonical fixtures |

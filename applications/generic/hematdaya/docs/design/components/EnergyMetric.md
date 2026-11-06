# EnergyMetric

Recorded kWh for a period and physical scope, with provenance and the quality qualifier next to the number.

**Anatomy.** Label "Energi yang dipantau" + provenance tag · period · scope · value + unit · qualifier · empty state.

**Consumer provides.** `kwh` (number or null), `quality` complete | partial | unavailable, `completeness`, `gapLabel`, `periodLabel`, `scopeLabel`, `provenance`, `emptyAction`.

**Variants and states.** Complete, partial ("Sebagian data belum tersedia · Kelengkapan data: 50% periode"), measured zero ("Nol terukur dengan data lengkap"), no data ("Belum ada data energi", no number).

**Keyboard and screen reader.** A labelled `<section>`; value and unit are one text run.

**Tokens.** `type-metric`, `color-text-*`, `color-status-attention-foreground`.

**Responsive.** Value and unit wrap as a group.

**Example.** 14,700 kWh · 19–25 Oktober 2026 · Cakupan pengukuran: 4 perangkat · Demo · Data simulasi.

**Limits.** Never show 0 for missing data or a zero-filled full total for partial data.

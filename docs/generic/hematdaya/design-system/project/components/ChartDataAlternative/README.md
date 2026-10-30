# ChartDataAlternative

Text summary and structured table resolving the same values and filters as the chart.

**Anatomy.** Summary · disclosure "Lihat data dalam tabel" · table with caption.

**Consumer provides.** `caption`, `columns[{key,label,numeric,format}]`, `rows`, `summary`, `collapsed`.

**Variants and states.** Collapsed, expanded, null cells ("Tidak ada data").

**Keyboard and screen reader.** Real `<table>` with row/column headers; below 768 px rows stack with labels.

**Tokens.** `color-border-*`, `color-text-secondary`.

**Responsive.** Stacked rows on phones; no page scroll.

**Example.** TV per hari table.

**Limits.** Must match the chart exactly.
